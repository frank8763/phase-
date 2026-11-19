"""Latest observation is best effort; command acceptance stays fail closed."""
import socket


def send_latest(sock,payload,peer):
    previous=sock.gettimeout()
    sock.setblocking(False)
    try:
        sock.sendto(payload,socket.MSG_DONTWAIT,peer);return True
    except (BlockingIOError,TimeoutError,FileNotFoundError,ConnectionRefusedError):
        return False
    finally:
        sock.settimeout(previous)
