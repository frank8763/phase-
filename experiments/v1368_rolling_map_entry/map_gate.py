"""Readiness of the current rolling window against the unchanged public map."""
import math


def snapshot(message):
    pose=message.info.origin
    return dict(frame_id=message.header.frame_id,width=message.info.width,height=message.info.height,
        resolution=message.info.resolution,origin=[pose.position.x,pose.position.y],
        orientation=[pose.orientation.x,pose.orientation.y,pose.orientation.z,pose.orientation.w],data=list(message.data))


def inspect_map(actual,public):
    def fail(reason,**detail):return dict(passed=False,reason=reason,**detail)
    try:
        width,height=actual['width'],actual['height'];resolution=actual['resolution'];origin=actual['origin'];data=actual['data']
        if type(width) is not int or type(height) is not int or min(width,height)<=0 or len(data)!=width*height:return fail('MALFORMED_MAP')
        if not all(math.isfinite(v) for v in [resolution,*origin[:2]]) or resolution<=0:return fail('NONFINITE_OR_INVALID_GEOMETRY')
        if abs(resolution-public['resolution'])>1e-7:return fail('RESOLUTION_MISMATCH')
        if actual.get('frame_id','odom')!='odom':return fail('FRAME_MISMATCH')
        rotation=actual.get('orientation',[0.,0.,0.,1.])
        if len(rotation)!=4 or not all(math.isfinite(v) for v in rotation) or max(abs(v-w) for v,w in zip(rotation,[0.,0.,0.,1.]))>1e-7:return fail('ORIGIN_ORIENTATION_MISMATCH')
        if any(type(v) is not int or not -1<=v<=100 for v in data):return fail('INVALID_OCCUPANCY_VALUE')
        required=present=overlap=0
        for y in range(height):
            world_y=origin[1]+(y+.5)*resolution
            py=math.floor((world_y-public['origin'][1])/public['resolution'])
            for x in range(width):
                world_x=origin[0]+(x+.5)*resolution
                px=math.floor((world_x-public['origin'][0])/public['resolution'])
                if 0<=px<public['width'] and 0<=py<public['height']:
                    overlap+=1
                    if public['data'][py*public['width']+px]==100:
                        required+=1;present+=data[y*width+x]==100
        return dict(passed=required>0 and present==required,reason='READY' if required>0 and present==required else 'MISSING_CURRENT_WINDOW_PUBLIC_OCCUPANCY',
            current_window=[*origin[:2],origin[0]+width*resolution,origin[1]+height*resolution],
            required_public_occupied=required,present_public_occupied=present,overlap_cells=overlap,
            map_width=width,map_height=height,resolution=resolution)
    except (KeyError,IndexError,TypeError,ValueError,OverflowError):return fail('MALFORMED_MAP')
