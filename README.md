# fusion360-joystick-bridge
The purpose of this project is to control Fusion360's orbiting through a USB joystick.
Other joysticks are likely to be supported, though I personally tested this only on the Thrustmaster model sold as 
"Thrustmaster USB Joystick" (the one with the small throttle handle on the side). 

This method works in two steps:
- Broadcasting the joystick's telemetry to a port in the local network
- Having a Fusion360 add-in read from that port and update the camera

So this repository is divided in two parts:
- **standalone_node:** it contains the **main.py** file that needs to run in the background for the Fusion add-in to receive the data. It also contains a tester file that you can run (while *main.py* is running, in another terminal window) to make sure that main is actually sending data through the selected port.
- **fusion_addin:** it contains the **thrustmaster_joystick_bridge.py** file. That file **shouldn't be run**, as it will throw an ImportError. You actually have to paste that code into the main Add-In python file *once* you have created your Fusion add-in.

**NOTE**: The actual code in fusion_addin is to be copied and pasted into a fusion add-in once that add-in was created from the Fusion360 interface.

## Requirements:
- **pygame**: *standalone_node.main* uses `pygame.joystick` to read the joystick inputs.
To install the dependencies for the standalone script (only pygame currently), open your terminal, navigate to the root folder, and run:
`pip install -r requirements.txt`

## Features:
This design is currently limited to orbiting and zooming around the 3d model.

## 1. How to create our Fusion360 Add-In
1. Open up **Fusion 360**
2. **Shift + "S"**, the **Scripts and Add-ins** window will open up
3. Click the "**+**" symbol in the top left corner and select "**Create script or add-in**"
4. Select "**Add-in**" (not "Script"), and pick an add-in name.

### 2. Pasting the code into the Fusion add-in
5. Once you've created your add-in, **open the add-in list** (Shift + "S" if you closed it)
6. **Right-click on the add-in **you just created. You can also **click the "Edit" button**, which should automatically open the add-in's folder in your IDE or fusion's own editor.
7. "**Open File Location**". This should launch File Explorer into a folder named after your add-in. It should contain:
    - A *config.py* file (don't touch that)
    - A file named *<your_addin_name>.manifest* (don't touch that either)
    - **A file named *<your_addin_name>.py*** <- That is the one we're working with
    - ...and some other stuff (like a "commands" and a "lib" folder and an "AddInIcon.svg" file. I suppose the exact folder structure might change in future updates)
8. Open up the file named ***<your_addin_name>.py***. It will contain some template code. You can safely delete all its code and **replace it with the one in "fusion_addin.thrustmaster_joystick_bridge.py"**.
    - NOTE: your IDE won't recognize the `adsk.core` and `adsk.fusion` modules, and **trying to run the add-in file will result in an error**. That's completely normal, as that file is intended to be run by Fusion360 itself.
9. Done.

## 3. How to use it
1. **Connect your USB joystick**
2. Run **standalone_node/main.py** (the add-in itself won't work if main.py isn't running in the background)
3. On **Fusion 360**: open the **add-in list** (Shift + "S"), and **click the "Run" switch** next to the Fusion add-in you created.
    - NOTE: I don't advise selecting the "Run on startup" checkbox. If for any reason the add-in crashes or raises an exception, Fusion itself might crash (though it's unlikely since an add-in with an exception should only try to run once)
4. Moving your joystick should now orbit/zoom your Fusion 360 view.

### 4. Fine-tuning:
Edit the global constants inside *main.py* and *thrustmaster_joystick_bridge*. To have fusion reflecting the changes you'll have to either rerun main.py or deactivate and reactivate your add-in (depending on what you changed).
Customization options include:
- Orbit and zoom multiplier (inside `standalone_node.fusion_addin`): they control the sensitivity of the camera movements. **Negative values in the multipliers will invert the direction of the movement.**
- `UDP_IP` and `UDP_PORT`: global constants inside **all files**. You should change these only if the default ip/port (`127.0.0.1:5005`) are busy. You'll have to change those inside **standalone_node/main.py**, **standalone_node/test_listener.py** and **your fusion add-in's code.**

**Note on fine-tuning in the fusion add-in:** once you created the add-in and pasted the code inside it, what's running is the code inside the add-in. To edit the multipliers you'll have to open its code (not fusion_addin/thrustmaster_joystick_bridge.py) as explained in **step 2**.
