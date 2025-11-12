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
from re import search, IGNORECASE, findall

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.ScrollLabel import ScrollLabel

from .tools import get_wifi_interfaces
from . import _


class WiFiDiagnostics(Screen):
    skin = """
    <screen position="center,center" size="800,700" title="WiFi Diagnostics">
        <widget name="diagnostics_output" position="10,10" size="773,579" font="Regular;18" />
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
        self["diagnostics_output"] = ScrollLabel()
        self["key_red"] = Button(_("Full Test"))
        self["key_green"] = Button(_("Quick Test"))
        self["key_yellow"] = Button(_("Clear"))
        self["key_blue"] = Button(_("Exit"))
        self["actions"] = ActionMap(
            ["ColorActions", "OkCancelActions", "DirectionActions"],
            {
                "red": lambda: self.run_diagnostics(full_test=True),
                "green": lambda: self.run_diagnostics(full_test=False),
                "yellow": self.clear_output,
                "blue": self.close,
                "cancel": self.close,
                "pageUp": self.pageUp,
                "pageDown": self.pageDown,
                "up": self.pageUp,
                "down": self.pageDown,
                "left": self.pageUp,
                "right": self.pageDown,
            }
        )
        self.setTitle(_("WiFi Diagnostics"))
        self.interfaces = get_wifi_interfaces()
        self.run_diagnostics(full_test=False)

    def pageUp(self):
        self["diagnostics_output"].pageUp()

    def pageDown(self):
        self["diagnostics_output"].pageDown()

    def run_diagnostics(self, full_test=True):
        diagnostics = ["=== WiFi Diagnostics (System Commands Only) ===\n"]
        diagnostics.append(f"Test Type: {'Full Comprehensive Test' if full_test else 'Quick System Check'}\n\n")

        # LOG INIZIALE
        print("[WiFiDiagnostics] Starting diagnostics...")

        try:
            # 1. SYSTEM LEVEL CHECKS
            diagnostics.append("🔧 SYSTEM LEVEL DIAGNOSTICS\n")
            diagnostics.append("=" * 50 + "\n")

            # Kernel modules
            print("[WiFiDiagnostics] Checking kernel modules...")
            kernel_modules = self.check_kernel_modules()
            diagnostics.extend(kernel_modules)
            for line in kernel_modules:
                print(f"[WiFiDiagnostics] {line.strip()}")

            # USB devices
            print("[WiFiDiagnostics] Checking USB devices...")
            usb_wifi = self.check_usb_wifi_devices()
            diagnostics.extend(usb_wifi)
            for line in usb_wifi:
                print(f"[WiFiDiagnostics] {line.strip()}")

            # System commands availability
            print("[WiFiDiagnostics] Checking system commands...")
            commands_check = self.check_system_commands()
            diagnostics.extend(commands_check)
            for line in commands_check:
                print(f"[WiFiDiagnostics] {line.strip()}")

            # 2. NETWORK INTERFACE CHECKS
            diagnostics.append("\n📡 NETWORK INTERFACE DIAGNOSTICS\n")
            diagnostics.append("=" * 50 + "\n")

            # Get WiFi interfaces using system commands
            print("[WiFiDiagnostics] Scanning for WiFi interfaces...")
            wifi_interfaces = get_wifi_interfaces()
            all_interfaces = self.get_all_interfaces()

            diagnostics.append(f"All Network Interfaces: {', '.join(all_interfaces) if all_interfaces else 'None found'}\n")
            diagnostics.append(f"Wireless Interfaces: {', '.join(wifi_interfaces) if wifi_interfaces else 'None found'}\n\n")

            print(f"[WiFiDiagnostics] Found interfaces: {wifi_interfaces}")

            if not wifi_interfaces:
                diagnostics.append("❌ CRITICAL: No WiFi interfaces detected!\n")
                solutions = self.suggest_solutions(no_interfaces=True)
                diagnostics.extend(solutions)
                for line in solutions:
                    print(f"[WiFiDiagnostics] {line.strip()}")
                self.display_results(diagnostics)
                return

            # 3. PER-INTERFACE DETAILED TESTS
            for ifname in wifi_interfaces:
                print(f"[WiFiDiagnostics] Testing interface: {ifname}")
                diagnostics.append(f"\n🔍 DETAILED ANALYSIS: {ifname}\n")
                diagnostics.append("-" * 40 + "\n")

                # Interface status
                print("[WiFiDiagnostics] Checking interface status...")
                iface_status = self.check_interface_status(ifname)
                diagnostics.extend(iface_status)
                for line in iface_status:
                    print(f"[WiFiDiagnostics] {line.strip()}")

                # Driver info
                print("[WiFiDiagnostics] Checking driver info...")
                driver_info = self.check_driver_info(ifname)
                diagnostics.extend(driver_info)
                for line in driver_info:
                    print(f"[WiFiDiagnostics] {line.strip()}")

                # Basic wireless tests
                print("[WiFiDiagnostics] Running basic wireless tests...")
                basic_tests = self.run_basic_wireless_tests(ifname)
                diagnostics.extend(basic_tests)
                for line in basic_tests:
                    print(f"[WiFiDiagnostics] {line.strip()}")

                # Full comprehensive tests (only if requested)
                if full_test:
                    print("[WiFiDiagnostics] Running advanced tests...")
                    advanced_tests = self.run_advanced_tests(ifname)
                    diagnostics.extend(advanced_tests)
                    for line in advanced_tests:
                        print(f"[WiFiDiagnostics] {line.strip()}")

                # Performance tests
                print("[WiFiDiagnostics] Running performance tests...")
                perf_tests = self.run_performance_tests(ifname)
                diagnostics.extend(perf_tests)
                for line in perf_tests:
                    print(f"[WiFiDiagnostics] {line.strip()}")

            # 4. SUMMARY AND RECOMMENDATIONS
            diagnostics.append("\n💡 SUMMARY & RECOMMENDATIONS\n")
            diagnostics.append("=" * 50 + "\n")
            summary = self.generate_summary(wifi_interfaces)
            diagnostics.extend(summary)
            for line in summary:
                print(f"[WiFiDiagnostics] {line.strip()}")

            print("[WiFiDiagnostics] Diagnostics completed successfully")

        except Exception as e:
            error_msg = f"\n❌ DIAGNOSTIC ERROR: {str(e)}\n"
            diagnostics.append(error_msg)
            print(f"[WiFiDiagnostics] ERROR: {e}")

        self.display_results(diagnostics)

    def get_all_interfaces(self):
        """Get all network interfaces"""
        interfaces = []
        try:
            result = subprocess.run(['ip', 'link', 'show'],
                                    capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if ': ' in line and 'LOOPBACK' not in line:
                    parts = line.split(': ')
                    if len(parts) > 1:
                        ifname = parts[1].strip()
                        if ifname and ifname not in interfaces:
                            interfaces.append(ifname)
        except:
            pass
        return interfaces

    def check_kernel_modules(self):
        """Check loaded WiFi kernel modules"""
        results = []
        try:
            output = subprocess.check_output(["lsmod"], text=True)
            wifi_modules = []
            for module in ["rtl", "ath", "brcm", "wl", "iwl", "mt", "rt", "zd"]:
                if module in output.lower():
                    matches = findall(rf"({module}\w*)\s+\d", output)
                    wifi_modules.extend(matches)

            if wifi_modules:
                results.append(f"✅ Loaded WiFi modules: {', '.join(set(wifi_modules))}\n")
            else:
                results.append("⚠️  No WiFi kernel modules detected\n")
        except Exception as e:
            results.append(f"❌ Kernel module check failed: {e}\n")
        return results

    def check_usb_wifi_devices(self):
        """Check for USB WiFi devices"""
        results = []
        try:
            output = subprocess.check_output(["lsusb"], text=True)
            wifi_adapters = []
            for vendor in ["Realtek", "Ralink", "Atheros", "Broadcom", "Intel", "MediaTek"]:
                if vendor.lower() in output.lower():
                    matches = findall(rf".*{vendor}.*", output, IGNORECASE)
                    wifi_adapters.extend(matches)

            if wifi_adapters:
                results.append("✅ USB WiFi adapters detected:\n")
                for adapter in set(wifi_adapters):
                    results.append(f"   - {adapter.strip()}\n")
            else:
                results.append("ℹ️  No USB WiFi adapters found\n")
        except Exception as e:
            results.append(f"❌ USB device check failed: {e}\n")
        return results

    def check_system_commands(self):
        """Check availability of essential commands"""
        results = []
        essential_cmds = ["iwconfig", "iw", "ip", "ifconfig", "wpa_supplicant"]
        available_cmds = []
        missing_cmds = []
        for cmd in essential_cmds:
            try:
                subprocess.run([cmd, "--help"], capture_output=True, timeout=2)
                available_cmds.append(cmd)
            except:
                missing_cmds.append(cmd)

        if available_cmds:
            results.append(f"✅ Available commands: {', '.join(available_cmds)}\n")
        if missing_cmds:
            results.append(f"⚠️  Missing commands: {', '.join(missing_cmds)}\n")

        return results

    def check_interface_status(self, ifname):
        """Check interface status using ip command"""
        results = []
        try:
            # Check if interface exists and status
            output = subprocess.check_output(["ip", "link", "show", ifname], text=True)
            if "state UP" in output:
                results.append(f"✅ Interface {ifname}: UP and active\n")
            elif "state DOWN" in output:
                results.append(f"⚠️  Interface {ifname}: DOWN (needs activation)\n")
            else:
                results.append(f"❌ Interface {ifname}: UNKNOWN STATE\n")

            # Get MAC address
            mac_match = search(r"link/ether (([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))", output)
            if mac_match:
                results.append(f"   MAC Address: {mac_match.group(1)}\n")

        except subprocess.CalledProcessError:
            results.append(f"❌ Interface {ifname}: NOT FOUND\n")
        except Exception as e:
            results.append(f"❌ Interface check failed: {e}\n")

        return results

    def check_driver_info(self, ifname):
        """Get driver information for interface"""
        results = []
        try:
            driver_path = f"/sys/class/net/{ifname}/device/driver"
            if subprocess.run(["test", "-d", driver_path], capture_output=True).returncode == 0:
                driver_name = subprocess.check_output(["basename", driver_path], text=True).strip()
                results.append(f"   Driver: {driver_name}\n")
            else:
                results.append("   Driver: Unknown\n")
        except Exception as e:
            results.append(f"   Driver check failed: {e}\n")
        return results

    def run_basic_wireless_tests(self, ifname):
        """Run basic wireless functionality tests using system commands only"""
        print(f"[WiFiDiagnostics] Running basic tests for {ifname}")
        results = []

        # Test ESSID con iwconfig
        try:
            print(f"[WiFiDiagnostics] Running iwconfig for {ifname}...")
            output = subprocess.check_output(["iwconfig", ifname], text=True, timeout=5)
            print(f"[WiFiDiagnostics] iwconfig output: {output[:200]}...")  # Prime 200 caratteri

            essid_match = search(r'ESSID:"([^"]*)"', output)
            if essid_match:
                results.append(f"📶 ESSID: {essid_match.group(1)}\n")
                print(f"[WiFiDiagnostics] ESSID found: {essid_match.group(1)}")
            else:
                results.append("📶 ESSID: Not connected\n")
                print("[WiFiDiagnostics] No ESSID found")
        except Exception as e:
            error_msg = f"❌ ESSID check: {e}\n"
            results.append(error_msg)
            print(f"[WiFiDiagnostics] {error_msg}")

        # Test signal quality con iwconfig
        try:
            output = subprocess.check_output(["iwconfig", ifname], text=True, timeout=5)
            quality_match = search(r'Link Quality=(\d+)/(\d+)', output)
            signal_match = search(r'Signal level=(-?\d+)', output)

            if quality_match:
                current = int(quality_match.group(1))
                max_val = int(quality_match.group(2))
                quality_percent = int((current / max_val) * 100)
                signal_dbm = signal_match.group(1) if signal_match else "N/A"
                results.append(f"📊 Signal: {quality_percent}% quality, {signal_dbm} dBm\n")
            else:
                results.append("📊 Signal: No quality data available\n")
        except Exception as e:
            results.append(f"❌ Signal check: {e}\n")

        # Test operation mode con iwconfig
        try:
            output = subprocess.check_output(["iwconfig", ifname], text=True, timeout=5)
            mode_match = search(r'Mode:(\w+)', output)
            if mode_match:
                results.append(f"🔧 Mode: {mode_match.group(1)}\n")
            else:
                results.append("🔧 Mode: Unknown\n")
        except Exception as e:
            results.append(f"❌ Mode check: {e}\n")

        return results

    def run_advanced_tests(self, ifname):
        """Run advanced comprehensive tests"""
        results = []
        results.append("\n   🔬 ADVANCED TESTS:\n")

        advanced_tests = [
            ("Frequency/Channel", f"iwconfig {ifname} | grep Frequency"),
            ("Bitrate", f"iwconfig {ifname} | grep BitRate"),
            ("Encryption", f"iwconfig {ifname} | grep Encryption"),
            ("Access Point", f"iwconfig {ifname} | grep 'Access Point'"),
        ]

        for test_name, cmd in advanced_tests:
            try:
                output = subprocess.check_output(cmd, shell=True, text=True, timeout=5)
                if output.strip():
                    results.append(f"   ✅ {test_name}: {output.strip()}\n")
                else:
                    results.append(f"   ⚠️  {test_name}: No data\n")
            except Exception as e:
                results.append(f"   ❌ {test_name}: Failed\nError: {e}")

        return results

    def run_performance_tests(self, ifname):
        """Run performance tests using system commands"""
        results = []
        results.append("\n   🚀 PERFORMANCE TESTS:\n")

        # Test scan capability con iwlist
        try:
            output = subprocess.check_output(["iwlist", ifname, "scan"],
                                             text=True, timeout=10,
                                             stderr=subprocess.STDOUT)
            cell_count = output.count("Cell ")
            results.append(f"   📡 Scan: Found {cell_count} networks\n")
        except subprocess.CalledProcessError as e:
            if "Device or resource busy" in e.output:
                results.append("   ⚠️  Scan: Interface busy (connected to network)\n")
            else:
                results.append(f"   ❌ Scan test: {e.output.strip()}\n")
        except Exception as e:
            results.append(f"   ❌ Scan test: {e}\n")

        # Test connectivity
        try:
            from Components.Network import iNetwork
            ip = iNetwork.getAdapterAttribute(ifname, "ip")
            if ip and ip != [0, 0, 0, 0]:
                results.append(f"   🌐 Connectivity: IP {'.'.join(map(str, ip))} - ONLINE\n")
            else:
                results.append("   🌐 Connectivity: No IP address - OFFLINE\n")
        except:
            results.append("   🌐 Connectivity: Unknown status\n")

        return results

    def suggest_solutions(self, no_interfaces=False):
        """Provide solution suggestions based on problems found"""
        suggestions = []
        suggestions.append("\n🔧 POSSIBLE SOLUTIONS:\n")

        if no_interfaces:
            suggestions.append("1. Check if WiFi adapter is properly connected\n")
            suggestions.append("2. Verify WiFi adapter is supported by your receiver\n")
            suggestions.append("3. Try different USB port for USB WiFi adapters\n")
            suggestions.append("4. Check if WiFi drivers are installed\n")
            suggestions.append("5. Restart the receiver and try again\n")

        else:
            suggestions.append("✅ All systems operational\n")
            suggestions.append("💡 Tips:\n")
            suggestions.append("   • Monitor signal strength for best performance\n")
            suggestions.append("   • Keep drivers updated\n")
            suggestions.append("   • Use 5GHz band for less interference\n")

        return suggestions

    def generate_summary(self, wifi_interfaces):
        """Generate diagnostic summary"""
        summary = []
        if wifi_interfaces:
            summary.append("✅ SYSTEM STATUS: WiFi hardware detected and functional\n")
            summary.append("🔧 METHOD: Using system commands (no root required)\n")
            summary.append("💡 All basic diagnostics available\n")
        else:
            summary.append("❌ SYSTEM STATUS: No WiFi interfaces detected\n")
            summary.append("🚨 Check hardware connection and drivers\n")
        return summary

    def display_results(self, results):
        if isinstance(results, list):
            self["diagnostics_output"].setText("".join(results))
        else:
            self["diagnostics_output"].setText(results)

    def clear_output(self):
        self["diagnostics_output"].setText("")

    def test_wireless_protocol(self, wireless):
        try:
            protocol = wireless.getWirelessName()
            return True, protocol
        except Exception as e:
            return False, str(e)

    def test_essid(self, wireless):
        try:
            essid = wireless.getEssid()
            return True, essid if essid else "Not connected"
        except Exception as e:
            return False, str(e)

    def test_ap_address(self, wireless):
        try:
            ap_addr = wireless.getAPaddr()
            return True, ap_addr
        except Exception as e:
            return False, str(e)

    def test_operation_mode(self, wireless):
        try:
            mode = wireless.getMode()
            return True, mode
        except Exception as e:
            return False, str(e)

    def test_frequency(self, wireless):
        try:
            freq = wireless.getFrequency()
            return True, freq
        except Exception as e:
            return False, str(e)

    def test_bitrate(self, wireless):
        try:
            bitrate = wireless.getBitrate()
            return True, bitrate
        except Exception as e:
            return False, str(e)

    def test_signal_quality(self, wireless):
        try:
            quality = wireless.getQualityAvg()
            if quality:
                return True, f"Quality: {quality.quality}%, Signal: {quality.siglevel} dBm"
            return False, "No quality data"
        except Exception as e:
            return False, str(e)

    def test_tx_power(self, wireless):
        try:
            txpower = wireless.getTXPower()
            return True, txpower
        except Exception as e:
            return False, str(e)

    def test_scan_capability(self, wireless):
        try:
            scan_results = wireless.scan()
            return True, f"Found {len(scan_results)} networks"
        except Exception as e:
            return False, str(e)

    def test_iwconfig_compatibility(self, wireless):
        """Test compatibilità funzioni iwconfig"""
        try:
            from .iwconfig import getBitrate, getTXPower, getEncryption
            bitrate_info = getBitrate(wireless)
            txpower_info = getTXPower(wireless)
            encryption_info = getEncryption(wireless)

            result = "iwconfig functions available - "
            if bitrate_info:
                result += "Bitrate OK "
            if txpower_info:
                result += "TXPower OK "
            if encryption_info:
                result += "Encryption OK"

            return True, result.strip()
        except Exception as e:
            return False, f"iwconfig error: {str(e)}"
