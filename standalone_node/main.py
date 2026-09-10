import pygame
import socket
import json
import time


# Configuring:
UDP_IP = "127.0.0.1"    # Localhost
UDP_PORT = 5005         # Port Fusion360 will listen to
DEADZONE = 0.1         # Ignore movements < 0.08 to prevent camera drift
TICK_RATE = 1 / 60.0    # Time between updates. Currently 60 per second


def apply_deadzone(value, deadzone = DEADZONE):
    """Zeroes out if the joystick is close to rest position."""
    return value if abs(value) > deadzone else 0.0

def main():
    # Initializing pygame + joystick:
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("ERROR [standalone_node.main] No joystick detected. Plug in the Thrustmaster joystick and rerun.")
        return

    stick = pygame.joystick.Joystick(0)     # NOTE that if more than one joystick is connected, it will use the one with index 0
    stick.init()
    print(f"INFO [standalone_node.main] Hardware found: {stick.get_name()}")

    # Setting up the UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"INFO [standalone_node.main] Broadcasting telemetry to {UDP_IP}:{UDP_PORT}...\nPress Ctrl+C to stop.")

    try:
        while True:
            pygame.event.pump()     # Pygame requires this to update the internal hardware state

            # Read the raw axes (-1.0 to 1.0)
            # Axis mapping varies by Thrustmaster model, but generally:
            # 0: X-axis (roll), 1: Y-axis (pitch), 2: Z-axis/twist (yaw)
            raw_x = stick.get_axis(0)
            raw_y = stick.get_axis(1)
            raw_z = stick.get_axis(2) if stick.get_numaxes() > 2 else 0.0

            # Packageing the unfiltered data:
            payload = json.dumps({
                "x": apply_deadzone(raw_x),
                "y": apply_deadzone(raw_y),
                "z": apply_deadzone(raw_z)
            })

            # Firing the packet and waiting for the next frame
            sock.sendto(payload.encode("utf-8"), (UDP_IP, UDP_PORT))
            time.sleep(TICK_RATE)

    except KeyboardInterrupt:
        print("CRITICAL [standalone_node.main] Ctrl+C -> Shutting down broadcaster")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()