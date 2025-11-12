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
from enigma import eTimer
from re import sub, search, IGNORECASE

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ProgressBar import ProgressBar

from . import _
from .tools import (
    get_wifi_interfaces,
    get_interface_info,
    # is_interface_up,
    format_signal_quality
)


class WiFiMonitor(Screen):
    skin = """
    <screen position="center,center" size="800,700" title="WiFi Monitor">
        <widget name="interface_label" position="10,35" size="780,40" font="Regular;20" />
        <widget name="essid_label" position="10,100" size="780,40" font="Regular;20" />
        <widget name="ip_label" position="10,165" size="780,40" font="Regular;20" />
        <widget name="mac_label" position="10,230" size="780,40" font="Regular;20" />
        <widget name="quality_label" position="10,325" size="580,30" font="Regular;20" />
        <widget name="signal_label" position="10,457" size="580,30" font="Regular;20" />
        <widget name="quality_bar" position="10,372" size="580,60" />
        <widget name="signal_bar" position="10,503" size="580,60" />
        <widget name="key_red" position="10,635" size="180,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="red" transparent="1" />
        <widget name="key_green" position="210,635" size="180,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="green" transparent="1" />
        <widget name="key_yellow" position="410,635" size="180,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="yellow" transparent="1" />
        <widget name="key_blue" position="600,635" size="180,40" zPosition="1" font="Regular;20" halign="center" valign="center" backgroundColor="blue" transparent="1" />
        <eLabel name="" position="9,677" size="180,8" zPosition="3" backgroundColor="#fe0000" />
        <eLabel name="" position="209,677" size="180,8" zPosition="3" backgroundColor="#fe00" />
        <eLabel name="" position="409,677" size="180,8" zPosition="3" backgroundColor="#cccc40" />
        <eLabel name="" position="599,677" size="180,8" zPosition="3" backgroundColor="#1a27408b" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self["interface_label"] = Label()
        self["essid_label"] = Label()
        self["ip_label"] = Label()
        self["mac_label"] = Label()
        self["quality_label"] = Label()
        self["signal_label"] = Label()
        self["quality_bar"] = ProgressBar()
        self["signal_bar"] = ProgressBar()
        self["signal_label"].setText("Signal: N/A")
        for name in ["quality_bar", "signal_bar"]:
            self[name].setRange((0, 100))
            self[name].setValue(0)
        self["key_red"] = Label(_("Start"))
        self["key_green"] = Label(_("Stop"))
        self["key_yellow"] = Label(_("Refresh"))
        self["key_blue"] = Label(_("Exit"))
        self["actions"] = ActionMap(
            ["ColorActions", "OkCancelActions"],
            {
                "red": self.start_monitoring,
                "green": self.stop_monitoring,
                "yellow": self.update_status,
                "blue": self.close,
                "cancel": self.close,
            }
        )
        self.monitoring = False
        self.monitor_timer = eTimer()
        self.monitor_timer.callback.append(self.update_status)
        self.setTitle(_("WiFi Signal Monitor"))
        self.start_monitoring()

    def start_monitoring(self):
        """Start monitoring with interface check"""
        interfaces = get_wifi_interfaces()
        if not interfaces:
            self.show_error("No WiFi interfaces found")
            return

        self.monitoring = True
        self.monitor_timer.start(2000)
        self["key_red"].setText(_("Pause"))

    def stop_monitoring(self):
        self.monitoring = False
        self.monitor_timer.stop()
        self["key_red"].setText(_("Start"))

    def update_quality_bar(self, quality):
        """Update quality bar with color change using show/hide"""
        try:
            quality = int(quality)
            quality = max(0, min(100, quality))

            # Set value on the quality bar
            self["quality_bar"].hide()
            self["quality_bar"].setValue(quality)
            self["quality_bar"].show()

            # Update label
            self["quality_label"].setText(f"Quality: {quality}%")

        except Exception as e:
            print(f"[WiFiMonitor] Error in update_quality_bar: {e}")

    def update_signal_bar(self, signal):
        """Update signal bar with color change using show/hide"""
        try:
            if isinstance(signal, str):
                m = search(r'(-?\d+)', signal)
                signal = int(m.group(1)) if m else -90

            # Convert dBm to percentage
            if signal >= -30:
                signal_percent = 100
            elif signal <= -90:
                signal_percent = 0
            else:
                signal_percent = int(((signal + 90) * 100) / 60)

            # Set value on the signal bar
            self["signal_bar"].hide()
            self["signal_bar"].setValue(signal_percent)
            self["signal_bar"].show()

            # Update label
            self["signal_label"].setText(f"Signal: {signal} dBm")

        except Exception as e:
            print(f"[WiFiMonitor] Error in update_signal_bar: {e}")

        except Exception as e:
            print(f"[WiFiMonitor] Error in update_signal_bar: {e}")

    def update_status(self):
        if not self.monitoring:
            return

        try:
            wifi_data = self.get_wifi_info_iwconfig()
            if wifi_data:
                print(f"[WiFiMonitor] Data: {wifi_data}")
                self["interface_label"].setText(f"Interface: {wifi_data.get('interface', 'N/A')}")
                self["essid_label"].setText(f"ESSID: {wifi_data.get('essid', 'Not connected')}")
                self["ip_label"].setText(f"IP: {wifi_data.get('ip', 'N/A')}")
                self["mac_label"].setText(f"MAC: {wifi_data.get('mac', 'N/A')}")

                quality = wifi_data.get('quality', 0)
                signal = wifi_data.get('signal', 0)
                print(f"[WiFiMonitor] Quality: {quality}%, Signal: {signal} dBm")

                # Use format_signal_quality for a better description
                signal_description = format_signal_quality(quality)

                self["quality_label"].setText(f"Quality: {quality}% ({signal_description})")
                self["signal_label"].setText(f"Signal: {signal} dBm")

                self["quality_bar"].setValue(quality)

                # Convert dBm to percentage: -30dBm (excellent) to -90dBm (poor)
                # Also handle positive signals (rare)
                if signal > 0:
                    signal_percent = 100  # Maximum for positive signal values
                else:
                    signal_percent = max(0, min(100, (signal + 90) * 100 / 60))

                self["signal_bar"].setValue(int(signal_percent))

            else:
                self.show_error("No WiFi connection data available")

        except Exception as e:
            print(f"[WiFiMonitor] Update error: {e}")
            self.show_error(f"Monitoring error: {str(e)}")

    def get_wifi_info_iwconfig(self):
        """Get WiFi info using tools.py (more reliable)"""
        try:
            # Find WiFi interfaces using tools.py
            interfaces = get_wifi_interfaces()
            if not interfaces:
                return None

            # Use the first available interface
            ifname = interfaces[0]
            wifi_data = {'interface': ifname}

            # Get information using get_interface_info from tools.py
            interface_info = get_interface_info(ifname)
            print(f"[WiFiMonitor] Interface info: {interface_info}")  # DEBUG

            if 'error' in interface_info:
                print(f"[WiFiMonitor] Error getting interface info: {interface_info['error']}")
                return None

            # ESSID
            wifi_data['essid'] = interface_info.get('essid', 'Not connected')

            # Quality
            quality_str = interface_info.get('quality', '0')
            print(f"[WiFiMonitor] Raw quality string: '{quality_str}'")  # DEBUG

            try:
                if isinstance(quality_str, str):
                    # Common cases: "70/70", "50%", "35", "-45 dBm"
                    if '/' in quality_str:
                        # Format "current/max"
                        parts = quality_str.split('/')
                        if len(parts) == 2:
                            current = float(parts[0])
                            max_val = float(parts[1])
                            quality = int((current / max_val) * 100) if max_val > 0 else 0
                        else:
                            quality = 0
                    elif '%' in quality_str:
                        # Remove the % and convert
                        quality = int(float(quality_str.replace('%', '')))
                    else:
                        # Try to convert directly
                        quality_clean = sub(r'[^\d.-]', '', quality_str)
                        quality = int(float(quality_clean)) if quality_clean else 0
                else:
                    quality = int(quality_str)

                wifi_data['quality'] = min(max(quality, 0), 100)  # Clamp between 0 and 100
                print(f"[WiFiMonitor] Parsed quality: {wifi_data['quality']}%")  # DEBUG

            except (ValueError, TypeError) as e:
                print(f"[WiFiMonitor] Quality parsing error: {e}")
                wifi_data['quality'] = 0

            # Signal level
            try:
                # Run iwconfig to get detailed signal info
                result = subprocess.run(['iwconfig', ifname],
                                        capture_output=True, text=True, timeout=5)
                output = result.stdout
                print(f"[WiFiMonitor] iwconfig output: {output}")  # DEBUG

                # Search for signal level in dBm
                signal_match = search(r'Signal level=(-?\d+) dBm', output)
                if signal_match:
                    wifi_data['signal'] = int(signal_match.group(1))
                    print(f"[WiFiMonitor] Found signal level: {wifi_data['signal']} dBm")  # DEBUG
                else:
                    # Try alternative format
                    signal_match2 = search(r'Signal level=(-?\d+)', output)
                    if signal_match2:
                        wifi_data['signal'] = int(signal_match2.group(1))
                        print(f"[WiFiMonitor] Found signal level (alt format): {wifi_data['signal']}")  # DEBUG
                    else:
                        # Fallback: use quality-based estimation
                        quality_percent = wifi_data['quality']
                        # Better conversion: 100% = -20dBm, 0% = -100dBm
                        wifi_data['signal'] = int(-100 + (quality_percent * 0.8))
                        print(f"[WiFiMonitor] Estimated signal: {wifi_data['signal']} dBm")  # DEBUG

            except Exception as e:
                print(f"[WiFiMonitor] Error getting signal: {e}")
                wifi_data['signal'] = -90  # Default value for "no signal"

            # IP and MAC
            try:
                from Components.Network import iNetwork
                ip = iNetwork.getAdapterAttribute(ifname, "ip")
                mac = iNetwork.getAdapterAttribute(ifname, "mac")

                if ip and ip != [0, 0, 0, 0]:
                    wifi_data['ip'] = '.'.join(map(str, ip))
                else:
                    wifi_data['ip'] = 'Not connected'

                wifi_data['mac'] = mac if mac else 'N/A'

            except:
                # Fallback: try getting IP via subprocess
                try:
                    result = subprocess.run(['ip', 'addr', 'show', ifname],
                                            capture_output=True, text=True)
                    ip_match = search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
                    wifi_data['ip'] = ip_match.group(1) if ip_match else 'Not connected'

                    # Get MAC address
                    mac_match = search(r'link/ether ([0-9a-f:]+)', result.stdout, IGNORECASE)
                    wifi_data['mac'] = mac_match.group(1) if mac_match else 'N/A'
                except:
                    wifi_data['ip'] = 'N/A'
                    wifi_data['mac'] = 'N/A'

            print(f"[WiFiMonitor] Final data: {wifi_data}")  # DEBUG
            return wifi_data

        except Exception as e:
            print(f"[WiFiMonitor] Error: {e}")
            return None

    def show_error(self, message):
        """Show error status with contextual information"""
        interfaces = get_wifi_interfaces()

        self["interface_label"].setText(f"Interface: {interfaces[0] if interfaces else 'N/A'}")
        self["essid_label"].setText(message)
        self["ip_label"].setText("IP: N/A")
        self["mac_label"].setText("MAC: N/A")
        self["quality_label"].setText("Quality: N/A")
        self["signal_label"].setText("Signal: N/A")
        # Reset bars
        self["quality_bar"].setValue(0)
        self["signal_bar"].setValue(0)
        self["quality_bar"].hide()
        self["signal_bar"].hide()
