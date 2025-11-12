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

import subprocess
import traceback
from datetime import datetime

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ScrollLabel import ScrollLabel

from . import _
from .tools import (
    get_interface_info,
    is_interface_up,
    scan_networks,
    format_signal_quality,
    get_wifi_interfaces
)


class WiFiDetailedInfo(Screen):
    skin = """
    <screen position="center,center" size="800,700" title="WiFi Detailed Info">
        <widget name="info_output" position="10,10" size="780,600" font="Regular;18" />
        <widget name="key_red" position="10,635" size="180,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="red" transparent="1" />
        <widget name="key_green" position="210,635" size="180,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="green" transparent="1" />
        <eLabel name="" position="9,677" size="180,8" zPosition="3" backgroundColor="#fe0000" />
        <eLabel name="" position="209,677" size="180,8" zPosition="3" backgroundColor="#fe00" />
    </screen>
    """

    def __init__(self, session, ifname):
        Screen.__init__(self, session)
        self.session = session
        self.ifname = ifname
        self.debug_file = '/tmp/WifiManager_detailed_info_debug.txt'
        self["info_output"] = ScrollLabel()
        self["key_red"] = Button(_("Refresh"))
        self["key_green"] = Button(_("Close"))
        self["actions"] = ActionMap(
            ["ColorActions", "OkCancelActions", "DirectionActions"],
            {
                "red": self.refresh_info,
                "green": self.close,
                "cancel": self.close,
                "pageUp": self.pageUp,
                "pageDown": self.pageDown,
                "up": self.pageUp,
                "down": self.pageDown,
                "left": self.pageUp,
                "right": self.pageDown,
            }
        )
        self.setTitle(_("Detailed Info - {}").format(ifname))
        # Write initialization to the debug file
        self._write_debug(f"🚀 WiFiDetailedInfo INITIALIZED for interface: {ifname}")
        self.refresh_info()

    def _write_debug(self, message, error=False):
        """Write debug messages to file"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_level = "❌ ERROR" if error else "📝 DEBUG"
            full_message = f"[{timestamp}] {log_level}: {message}\n"

            with open(self.debug_file, "a", encoding="utf-8") as f:
                f.write(full_message)

            # Also print to console for dual debugging
            print(full_message.strip())
        except Exception as e:
            print(f"CRITICAL: Cannot write to debug file: {e}")

    def pageUp(self):
        self["info_output"].pageUp()

    def pageDown(self):
        self["info_output"].pageDown()

    def refresh_info(self):
        self._write_debug(f"🔄 STARTING REFRESH for {self.ifname}")
        print(f"[WiFiDetailedInfo] Starting refresh for {self.ifname}")
        wifi_ifaces = get_wifi_interfaces()
        if self.ifname not in wifi_ifaces:
            error_msg = f"❌ Interface {self.ifname} not found or not a WiFi interface\n"
            error_msg += f"Available interfaces: {', '.join(wifi_ifaces) if wifi_ifaces else 'None'}"
            self._write_debug(f"Interface not found: {self.ifname}", error=True)
            self["info_output"].setText(error_msg)
            return

        try:
            info_text = f"📡 DETAILED WIFI INFORMATION - {self.ifname.upper()}\n"
            info_text += "=" * 60 + "\n\n"

            # 1. BASIC INTERFACE INFORMATION
            self._write_debug("Getting basic interface info...")
            print("[WiFiDetailedInfo] Getting basic interface info...")
            info_text += "🔧 BASIC INTERFACE INFO\n"
            info_text += "-" * 40 + "\n"
            basic_info = self.get_basic_interface_info()
            info_text += basic_info
            info_text += "\n"

            # 2. WIRELESS INFORMATION
            self._write_debug("Getting wireless info...")
            print("[WiFiDetailedInfo] Getting wireless info...")
            info_text += "📶 WIRELESS INFORMATION\n"
            info_text += "-" * 40 + "\n"
            wireless_info = self.get_wireless_info()
            info_text += wireless_info
            info_text += "\n"

            # 3. DRIVER AND HARDWARE INFO
            self._write_debug("Getting driver info...")
            print("[WiFiDetailedInfo] Getting driver info...")
            info_text += "🔌 DRIVER & HARDWARE\n"
            info_text += "-" * 40 + "\n"
            driver_info = self.get_driver_info()
            info_text += driver_info
            info_text += "\n"

            # 4. NETWORK STATISTICS
            self._write_debug("Getting network statistics...")
            print("[WiFiDetailedInfo] Getting network statistics...")
            info_text += "📊 NETWORK STATISTICS\n"
            info_text += "-" * 40 + "\n"
            stats_info = self.get_network_statistics()
            info_text += stats_info
            info_text += "\n"

            # 5. AVAILABLE NETWORKS (scan results)
            self._write_debug("Scanning for available networks...")
            print("[WiFiDetailedInfo] Scanning for available networks...")
            info_text += "🌐 AVAILABLE NETWORKS\n"
            info_text += "-" * 40 + "\n"
            networks_info = self.get_available_networks()
            info_text += networks_info

            # Also save complete information to the debug file
            self._write_debug(f"REFRESH COMPLETED SUCCESSFULLY - Interface: {self.ifname}")
            self._write_debug(f"FINAL OUTPUT LENGTH: {len(info_text)} characters")

            # Save the full output to the debug file
            try:
                with open(self.debug_file, "a", encoding="utf-8") as f:
                    f.write("\n" + "=" * 50 + " FULL OUTPUT " + "=" * 50 + "\n")
                    f.write(info_text)
                    f.write("\n" + "=" * 120 + "\n")
            except Exception as e:
                self._write_debug(f"Error saving full output to debug file: {e}", error=True)

            print("[WiFiDetailedInfo] Refresh completed successfully")
            self["info_output"].setText(info_text)

        except Exception as e:
            error_msg = f"❌ Error getting detailed info:\n{str(e)}\n\n"
            stack_trace = traceback.format_exc()
            self._write_debug(f"CRITICAL ERROR during refresh: {error_msg}", error=True)
            self._write_debug(f"STACK TRACE: {stack_trace}", error=True)
            print(f"[WiFiDetailedInfo] ERROR: {e}")
            print(f"Stack trace: {stack_trace}")
            self["info_output"].setText(error_msg)

    def get_wireless_info(self):
        """Get wireless-specific information using tools.py"""
        self._write_debug(f"Getting wireless info for {self.ifname} using tools.py")
        print(f"[WiFiDetailedInfo] Getting wireless info for {self.ifname}")
        info = ""

        try:
            interface_info = get_interface_info(self.ifname)

            if 'error' in interface_info:
                info += f"❌ Error: {interface_info['error']}\n"
                self._write_debug(f"Error getting wireless info: {interface_info['error']}", error=True)
                return info

            info += "📡 Interface Type: WIRELESS\n"
            self._write_debug("Interface is WIRELESS")

            # ESSID
            essid = interface_info.get('essid', 'Not connected')
            info += f"📡 ESSID: {essid}\n"
            self._write_debug(f"ESSID: {essid}")

            # Mode
            mode = interface_info.get('mode', 'Unknown')
            info += f"🔧 Mode: {mode}\n"
            self._write_debug(f"Mode: {mode}")

            # Frequency/Channel
            frequency = interface_info.get('frequency', 'Unknown')
            info += f"📶 Frequency: {frequency}\n"
            self._write_debug(f"Frequency: {frequency}")

            # Quality and Signal
            quality = interface_info.get('quality', 'Unknown')
            info += f"📊 Quality: {quality}\n"
            self._write_debug(f"Quality: {quality}")

            # Bit Rate
            bitrate = interface_info.get('bitrate', 'Unknown')
            info += f"🚀 Bit Rate: {bitrate}\n"
            self._write_debug(f"Bit Rate: {bitrate}")

            # TX Power
            txpower = interface_info.get('txpower', 'Unknown')
            info += f"⚡ TX Power: {txpower}\n"
            self._write_debug(f"TX Power: {txpower}")

            # Protocol/Driver
            protocol = interface_info.get('protocol', 'Unknown')
            info += f"💾 Protocol: {protocol}\n"
            self._write_debug(f"Protocol: {protocol}")

        except Exception as e:
            error_msg = f"Wireless info error: {str(e)}"
            info += f"❌ {error_msg}\n"
            self._write_debug(error_msg, error=True)
            print(f"[WiFiDetailedInfo] {error_msg}")

        self._write_debug(f"Wireless info completed, length: {len(info)}")
        return info

    def get_basic_interface_info(self):
        """Get basic interface information using tools.py"""
        self._write_debug(f"Getting basic info for {self.ifname} using tools.py")
        print(f"[WiFiDetailedInfo] Getting basic info for {self.ifname}")
        info = ""

        try:
            interface_info = get_interface_info(self.ifname)
            if 'error' in interface_info:
                info += f"❌ Error: {interface_info['error']}\n"
                self._write_debug(f"Error getting interface info: {interface_info['error']}", error=True)
                return info

            # Status
            status = "UP and active" if is_interface_up(self.ifname) else "DOWN"
            icon = "✅" if is_interface_up(self.ifname) else "🔌"
            info += f"{icon} Status: {status}\n"
            self._write_debug(f"Status: {status}")

            # Interface name
            info += f"🔧 Interface: {interface_info.get('name', self.ifname)}\n"

            # MAC Address
            if 'ap_addr' in interface_info and interface_info['ap_addr'] != "Unknown":
                info += f"📟 MAC: {interface_info['ap_addr']}\n"
                self._write_debug(f"MAC: {interface_info['ap_addr']}")

            # Type
            interface_type = "Wireless" if self.ifname in get_wifi_interfaces() else "Wired"
            icon = "📡" if interface_type == "Wireless" else "🔌"
            info += f"{icon} Type: {interface_type} interface\n"
            self._write_debug(f"Type: {interface_type}")

        except Exception as e:
            error_msg = f"Basic info error: {str(e)}"
            info += f"❌ {error_msg}\n"
            self._write_debug(error_msg, error=True)
            print(f"[WiFiDetailedInfo] {error_msg}")

        self._write_debug(f"Basic info completed, length: {len(info)}")
        return info

    def get_driver_info(self):
        """Get driver and hardware information"""
        self._write_debug("Getting driver info")
        info = ""

        try:
            driver_path = f"/sys/class/net/{self.ifname}/device/driver"
            self._write_debug(f"Checking driver path: {driver_path}")

            if subprocess.run(["test", "-d", driver_path], capture_output=True).returncode == 0:
                driver_name = subprocess.check_output(["basename", driver_path], text=True).strip()
                info += f"💾 Driver: {driver_name}\n"
                self._write_debug(f"Driver found: {driver_name}")
            else:
                info += "💾 Driver: Unknown\n"
                self._write_debug("Driver: Unknown")

            interface_info = get_interface_info(self.ifname)
            if 'protocol' in interface_info and interface_info['protocol'] != "Unknown":
                info += f"🔧 Module: {interface_info['protocol']}\n"
                self._write_debug(f"Module: {interface_info['protocol']}")

            if self.ifname in get_wifi_interfaces():
                info += "📡 Type: Wireless interface\n"
                self._write_debug("Type: Wireless interface")
            else:
                info += "🔌 Type: Wired interface\n"
                self._write_debug("Type: Wired interface")

        except Exception as e:
            error_msg = f"Driver info error: {str(e)}"
            info += f"❌ {error_msg}\n"
            self._write_debug(error_msg, error=True)

        self._write_debug(f"Driver info completed, length: {len(info)}")
        return info

    def get_network_statistics(self):
        """Get network statistics"""
        self._write_debug("Getting network statistics")
        info = ""
        try:
            # Interface statistics
            rx_path = f'/sys/class/net/{self.ifname}/statistics/rx_bytes'
            tx_path = f'/sys/class/net/{self.ifname}/statistics/tx_bytes'

            self._write_debug(f"Reading RX bytes from: {rx_path}")
            result = subprocess.run(['cat', rx_path],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                rx_bytes = int(result.stdout.strip())
                formatted_rx = self.format_bytes(rx_bytes)
                info += f"⬇️  Received: {formatted_rx}\n"
                self._write_debug(f"RX bytes: {rx_bytes} ({formatted_rx})")
            else:
                self._write_debug(f"Failed to read RX bytes: {result.stderr}")

            self._write_debug(f"Reading TX bytes from: {tx_path}")
            result = subprocess.run(['cat', tx_path],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                tx_bytes = int(result.stdout.strip())
                formatted_tx = self.format_bytes(tx_bytes)
                info += f"⬆️  Transmitted: {formatted_tx}\n"
                self._write_debug(f"TX bytes: {tx_bytes} ({formatted_tx})")
            else:
                self._write_debug(f"Failed to read TX bytes: {result.stderr}")

        except Exception as e:
            error_msg = f"Statistics error: {str(e)}"
            info += f"❌ {error_msg}\n"
            self._write_debug(error_msg, error=True)

        self._write_debug(f"Network statistics completed, length: {len(info)}")
        return info

    def get_available_networks(self):
        """Get available networks via scan using tools.py"""
        self._write_debug("Starting network scan using tools.py")
        info = ""

        try:
            self._write_debug(f"Running scan_networks for {self.ifname}")

            networks = scan_networks(self.ifname, detailed=True)

            self._write_debug(f"Scan completed, found {len(networks)} networks")

            if networks:
                info += f"Found {len(networks)} networks:\n"
                self._write_debug(f"Found {len(networks)} networks")

                for i, net in enumerate(networks[:8]):
                    essid = net.get('essid', 'Unknown')
                    signal = net.get('signal', 'N/A')
                    quality_percent = net.get('quality_percent', 0)
                    channel = net.get('channel', '?')
                    encrypted = "🔒" if net.get('encryption') else "🔓"

                    signal_quality = format_signal_quality(quality_percent)

                    info += f"  {i + 1:2d}. {encrypted} {essid:20} | "
                    info += f"Signal: {signal:4} dBm ({signal_quality}) | "
                    info += f"Channel: {channel}\n"

                if len(networks) > 8:
                    info += f"  ... and {len(networks) - 8} more networks\n"
            else:
                info += "No networks found or scan not supported\n"
                self._write_debug("No networks found in scan")

        except Exception as e:
            error_msg = f"Scan error: {str(e)}"
            info += f"{error_msg}\n"
            self._write_debug(error_msg, error=True)

        self._write_debug(f"Network scan completed, length: {len(info)}")
        return info

    def format_bytes(self, bytes):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"
