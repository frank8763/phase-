"""GPU ideal-model proposals only. Outputs require independent native certification."""
import torch

from cases import BATCH, HORIZON


def evaluate(pose, last, goal, path, rectangles, circles, half, lower, upper, rate,
             offsets, wheels, follow, lookahead, brakes):
    xy = pose[:2].expand(BATCH, 2).clone()
    yaw = pose[2].expand(BATCH).clone()
    command = last.expand(BATCH, 4).clone()
    position_rows, command_rows = [], []
    path_arc = torch.cat((torch.zeros(1, device=pose.device, dtype=pose.dtype),
                          torch.linalg.vector_norm(path[1:, :2] - path[:-1, :2], dim=1).cumsum(0)))
    for tick in range(HORIZON):
        nearest = ((xy[:, None] - path[None, :, :2]) ** 2).sum(2).argmin(1)
        target_arc = path_arc[nearest] + lookahead
        target_index = (path_arc[None] - target_arc[:, None]).abs().argmin(1)
        relative = path[target_index, :2] - xy
        lateral = -torch.sin(yaw) * relative[:, 0] + torch.cos(yaw) * relative[:, 1]
        pursuit = torch.atan2(1.2 * lateral, (relative ** 2).sum(1).clamp_min(.02))
        steer = torch.where(follow, pursuit + offsets[:, tick], offsets[:, tick]).clamp(-.42722137342572125, .42722137342572125)
        radius = .6 / torch.tan(steer.abs()).clamp_min(1e-12)
        inner = torch.atan2(torch.full_like(radius, .6), radius - .27)
        outer = torch.atan2(torch.full_like(radius, .6), radius + .27)
        left = torch.where(steer >= 0, inner, -outer)
        right = torch.where(steer >= 0, outer, -inner)
        mean = wheels[:, tick]
        delta = 8. * mean * torch.tan(steer) * .54 / 1.2
        wheel_left = torch.where(follow, mean - delta, mean)
        wheel_right = torch.where(follow, mean + delta, mean)
        braking = tick >= brakes
        target = torch.stack((torch.where(braking, command[:, 0], left),
                              torch.where(braking, command[:, 1], right),
                              torch.where(braking, torch.zeros_like(mean), wheel_left),
                              torch.where(braking, torch.zeros_like(mean), wheel_right)), 1)
        target = torch.minimum(torch.maximum(target, lower), upper)
        command = torch.minimum(torch.maximum(target, command - rate), command + rate)
        # Ideal bicycle model: an approximate proposer, not the actual dynamics.
        speed = .12 * command[:, 2:].mean(1)
        omega = speed * torch.tan(command[:, :2].mean(1)) / .6
        heading = yaw + .04 * omega
        xy = xy + .08 * speed[:, None] * torch.stack((torch.cos(heading), torch.sin(heading)), 1)
        yaw = yaw + .08 * omega
        position_rows.append(torch.cat((xy, yaw[:, None]), 1))
        command_rows.append(command)
    poses = torch.stack(position_rows, 1)
    controls = torch.stack(command_rows, 1)
    c, s = torch.cos(poses[:, :, 2]), torch.sin(poses[:, :, 2])
    ex, ey = c.abs() * half[0] + s.abs() * half[1], s.abs() * half[0] + c.abs() * half[1]
    clearance = torch.stack((poses[:, :, 0] - ex + 5., 5. - poses[:, :, 0] - ex,
                             poses[:, :, 1] - ey + 5., 5. - poses[:, :, 1] - ey), 2).amin(2)
    dx = rectangles[None, None, :, 0] - poses[:, :, None, 0]
    dy = rectangles[None, None, :, 1] - poses[:, :, None, 1]
    rx, ry = rectangles[None, None, :, 2], rectangles[None, None, :, 3]
    separation = torch.stack((dx.abs() - rx - ex[:, :, None], dy.abs() - ry - ey[:, :, None],
                              (dx * c[:, :, None] + dy * s[:, :, None]).abs() - half[0] - rx * c[:, :, None].abs() - ry * s[:, :, None].abs(),
                              (-dx * s[:, :, None] + dy * c[:, :, None]).abs() - half[1] - rx * s[:, :, None].abs() - ry * c[:, :, None].abs()), 3).amax(3).amin(2)
    clearance = torch.minimum(clearance, separation)
    dx = circles[None, None, :, 0] - poses[:, :, None, 0]
    dy = circles[None, None, :, 1] - poses[:, :, None, 1]
    lx = (dx * c[:, :, None] + dy * s[:, :, None]).abs() - half[0]
    ly = (-dx * s[:, :, None] + dy * c[:, :, None]).abs() - half[1]
    circle_distance = torch.where(torch.maximum(lx, ly) <= 0., torch.maximum(lx, ly),
                                  torch.sqrt(lx.clamp_min(0.) ** 2 + ly.clamp_min(0.) ** 2)) - circles[None, None, :, 2]
    clearance = torch.minimum(clearance, circle_distance.amin(2))
    route_distance = ((poses[:, :, None, :2] - path[None, None, :, :2]) ** 2).sum(3)
    contour = route_distance.amin(2).sqrt().mean(1)
    start_index = ((pose[None, :2] - path[:, :2]) ** 2).sum(1).argmin()
    end_index = route_distance[:, -1].argmin(1)
    progress = path_arc[end_index] - torch.gather(path_arc, 0, start_index.reshape(1))[0]
    goal_distance = torch.linalg.vector_norm(poses[:, -1, :2] - goal, dim=1)
    penalty = (.18 - clearance).clamp_min(0.).square().mean(1)
    effort = ((controls[:, 1:] - controls[:, :-1]) ** 2).mean((1, 2))
    cost = goal_distance + 2. * contour - 2. * progress + 1000. * penalty + .02 * effort + 2. * (.12 * controls[:, -1, 2:].mean(1)) ** 2
    order = torch.argsort(cost, stable=True)
    return poses, controls, cost, order


class GPUProposer:
    KEYS = ('pose', 'last', 'goal', 'path', 'rectangles', 'circles', 'half', 'lower', 'upper', 'rate')
    PARAMS = ('offsets', 'wheels', 'follow', 'lookahead', 'brakes')

    def __init__(self, case, parameters):
        self.inputs = [torch.as_tensor(case[key], device='cuda') for key in self.KEYS]
        self.parameters = [torch.as_tensor(parameters[key], device='cuda') for key in self.PARAMS]
        stream = torch.cuda.Stream()
        stream.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(stream):
            for _ in range(3):
                evaluate(*self.inputs, *self.parameters)
        torch.cuda.current_stream().wait_stream(stream)
        self.graph = torch.cuda.CUDAGraph()
        with torch.cuda.graph(self.graph):
            self.outputs = evaluate(*self.inputs, *self.parameters)
        torch.cuda.synchronize()

    def execute(self, case):
        for device, key in zip(self.inputs, self.KEYS):
            device.copy_(torch.as_tensor(case[key]))
        self.graph.replay()
        # Return a small finite proposal set; no GPU proposal authorizes execution.
        index = self.outputs[3][:4]
        return index.cpu().numpy(), self.outputs[1][index].cpu().numpy(), self.outputs[2][index].cpu().numpy()

    def full_outputs(self):
        return [value.cpu().numpy() for value in self.outputs]
