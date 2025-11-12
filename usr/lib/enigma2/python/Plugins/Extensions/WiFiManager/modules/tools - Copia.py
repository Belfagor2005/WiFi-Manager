# -*- coding: utf-8 -*-

"""
#########################################################
#                                                       #
#  WiFi Manager Plugin                                  #
#  Version: 1.0                                         #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: Gnu Gpl v2                                  #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#  Last Modified: "00:00 - 20250101"                    #
#                                                       #
#  Credits:                                             #
#  - Original concept by Lululla                        #
#  Usage of this code without proper attribution        #
#  is strictly prohibited.                              #
#  For modifications and redistribution,                #
#  please maintain this credit header.                  #
#########################################################
"""

import time
import subprocess
from json import load, dump
from re import search, findall, DOTALL
from os.path import exists

from .. import _


def get_wifi_interfaces():
    """Returns all available WiFi interfaces using multiple detection methods"""
    wifi_interfaces = []

    try:
        # METHOD 1: Check /proc/net/wireless (most reliable)
        try:
            with open('/proc/net/wireless', 'r') as f:
                lines = f.readlines()
            for line in lines[2:]:  # Skip header lines
                parts = line.split(':')
                if len(parts) > 0:
                    ifname = parts[0].strip()
                    if ifname and ifname not in wifi_interfaces:
                        wifi_interfaces.append(ifname)
        except Exception as e:
            print(f"[get_wifi_interfaces] Error reading /proc/net/wireless: {e}")

        # METHOD 2: Check iwconfig output
        try:
            result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'IEEE 802.11' in line or 'ESSID:' in line:
                        if 'no wireless extensions' not in line:
                            ifname_match = search(r'^(\w+)\s+', line)
                            if ifname_match:
                                ifname = ifname_match.group(1)
                                if ifname and ifname not in wifi_interfaces:
                                    wifi_interfaces.append(ifname)
        except Exception as e:
            print(f"[get_wifi_interfaces] Error with iwconfig: {e}")

        # METHOD 3: Check ip link show with iw verification
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if any(name in line for name in ['wlan', 'wlp', 'wifi', 'ath', 'ra']):
                        ifname_match = search(r'^\d+:\s+(\w+):', line)
                        if ifname_match:
                            ifname = ifname_match.group(1)
                            if ifname and ifname not in wifi_interfaces:
                                # Verify it's actually a WiFi interface
                                try:
                                    iw_result = subprocess.run(['iw', 'dev', ifname, 'info'],
                                                               capture_output=True, text=True, timeout=5)
                                    if iw_result.returncode == 0:
                                        wifi_interfaces.append(ifname)
                                except:
                                    pass
        except Exception as e:
            print(f"[get_wifi_interfaces] Error with ip link: {e}")

        # METHOD 4: Check common interface names with verification
        common_names = ['wlan0', 'wlan1', 'wlan2', 'wlp2s0', 'wlp3s0', 'wifi0', 'ath0', 'ra0']
        for ifname in common_names:
            try:
                result = subprocess.run(['ip', 'link', 'show', ifname],
                                        capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Verify it's a WiFi interface
                    iw_result = subprocess.run(['iw', 'dev', ifname, 'info'],
                                               capture_output=True, text=True, timeout=5)
                    if iw_result.returncode == 0 and ifname not in wifi_interfaces:
                        wifi_interfaces.append(ifname)
            except:
                pass

        # METHOD 5: Check sysfs for wireless devices
        try:
            import os
            if os.path.exists('/sys/class/net'):
                for ifname in os.listdir('/sys/class/net'):
                    wireless_path = f'/sys/class/net/{ifname}/wireless'
                    if os.path.exists(wireless_path) and ifname not in wifi_interfaces:
                        wifi_interfaces.append(ifname)
        except Exception as e:
            print(f"[get_wifi_interfaces] Error checking sysfs: {e}")

    except Exception as e:
        print(f"[get_wifi_interfaces] General error: {e}")

    return wifi_interfaces


def get_interface_info(ifname):
    """Returns detailed information about an interface using system commands"""
    try:
        info = {'name': ifname}

        # Get basic interface info using iwconfig
        result = subprocess.run(['iwconfig', ifname], capture_output=True, text=True)
        if result.returncode != 0:
            info['error'] = f"Interface {ifname} not available"
            return info

        output = result.stdout

        # Extract ESSID
        essid_match = search(r'ESSID:"([^"]*)"', output)
        info['essid'] = essid_match.group(1) if essid_match else "Not connected"

        # Extract AP MAC address
        ap_match = search(r'Access Point: ([0-9A-Fa-f:]{17})', output)
        info['ap_addr'] = ap_match.group(1) if ap_match else "Unknown"

        # Extract Mode
        mode_match = search(r'Mode:(\w+)', output)
        info['mode'] = mode_match.group(1) if mode_match else "Unknown"

        # Extract Frequency/Channel
        freq_match = search(r'Frequency:([0-9.]+) GHz', output)
        channel_match = search(r'Channel[=:](\d+)', output)
        if freq_match:
            info['frequency'] = f"{freq_match.group(1)} GHz"
        elif channel_match:
            info['frequency'] = f"Channel {channel_match.group(1)}"
        else:
            info['frequency'] = "Unknown"

        # Extract Bitrate
        rate_match = search(r'Bit Rate[=:]([0-9.]+) Mb/s', output)
        info['bitrate'] = f"{rate_match.group(1)} Mb/s" if rate_match else "Unknown"

        # Extract Signal Quality
        quality_match = search(r'Link Quality=(\d+)/(\d+)', output)
        signal_match = search(r'Signal level=(-?\d+) dBm', output)

        if quality_match:
            quality = int(quality_match.group(1))
            max_quality = int(quality_match.group(2))
            percentage = (quality / max_quality) * 100 if max_quality > 0 else 0
            info['quality'] = f"{percentage:.1f}%"
        elif signal_match:
            signal_dbm = int(signal_match.group(1))
            info['quality'] = f"{signal_dbm} dBm"
        else:
            info['quality'] = "Unknown"

        # Extract TX Power
        power_match = search(r'Tx-Power[=:](\d+) dBm', output)
        info['txpower'] = f"{power_match.group(1)} dBm" if power_match else "Unknown"

        # Get protocol/driver info using ethtool
        try:
            ethtool_result = subprocess.run(['ethtool', '-i', ifname],
                                            capture_output=True, text=True)
            if ethtool_result.returncode == 0:
                driver_match = search(r'driver:\s*(\w+)', ethtool_result.stdout)
                info['protocol'] = driver_match.group(1) if driver_match else "Unknown"
            else:
                info['protocol'] = "Unknown"
        except:
            info['protocol'] = "Unknown"

        return info

    except Exception as e:
        return {'name': ifname, 'error': str(e)}


def verify_connection(interface, essid):
    """Verify connection to network"""
    try:
        result = subprocess.run(f"iwconfig {interface}", shell=True, capture_output=True, text=True)
        if f'ESSID:"{essid}"' in result.stdout:
            ip_result = subprocess.run(f"ip addr show {interface}", shell=True, capture_output=True, text=True)
            return 'inet ' in ip_result.stdout
        return False
    except:
        return False


def scan_networks(ifname, detailed=False):
    """Scan available networks using iwlist - VERSIONE SICURA"""
    try:
        cmd = f"iwlist {ifname} scan"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            raise Exception(f"Scan failed: {result.stderr.strip()}")

        networks = parse_iwlist_scan(result.stdout)
        return networks

    except subprocess.TimeoutExpired:
        raise Exception(f"Scan timeout on {ifname}")
    except Exception as e:
        raise Exception(f"Scan failed on {ifname}: {str(e)}")


def parse_iwlist_scan(scan_output):
    """Parse iwlist scan output into network list"""
    networks = []
    current_network = {}

    for line in scan_output.split('\n'):
        line = line.strip()

        # New cell block
        if 'Cell' in line and 'Address' in line:
            if current_network:
                networks.append(current_network)
            current_network = {}
            mac_match = search(r'Address: ([0-9A-Fa-f:]{17})', line)
            if mac_match:
                current_network['bssid'] = mac_match.group(1)

        # ESSID
        elif 'ESSID:' in line:
            essid_match = search(r'ESSID:"([^"]*)"', line)
            if essid_match:
                current_network['essid'] = essid_match.group(1)

        # Signal Quality
        elif 'Quality=' in line:
            quality_match = search(r'Quality=(\d+)/(\d+)', line)
            signal_match = search(r'Signal level=(-?\d+) dBm', line)

            if quality_match:
                quality = int(quality_match.group(1))
                max_quality = int(quality_match.group(2))
                percentage = (quality / max_quality) * 100 if max_quality > 0 else 0
                current_network['quality'] = percentage
            if signal_match:
                current_network['signal'] = int(signal_match.group(1))

        # Channel/Frequency
        elif 'Channel:' in line or 'Frequency:' in line:
            channel_match = search(r'Channel:(\d+)', line)
            freq_match = search(r'Frequency:([0-9.]+) GHz', line)

            if channel_match:
                current_network['channel'] = int(channel_match.group(1))
            if freq_match:
                current_network['frequency'] = float(freq_match.group(1))

        # Encryption
        elif 'Encryption key:' in line:
            encrypt_match = search(r'Encryption key:(\w+)', line)
            if encrypt_match:
                current_network['encryption'] = encrypt_match.group(1) == 'on'

        # Mode
        elif 'Mode:' in line:
            mode_match = search(r'Mode:(\w+)', line)
            if mode_match:
                current_network['mode'] = mode_match.group(1)

    # Add the last network
    if current_network:
        networks.append(current_network)

    return networks


def format_signal_quality(quality_data):
    """Format the signal quality into readable text"""
    if not quality_data:
        return "No data"

    # Handle both percentage and dBm
    if isinstance(quality_data, (int, float)):
        quality = quality_data
    elif isinstance(quality_data, dict) and hasattr(quality_data, 'quality'):
        quality = quality_data.quality
    else:
        return "Unknown"

    levels = [
        (90, _("Excellent")),
        (70, _("Good")),
        (50, _("Fair")),
        (30, _("Poor")),
        (0, _("Very Poor"))
    ]

    for threshold, description in levels:
        if quality >= threshold:
            return f"{description} ({quality}%)"

    return f"{_('Very Poor')} ({quality}%)"


def load_saved_networks(config_file=None, interface=None):
    """Load saved networks from file"""
    try:
        # If config_file is not specified, use the default one
        if config_file is None:
            config_file = "/etc/wifi_saved_networks.json"

        if exists(config_file):
            with open(config_file, 'r') as f:
                networks = load(f)
                if networks:
                    return networks

        # Fallback to wpa_supplicant if interface is provided
        if interface:
            wpa_file = f"/etc/wpa_supplicant.{interface}.conf"
            if exists(wpa_file):
                networks = parse_wpa_supplicant(wpa_file, interface)
                if networks:
                    with open(config_file, 'w') as f:
                        dump(networks, f, indent=2)
                    return networks
    except Exception as e:
        print(f"Error loading saved networks: {e}")
    return {}


def parse_wpa_supplicant(wpa_file, interface):
    """Parse wpa_supplicant config file"""
    networks = {}
    try:
        with open(wpa_file, 'r') as f:
            content = f.read()

        network_blocks = findall(r'network=\{([^}]+)\}', content, DOTALL)

        for block in network_blocks:
            ssid_match = search(r'ssid="([^"]+)"', block)
            psk_match = search(r'psk="([^"]+)"', block)

            if ssid_match and psk_match:
                essid = ssid_match.group(1)
                password = psk_match.group(1)
                networks[essid] = {
                    'password': password,
                    'encryption': 'WPA/WPA2',
                    'timestamp': time.time(),
                    'interface': interface
                }
    except Exception as e:
        print(f"Error parsing wpa_supplicant: {e}")

    return networks


def scan_networks_simple(ifname):
    """Simple network scan using iw dev scan"""
    try:
        result = subprocess.run(['iw', 'dev', ifname, 'scan'],
                                capture_output=True, text=True, timeout=20)

        if result.returncode != 0:
            raise Exception(f"iw scan failed: {result.stderr.strip()}")

        return parse_iw_scan(result.stdout)

    except subprocess.TimeoutExpired:
        raise Exception(f"Scan timeout on {ifname}")
    except Exception as e:
        raise Exception(f"Scan failed on {ifname}: {str(e)}")


def get_current_connected_essid(interface):
    """Get currently connected ESSID"""
    try:
        result = subprocess.run(f"iwconfig {interface}", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            essid_match = search(r'ESSID:"([^"]*)"', result.stdout)
            if essid_match and essid_match.group(1):
                return essid_match.group(1)
    except:
        pass
    return None


def get_ip_address(interface):
    """Get assigned IP address"""
    try:
        result = subprocess.run(f"ip addr show {interface}", shell=True, capture_output=True, text=True)
        ip_match = search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
        return ip_match.group(1) if ip_match else None
    except:
        return None


def test_ping(host="8.8.8.8", count=3, timeout=5, debug=False):
    """
    Test ping latency with optional debug output.
    Returns the average ping in ms or an error string.
    """
    try:
        # Execute the ping command
        ping_result = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), host],
            capture_output=True,
            text=True,
            timeout=timeout + 2
        )

        if debug:
            print(f"[PING DEBUG] Return code: {ping_result.returncode}")
            print(f"[PING DEBUG] Output: {ping_result.stdout}")
            print(f"[PING DEBUG] Error: {ping_result.stderr}")

        if ping_result.returncode == 0:
            # Main pattern for Linux ping output
            pattern = r'min/avg/max/[^=]*=\s*[\d.]+/([\d.]+)/[\d.]+/[\d.]+'
            match = search(pattern, ping_result.stdout)

            if match:
                avg_ping = float(match.group(1))
                return f"{avg_ping:.1f} ms"
            else:
                return "No ping data"
        else:
            return "Failed"

    except subprocess.TimeoutExpired:
        return "Timeout"
    except Exception as e:
        return f"Error: {str(e)}"


