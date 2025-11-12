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
from re import search
from enigma import eTimer

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ScrollLabel import ScrollLabel

from wifi.scan import Cell

from . import _
from .tools import (
    get_wifi_interfaces,
    is_interface_up,
    ensure_interface_up,
    parse_iwlist_detailed,
    format_signal_quality,
    get_interface_info
)


IW_ENCODE_DISABLED = 0x8000  # Encoding disabled
IW_ENCODE_ENABLED = 0x0000  # Encoding enabled


class WiFiScanner(Screen):
    skin = """
    <screen position="center,center" size="800,700" title="WiFi Scanner">
        <widget name="scan_output" position="10,10" size="782,608" font="Regular;18" />
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
        self.scan_timer = eTimer()
        self.scan_timer.callback.append(self.perform_scan)

        self["scan_output"] = ScrollLabel()
        self["key_red"] = Button(_("Scan"))
        self["key_green"] = Button(_("Refresh"))
        self["key_yellow"] = Button(_("Details"))
        self["key_blue"] = Button(_("Exit"))

        self["actions"] = ActionMap(
            ["ColorActions", "OkCancelActions", "DirectionActions"],
            {
                "red": self.start_scan,
                "green": self.refresh_scan,
                "yellow": self.toggle_details,
                "blue": self.close,
                "cancel": self.close,
                "pageUp": self.pageUp,
                "pageDown": self.pageDown,
                "up": self.pageUp,
                "down": self.pageDown,
                "left": self.pageUp,
                "right": self.pageDown,
                "ok": self.refresh_scan,
            }
        )

        self.detailed_view = False
        self.last_scan_results = []
        self.setTitle(_("WiFi Scanner"))
        self.start_scan()

    def pageUp(self):
        self["scan_output"].pageUp()

    def pageDown(self):
        self["scan_output"].pageDown()

    def start_scan(self):
        self["scan_output"].setText(_("Scanning for WiFi networks..."))
        self.scan_timer.start(1000, True)

    def refresh_scan(self):
        if self.last_scan_results:
            self.display_networks(self.last_scan_results)
        else:
            self.start_scan()

    def perform_scan(self):
        try:
            networks = []
            print("[WiFiScanner] Starting scan process...")

            wifi_ifaces = get_wifi_interfaces()
            if not wifi_ifaces:
                networks.append("No WiFi interfaces found\n")
                networks.extend(self.get_detailed_network_status())
                self.last_scan_results = networks
                self.display_networks(networks)
                return

            # TRY WITH WIFI.SCAN MODULE (more reliable)
            try:
                # First activate interface if needed - use wifi_ifaces
                for iface in wifi_ifaces:
                    try:
                        print(f"[WiFiScanner] Testing interface: {iface}")

                        # Check if interface exists and is up
                        if not is_interface_up(iface):
                            print(f"[WiFiScanner] Activating interface {iface}")
                            # Bring interface up using tools function
                            ensure_interface_up(iface)

                        networks.append(f"\n=== SCAN with wifi.scan on {iface} ===\n")
                        print(f"[WiFiScanner] Starting Cell.all() on {iface}...")

                        # Use Cell.all() for scanning
                        scan_results = list(Cell.all(iface, timeout=10))
                        print(f"[WiFiScanner] Cell.all() returned {len(scan_results)} results")

                        if scan_results:
                            for i, cell in enumerate(scan_results):
                                essid = cell.ssid if cell.ssid else "Hidden"

                                # DEBUG: Print all cell attributes
                                print(f"[WiFiScanner] Cell {i}: {essid}")
                                print(f"[WiFiScanner]   Cell quality: {cell.quality}")
                                if hasattr(cell, 'signal'):
                                    print(f"[WiFiScanner]   Cell signal: {cell.signal}")

                                # Parse quality string
                                quality = 0
                                if isinstance(cell.quality, str) and '/' in cell.quality:
                                    parts = cell.quality.split('/')
                                    if len(parts) == 2:
                                        try:
                                            current = int(parts[0])
                                            max_val = int(parts[1])
                                            if max_val > 0:
                                                quality = int((current / max_val) * 100)
                                                print(f"[WiFiScanner]   Parsed quality: {current}/{max_val} = {quality}%")
                                            else:
                                                quality = 0
                                                print("[WiFiScanner]   Max quality is 0, setting quality to 0")
                                        except (ValueError, ZeroDivisionError) as e:
                                            quality = 0
                                            print(f"[WiFiScanner]   Error parsing quality: {e}")

                                # Parse signal
                                signal = self.extract_signal_from_cell(cell, debug=True)

                                # # Parse signal - try multiple methods
                                # signal = 0

                                # # Method 1: Try cell.signal attribute
                                # if hasattr(cell, 'signal') and cell.signal:
                                    # if isinstance(cell.signal, str):
                                        # # Parse signal string like "-61 dBm" or "signal=-61"
                                        # signal_match = search(r'(-?\d+)\s*dBm?', cell.signal)
                                        # if signal_match:
                                            # signal = int(signal_match.group(1))
                                            # print(f"[WiFiScanner]   Signal from cell.signal: {signal} dBm")
                                    # else:
                                        # signal = cell.signal
                                        # print(f"[WiFiScanner]   Signal from cell.signal (direct): {signal} dBm")

                                # # Method 2: If signal is still 0, try to get from cell string representation
                                # if signal == 0:
                                    # cell_str = str(cell)
                                    # signal_match = search(r'Signal level=(-?\d+)', cell_str)
                                    # if signal_match:
                                        # signal = int(signal_match.group(1))
                                        # print(f"[WiFiScanner]   Signal from cell string: {signal} dBm")

                                # # Method 3: Fallback - estimate from quality (only if quality is valid)
                                # if signal == 0 and quality > 0:
                                    # # Rough estimation: -30dBm (excellent) to -90dBm (poor)
                                    # signal = -90 + (quality * 0.6)
                                    # signal = int(signal)
                                    # print(f"[WiFiScanner]   Signal estimated from quality: {signal} dBm")

                                channel = getattr(cell, 'channel', 0)
                                encrypted = "Yes" if cell.encrypted else "No"
                                frequency = getattr(cell, 'frequency', 0)
                                print(f"[WiFiScanner] Final values\nQuality: {quality}%,\nSignal: {signal}dBm,\nChannel: {channel}\nFrequency: {frequency}")

                                # Use format_signal_quality for a better description
                                signal_quality = format_signal_quality(quality)

                                networks.append(
                                    f"{i + 1:2d}. {essid:20} | "
                                    f"Quality: {quality:3}% ({signal_quality}) | "
                                    f"Signal: {signal:4} dBm | "
                                    f"Channel: {channel:2} | "
                                    f"Encrypted: {encrypted}\n"
                                )
                            break  # Stop at first working interface
                        else:
                            networks.append(f"   No networks found on {iface}\n")
                            print(f"[WiFiScanner] No networks found on {iface}")

                    except Exception as e:
                        error_msg = f"   Error on {iface}: {str(e)}\n"
                        networks.append(error_msg)
                        print(f"[WiFiScanner] {error_msg}")
                        continue

            except ImportError as e:
                error_msg = "wifi.scan library not available\n"
                networks.append(error_msg)
                print(f"[WiFiScanner] {error_msg} {e}")
                networks.extend(self.fallback_iwlist_scan())

            # If no scan worked, show diagnostic info
            if len(networks) <= 3:  # Only headers and few results
                print("[WiFiScanner] Scan failed, showing diagnostics")
                networks.extend(self.get_detailed_network_status())

            self.last_scan_results = networks
            self.display_networks(networks)

        except Exception as e:
            error_msg = f"Scan error: {str(e)}"
            print(f"[WiFiScanner] {error_msg}")
            self["scan_output"].setText(_("Scan error: ") + str(e))

    def extract_signal_from_cell(self, cell, debug=False):
        """Extract signal strength from cell object with multiple methods"""
        signal = 0
        
        # Method 1: Try cell.signal attribute directly
        if hasattr(cell, 'signal') and cell.signal is not None:
            if isinstance(cell.signal, (int, float)):
                signal = int(cell.signal)
                if debug:
                    print(f"[SIGNAL] From cell.signal (direct): {signal} dBm")
                return signal
            elif isinstance(cell.signal, str):
                # Parse signal string like "-61 dBm" or "signal=-61"
                signal_match = search(r'(-?\d+)\s*dBm?', cell.signal)
                if signal_match:
                    signal = int(signal_match.group(1))
                    if debug:
                        print(f"[SIGNAL] From cell.signal string: {signal} dBm")
                    return signal

        # Method 2: Try cell.get('signal')
        try:
            if hasattr(cell, 'get') and callable(cell.get):
                cell_signal = cell.get('signal')
                if cell_signal:
                    if isinstance(cell_signal, (int, float)):
                        signal = int(cell_signal)
                        if debug:
                            print(f"[SIGNAL] From cell.get('signal'): {signal} dBm")
                        return signal
        except:
            pass

        # Method 3: Parse from cell string representation
        cell_str = str(cell)
        if debug:
            print(f"[SIGNAL] Cell string: {cell_str}")
        
        # Try multiple signal patterns
        signal_patterns = [
            r'Signal level=(-?\d+)',
            r'signal[=:](-?\d+)',
            r'dBm[=:](-?\d+)',
            r'signal[=\s]*(-?\d+)\s*dBm',
            r'level[=\s]*(-?\d+)\s*dBm'
        ]
        
        for pattern in signal_patterns:
            signal_match = search(pattern, cell_str, search.IGNORECASE)
            if signal_match:
                try:
                    signal = int(signal_match.group(1))
                    if debug:
                        print(f"[SIGNAL] From cell string pattern '{pattern}': {signal} dBm")
                    return signal
                except ValueError:
                    continue

        # Method 4: Estimate from quality if available
        if hasattr(cell, 'quality') and cell.quality:
            if isinstance(cell.quality, str) and '/' in cell.quality:
                parts = cell.quality.split('/')
                if len(parts) == 2:
                    try:
                        current = int(parts[0])
                        max_val = int(parts[1])
                        if max_val > 0:
                            quality_percent = (current / max_val) * 100
                            # Rough estimation: -30dBm (excellent) to -90dBm (poor)
                            signal = int(-90 + (quality_percent * 0.6))
                            if debug:
                                print(f"[SIGNAL] Estimated from quality {quality_percent}%: {signal} dBm")
                            return signal
                    except (ValueError, ZeroDivisionError):
                        pass

        if debug:
            print("[SIGNAL] No signal found, using 0 dBm")
        return signal

    def fallback_iwlist_scan(self):
        """Fallback scan with iwlist using tools.py"""
        print("[WiFiScanner] Starting fallback iwlist scan")
        networks = []
        networks.append("\n=== FALLBACK SCAN with iwlist ===\n")

        try:
            wifi_ifaces = get_wifi_interfaces()

            for iface in wifi_ifaces:
                try:
                    print(f"[WiFiScanner] iwlist scan on {iface}")
                    result = subprocess.check_output(['iwlist', iface, 'scan'],
                                                     stderr=subprocess.STDOUT,
                                                     text=True,
                                                     timeout=15)
                    print(f"[WiFiScanner] iwlist output length: {len(result)}")

                    # DEBUG: Show sample of iwlist output for signal parsing
                    lines = result.split('\n')
                    signal_lines = [line for line in lines if 'Signal level' in line or 'Quality' in line]
                    for i, line in enumerate(signal_lines[:3]):
                        print(f"[SIGNAL] iwlist signal line {i}: {line.strip()}")

                    # Use parse_iwlist_detailed da tools.py
                    parsed_networks = parse_iwlist_detailed(result)
                    if parsed_networks:
                        for i, net in enumerate(parsed_networks):
                            essid = net.get('essid', 'Unknown')
                            signal = net.get('signal', 0)
                            quality_percent = net.get('quality_percent', 0)
                            channel = net.get('channel', '?')
                            encrypted = "Yes" if net.get('encryption') else "No"

                            # Use format_signal_quality
                            signal_quality = format_signal_quality(quality_percent)

                            networks.append(
                                f"{i + 1:2d}. {essid:20} | "
                                f"Quality: {quality_percent:3}% ({signal_quality}) | "
                                f"Signal: {signal:4} dBm | "
                                f"Channel: {channel} | "
                                f"Encrypted: {encrypted}\n"
                            )
                        print(f"[WiFiScanner] iwlist found {len(parsed_networks)} networks")
                        break
                    else:
                        print("[WiFiScanner] No networks parsed from iwlist output")
                except Exception as e:
                    print(f"[WiFiScanner] iwlist error on {iface}: {e}")
                    continue

            if len(networks) <= 2:  # Only header
                networks.append("   No results with iwlist\n")
                print("[WiFiScanner] iwlist found no networks")

        except Exception as e:
            error_msg = f"   iwlist error: {e}\n"
            networks.append(error_msg)
            print(f"[WiFiScanner] {error_msg}")

        return networks

    def parse_iwlist_output(self, output):
        """Parse iwlist output with debug"""
        print("[WiFiScanner] Parsing iwlist output...")
        networks = []
        if "Cell" not in output:
            print("[WiFiScanner] No 'Cell' found in iwlist output")
            return ["iwlist: No networks found or interface busy\n"]

        lines = output.split('\n')
        current_net = {}
        cell_count = 0

        for line in lines:
            line = line.strip()
            print(f"[WiFiScanner] iwlist line: {line}")

            # New cell
            if 'Cell' in line and 'Address' in line:
                cell_count += 1
                if current_net:
                    formatted = self.format_network(current_net)
                    networks.append(formatted)
                    print(f"[WiFiScanner] Added network: {formatted.strip()}")
                current_net = {'bssid': line.split('Address: ')[1]}
                print(f"[WiFiScanner] New cell #{cell_count}")

            # ESSID
            elif 'ESSID:' in line:
                essid = line.split('ESSID:"')[1].rstrip('"') if 'ESSID:"' in line else 'Hidden'
                current_net['essid'] = essid
                print(f"[WiFiScanner] Found ESSID: {essid}")

            # Quality
            elif 'Quality=' in line:
                match = search(r'Quality=(\d+)/(\d+)', line)
                if match:
                    try:
                        current_qual = int(match.group(1))
                        max_qual = int(match.group(2))
                        # FIX: Check for zero division
                        if max_qual > 0:
                            quality = (current_qual / max_qual) * 100
                            current_net['quality'] = int(quality)
                            print(f"[WiFiScanner] Quality: {current_qual}/{max_qual} = {quality}%")
                        else:
                            current_net['quality'] = 0
                            print(f"[WiFiScanner] Quality: {current_qual}/{max_qual} = 0% (max is 0)")
                    except (ValueError, ZeroDivisionError) as e:
                        current_net['quality'] = 0
                        print(f"[WiFiScanner] Error parsing quality: {e}")

                # Also try to get signal level
                signal_match = search(r'Signal level=(-?\d+)', line)
                if signal_match:
                    current_net['signal'] = int(signal_match.group(1))
                    print(f"[WiFiScanner] Signal: {signal_match.group(1)} dBm")
                else:
                    # Try alternative signal patterns
                    alt_signal_match = search(r'signal[=:](-?\d+)', line, search.IGNORECASE)
                    if alt_signal_match:
                        current_net['signal'] = int(alt_signal_match.group(1))
                        print(f"[WiFiScanner] Signal (alt): {alt_signal_match.group(1)} dBm")
            # Signal level (separate line)
            elif 'Signal level=' in line and 'quality' not in line.lower():
                match = search(r'Signal level=(-?\d+)', line)
                if match:
                    current_net['signal'] = int(match.group(1))
                    print(f"[WiFiScanner] Signal level: {match.group(1)} dBm")

        if current_net:
            formatted = self.format_network(current_net)
            networks.append(formatted)
            print(f"[WiFiScanner] Final network: {formatted.strip()}")

        print(f"[WiFiScanner] Total networks parsed: {len(networks)}")
        return networks if networks else ["iwlist: No networks found\n"]

    def process_pythonwifi_scan(self, scan_results):
        """Process pythonwifi results"""
        networks = []
        if not scan_results:
            return ["pythonwifi: No networks found\n"]

        for i, network in enumerate(scan_results):
            essid = network.essid or "Hidden"
            quality = network.quality.quality if network.quality else 0
            signal = network.quality.siglevel if network.quality else 0

            networks.append(f"{i + 1}. {essid:20} | Quality: {quality:3}% | Signal: {signal:4} dBm\n")

        return networks

    def format_network(self, net):
        """Format a network for display"""
        essid = net.get('essid', 'Unknown')
        quality = net.get('quality', 0)
        signal = net.get('signal', 0)
        bssid = net.get('bssid', '')[:8]
        return f"{essid:20} | Quality: {quality:3}% | Signal: {signal:4} dBm | {bssid}...\n"

    def format_network_info(self, net):
        """Format network info for display"""
        essid = net.get('essid', 'Unknown')
        bssid = net.get('bssid', 'Unknown')
        quality = net.get('quality', 0)
        signal = net.get('signal', 0)

        return f"{essid:20} | Quality: {quality:3}% | Signal: {signal:4} dBm | {bssid}\n"

    def get_basic_network_info(self, network, index):
        essid = network.essid or "Hidden"
        quality = network.quality.quality if network.quality else 0
        signal = network.quality.siglevel if network.quality else 0

        return f"{index:2d}. {essid:20} | Quality: {quality:3}% | Signal: {signal:4} dBm\n"

    def get_detailed_network_status(self):
        """Detailed diagnostics using tools.py functions"""
        info = []
        info.append("\n" + "=" * 50)
        info.append("\nDETAILED DIAGNOSTICS")
        info.append("\n" + "=" * 50 + "\n")

        try:
            # 1. AVAILABLE WIFI INTERFACES - use get_wifi_interfaces
            info.append("\n📡 WIFI INTERFACES:\n")
            wifi_ifaces = get_wifi_interfaces()
            if wifi_ifaces:
                info.append(f"   Found: {', '.join(wifi_ifaces)}\n")
            else:
                info.append("   No WiFi interfaces found\n")

            # 2. INTERFACE STATUS - use is_interface_up
            info.append("\n🔧 INTERFACE STATUS:\n")
            for iface in wifi_ifaces:
                status = "ACTIVE" if is_interface_up(iface) else "INACTIVE"
                icon = "V" if is_interface_up(iface) else "X"
                info.append(f"   {icon} {iface}: {status}\n")

            # 3. ACTIVE CONNECTIONS - use get_interface_info
            info.append("\nACTIVE CONNECTIONS:\n")
            for iface in wifi_ifaces:
                interface_info = get_interface_info(iface)
                if 'essid' in interface_info and interface_info['essid'] != "Not connected":
                    essid = interface_info['essid']
                    quality = interface_info.get('quality', '?')
                    info.append(f"   {iface}: Connected to {essid} ({quality})\n")
                else:
                    info.append(f"   {iface}: Not connected\n")

            # 4. SOLUTIONS
            info.append("\nPOSSIBLE SOLUTIONS:\n")
            info.append("   1. Disconnect from current WiFi network\n")
            info.append("   2. Restart WiFi adapter\n")
            info.append("   3. Check if WiFi driver is installed\n")
            info.append("   4. Try with different USB WiFi adapter\n")
            info.append("   5. Check root permissions\n")

        except Exception as e:
            info.append(f"Diagnostic error: {e}\n")

        return info

    def display_networks(self, networks):
        if isinstance(networks, list):
            self["scan_output"].setText("".join(networks))
        else:
            self["scan_output"].setText(networks)

    def toggle_details(self):
        self.detailed_view = not self.detailed_view
        if self.detailed_view:
            self["scan_output"].setText(_("Detailed view enabled - rescan to see details"))
        else:
            self["scan_output"].setText(_("Basic view enabled - rescan to see basic info"))
