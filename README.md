# Automate The Capture Of Handshakes

# !!! DISCLAIMER !!!

This script is for educational purposes only, as this attack is illegal to perform without consent from the owner of the network you are trying to attack. Use it at your own risk. Only test networks that you have permission to test.

## Requirements
[monitormode](https://www.github.com/osiris-314/monitormode)

## The program deauthenticates all clients in a wifi network, and setup a listener for handshakes. when the clients try to reconnect to the wifi , the handshake gets captured and the attack stops.
```
python capturehandshake.py <interface_name>
```
![pre_capture](https://github.com/user-attachments/assets/bd2927ca-0721-4072-a9cb-b924a3f8f83a)
![capture](https://github.com/user-attachments/assets/b8678991-463a-4800-8b6a-332089ec8e2a)

# The Handshake Is Captured In The .cap File, for later decryption.
![dir_after_capture](https://github.com/user-attachments/assets/df6dfddc-2fe1-4638-ad42-4e3771ae5779)