def is_interface_up(interface):
    """Check if interface is up"""
    try:
        result = subprocess.run(['ip', 'link', 'show', interface], capture_output=True, text=True)
        return 'state UP' in result.stdout
    except:
        return False


def ensure_interface_up(interface):
    """Ensure WiFi interface is up - with better error handling"""
    if not interface:
        return False

    try:
        # Check if interface exists
        result = subprocess.run(f"ip link show {interface}",
                                shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[DEBUG] Interface {interface} not found")
            return False

        # Try to bring interface up
        result = subprocess.run(f"ip link set {interface} up",
                                shell=True, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print(f"[DEBUG] Interface {interface} brought up successfully")
            time.sleep(1)  # Wait for interface to initialize
            return True
        else:
            print(f"[DEBUG] Failed to bring interface up: {result.stderr}")
            # Try alternative command
            result2 = subprocess.run(f"ifconfig {interface} up",
                                     shell=True, capture_output=True, text=True, timeout=10)
            return result2.returncode == 0

    except Exception as e:
        print(f"[DEBUG] Error ensuring interface up: {e}")
        return False


def parse_iw_scan(scan_output):
    """Parse iw scan output"""
    networks = []
    current_bss = {}

    for line in scan_output.split('\n'):
        line = line.strip()

        if line.startswith('BSS'):
            if current_bss:
                networks.append(current_bss)
            current_bss = {}
            bss_match = search(r'BSS ([0-9a-f:]{17})', line)
            if bss_match:
                current_bss['bssid'] = bss_match.group(1).lower()

        elif 'SSID:' in line:
            ssid_match = search(r'SSID: (.+)', line)
            if ssid_match:
                current_bss['essid'] = ssid_match.group(1).strip()

        elif 'signal:' in line:
            signal_match = search(r'signal: (-?\d+\.\d+) dBm', line)
            if signal_match:
                current_bss['signal'] = float(signal_match.group(1))

        elif 'freq:' in line:
            freq_match = search(r'freq: (\d+)', line)
            if freq_match:
                current_bss['frequency'] = int(freq_match.group(1))

    if current_bss:
        networks.append(current_bss)

    return networks


def parse_iwlist_detailed(scan_output):
    """More detailed parser for iwlist scan output"""
    networks = []
    current_net = {}

    for line in scan_output.split('\n'):
        line = line.strip()

        # New cell
        if 'Cell' in line and 'Address' in line:
            if current_net and current_net.get('essid'):
                networks.append(current_net)
            current_net = {'encryption': False}

            # Extract MAC address
            mac_match = search(r'Address: ([0-9A-Fa-f:]{17})', line)
            if mac_match:
                current_net['bssid'] = mac_match.group(1)

        # ESSID
        elif 'ESSID:' in line:
            essid_match = search(r'ESSID:\s*"([^"]*)"', line)
            if essid_match:
                current_net['essid'] = essid_match.group(1).strip()

        # Encryption with type detection
        elif 'Encryption key:' in line:
            current_net['encryption'] = 'on' in line.lower()

        # Signal level
        elif 'Signal level=' in line:
            signal_match = search(r'Signal level=\s*(-?\d+)', line)
            if signal_match:
                current_net['signal'] = int(signal_match.group(1))

        # Quality
        elif 'Quality=' in line:
            quality_match = search(r'Quality=(\d+)/(\d+)', line)
            if quality_match:
                quality = int(quality_match.group(1))
                max_quality = int(quality_match.group(2))
                percentage = (quality / max_quality) * 100 if max_quality > 0 else 0
                current_net['quality_percent'] = percentage

        # Channel/Frequency
        elif 'Channel:' in line:
            channel_match = search(r'Channel:(\d+)', line)
            if channel_match:
                current_net['channel'] = int(channel_match.group(1))

        # Mode
        elif 'Mode:' in line:
            mode_match = search(r'Mode:(\w+)', line)
            if mode_match:
                current_net['mode'] = mode_match.group(1)

    # Add last network
    if current_net and current_net.get('essid'):
        networks.append(current_net)

    return networks
