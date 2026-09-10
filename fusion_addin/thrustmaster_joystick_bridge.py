"""
This file isn't intended to be run directly. It only contains the
code to be manually pasted inside the Fusion add-in's main python file.

That is, once you actually created your add-in from the Fusion360 UI
(see main README.md in the root folder for a short guide on creating an add-in).
"""


import adsk.core, adsk.fusion, traceback
import threading, socket, json

app = None
ui = None
handlers = []
stopFlag = False
myCustomEvent = "JoystickTelemetryEvent"
customEvent = None

UDP_IP = "127.0.0.1"    # These have to correspond to the IP and port assigned in standalone_node.main
UDP_PORT = 5005

# Sensitivity multipliers (tweak if movement is too fast/slow)
ORBIT_SPEED = 0.075
ZOOM_SPEED = 0.15

latest_payload = None
is_rendering = False

# Background thread:
class UdpListener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))
        self.sock.settimeout(1.0)

    def run(self):
        global stopFlag, app, latest_payload, is_rendering

        while not stopFlag:
            try:
                data, addr = self.sock.recvfrom(1024)
                latest_payload = data.decode("utf-8")

                if app and not is_rendering:
                    is_rendering = True
                    app.fireCustomEvent(myCustomEvent, "")
            except socket.timeout:
                pass
            except Exception as e:
                pass

# Main thread event handler
class TelemetryHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        global latest_payload, is_rendering
        try:
            if not latest_payload:
                return

            payload = json.loads(latest_payload)

            x = payload["x"]
            y = payload["y"]
            z = payload["z"]

            # Skipping processing if the joystick is centered
            if x == 0.0 and y == 0.0 and z == 0.0:
                return

            # Grabbing the current camera state:
            viewport = app.activeViewport
            camera = viewport.camera
            target = camera.target
            eye = camera.eye
            up = camera.upVector

            # Determining world up (Fusion can be configured as Y-up or Z-up)
            world_up = adsk.core.Vector3D.create(0, 1, 0)

            if abs(up.z) > abs(up.y) and abs(up.z) > abs(up.x):
                world_up = adsk.core.Vector3D.create(0, 0, 1.0 if up.z > 0 else -1.0)
            elif abs(up.y) > abs(up.x):
                world_up = adsk.core.Vector3D.create(0, 1.0 if up.y > 0 else -1.0, 0)
            else:
                world_up = adsk.core.Vector3D.create(1.0 if up.x > 0 else -1.0, 0, 0)

            # Orbit left/right
            if x != 0.0:
                yaw_mat = adsk.core.Matrix3D.create()
                yaw_mat.setToRotation(x * ORBIT_SPEED, world_up, target)
                eye.transformBy(yaw_mat)

            # Orbit up/down
            # Finding the camera's local "right" axis using a cross product:
            eye_vec = target.vectorTo(eye)
            right_vec = up.crossProduct(eye_vec)

            if y != 0.0 and right_vec.length > 0.001:
                right_vec.normalize()
                pitch_mat = adsk.core.Matrix3D.create()
                pitch_mat.setToRotation(y * ORBIT_SPEED, right_vec, target)

                # Preventing gimbal lock: testing if the new pitch goes over the pole
                test_eye = eye.copy()
                test_eye.transformBy(pitch_mat)
                test_eye_vec = target.vectorTo(test_eye)
                test_eye_vec.normalize()

                # Applying pitch if we aren't looking perfectly straight down/up
                if abs(test_eye_vec.dotProduct(world_up)) < 0.99:
                    eye = test_eye
                    eye_vec = target.vectorTo(eye)

            # Reconstructing a stable camera up vector so it doesn't twist
            right_vec = world_up.crossProduct(eye_vec)
            if right_vec.length > 0.001:
                right_vec.normalize()
                stable_up = eye_vec.crossProduct(right_vec)
                stable_up.normalize()
                camera.upVector = stable_up
            

            # Zoom
            if z != 0.0:
                new_extents = camera.viewExtents * (1.0 + (z * ZOOM_SPEED))

                if new_extents > 0.1:
                    camera.viewExtents = new_extents

            # Applying the new vectors and pushing to the viewport
            camera.eye = eye
            camera.isSmoothTransition = False
            viewport.camera = camera

            # Forcing fusion to immediately paint the new frame
            viewport.refresh()

        except:
            pass    # Silently passing errors so we don't spam the UI 60 times per second
        finally:
            is_rendering = False

# Add-in setup
def run(context):
    global app, ui, customEvent, stopFlag
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        stopFlag = False

        customEvent = app.registerCustomEvent(myCustomEvent)
        onTelemetry = TelemetryHandler()
        customEvent.add(onTelemetry)
        handlers.append(onTelemetry)

        listener = UdpListener()
        listener.start()

        app.log(f"Joystick bridge started. Listening on port {UDP_PORT}.")

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

# Add-in shutdown
def stop(context):
    global stopFlag, app, customEvent
    try:
        stopFlag = True
        app.unregisterCustomEvent(myCustomEvent)
        app.log("Joystick bridge stopped.")
    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))