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
from threading import Thread

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.ScrollLabel import ScrollLabel
from Components.ProgressBar import ProgressBar

try:
    from .speedtest_simple import Enigma2Speedtest
except ImportError as e:
    print(f"SpeedtestSimple import error: {e}")
    Enigma2Speedtest = None

from . import speedtest
from .tools import get_wifi_interfaces
from .. import _


class WiFiSpeedtestManager(Screen):
    skin = """
    <screen position="center,center" size="800,700" title="WiFi Speed Test">
        <widget name="status_label" position="20,20" size="760,30" font="Regular;24" halign="center" />
        <widget name="progress" position="20,60" size="760,30" />
        <widget name="results" position="20,100" size="760,512" font="Regular;20" />
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
        self.speedtest = None
        self.is_testing = False
        self.current_test = None
        self.interface = get_wifi_interfaces

        self["status_label"] = Label(_("Select a speed test type"))
        self["progress"] = ProgressBar()
        self["results"] = ScrollLabel()

        self["key_red"] = Button(_("Close"))
        self["key_green"] = Button(_("Quick Test"))
        self["key_yellow"] = Button(_("Full Test"))
        self["key_blue"] = Button(_("Details"))

        self["progress"].setRange((0, 100))
        self["progress"].setValue(0)

        self["actions"] = ActionMap(["ColorActions", "OkCancelActions", "DirectionActions"], {
            "red": self.close,
            "green": self.quick_test,
            "yellow": self.full_test,
            "blue": self.detailed_test,
            "cancel": self.close,
            "ok": self.show_results,
            "up": self.keyUp,
            "down": self.keyDown,
            "left": self.keyLeft,
            "right": self.keyRight
        })

        self.setTitle(_("WiFi Speed Test Manager"))
        self.update_buttons()

    def update_buttons(self):
        """Update the state of the buttons"""
        # self["results"].setText("")
        if self.is_testing:
            self["key_green"].setText("")
            self["key_yellow"].setText("")
            self["key_blue"].setText("")
        else:
            self["key_green"].setText(_("Quick Test"))
            self["key_yellow"].setText(_("Full Test"))
            self["key_blue"].setText(_("Details"))

    def keyUp(self):
        """Handle UP key - navigate and auto-select"""
        print("[DEBUG] UP pressed")
        self["results"].pageUp()
        self.update_buttons()

    def keyDown(self):
        """Handle DOWN key - navigate and auto-select"""
        print("[DEBUG] DOWN pressed")
        self["results"].pageDown()
        self.update_buttons()

    def keyLeft(self):
        """Handle LEFT key - navigate and auto-select"""
        print("[DEBUG] LEFT pressed")
        self["results"].pageUp()
        self.update_buttons()

    def keyRight(self):
        """Handle RIGHT key - navigate and auto-select"""
        print("[DEBUG] RIGHT pressed")
        self["results"].pageDown()
        self.update_buttons()

    def _check_cancellation(self):
        """Check if test should be cancelled"""
        if not self.is_testing:
            self.show_error(_("Test cancelled"))
            return False
        return True

    def quick_test(self):
        """Quick speed test"""
        if self.is_testing:
            return

        self.is_testing = True
        self.update_buttons()
        self["results"].setText(_("wait..."))
        self["status_label"].setText(_("Running quick speed test..."))
        self["progress"].setValue(0)
        Thread(target=self._run_quick_test).start()

    def full_test(self):
        """Full speed test"""
        if self.is_testing:
            return

        self.is_testing = True
        self.update_buttons()
        self["results"].setText(_("wait..."))
        self["status_label"].setText(_("Running full speed test..."))
        self["progress"].setValue(0)

        Thread(target=self._run_full_test).start()

    def detailed_test(self):
        """Detailed test with more information"""
        if self.is_testing:
            return

        self.is_testing = True
        self.update_buttons()
        self["results"].setText(_("wait..."))
        self["status_label"].setText(_("Running detailed speed test..."))
        self["progress"].setValue(0)

        Thread(target=self._run_detailed_test).start()

    def _get_client_information(self):
        """Get client network information"""
        try:
            import socket
            import json
            from urllib.request import urlopen

            info = []

            # Hostname
            hostname = socket.gethostname()
            info.append(_("Hostname: {hostname}").format(hostname=hostname))

            # Public IP and ISP info
            try:
                ip_response = urlopen('http://ipinfo.io/json', timeout=5)
                ip_data = json.loads(ip_response.read().decode())
                info.append(_("Public IP: {ip}").format(ip=ip_data.get('ip', 'Unknown')))
                info.append(_("Location: {city}, {country}").format(
                    city=ip_data.get('city', 'Unknown'),
                    country=ip_data.get('country', 'Unknown')
                ))
                info.append(_("ISP: {isp}").format(isp=ip_data.get('org', 'Unknown')))
            except:
                info.append(_("Public IP: Unable to determine"))

            return "\n".join(info)
        except Exception as e:
            return _("Client info error: {error}").format(error=str(e))

    def _get_server_information(self):
        """Get server information"""
        try:
            servers = [
                ("Primary DNS", "8.8.8.8", "Google"),
                ("Secondary DNS", "1.1.1.1", "Cloudflare"),
                ("Tertiary DNS", "208.67.222.222", "OpenDNS")
            ]

            server_info = []
            for name, host, sponsor in servers:
                ping_result = speedtest.test_ping(host, 1)
                server_info.append(f"{name} ({sponsor}): {ping_result}")

            return "\n".join(server_info)
        except Exception as e:
            return _("Server info error: {error}").format(error=str(e))

    def _get_network_information(self):
        """Get detailed network information"""
        try:
            info = []

            # Interface information
            interfaces = get_wifi_interfaces()
            if interfaces:
                info.append(_("Network Interface: {interface}").format(interface=interfaces[0]))

            # Gateway
            try:
                result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'default' in line:
                        gateway = line.split()[2]
                        info.append(_("Gateway: {gateway}").format(gateway=gateway))
                        break
            except:
                pass

            return "\n".join(info) if info else _("Network information unavailable")
        except Exception as e:
            return _("Network info error: {error}").format(error=str(e))

    def _run_quick_test(self):
        """Run a quick test using speedtest.quick_speed_test"""
        try:
            self.current_test = "quick"

            self.update_progress(20, _("Testing connectivity..."))
            ping_result = speedtest.test_ping()

            self.update_progress(40, _("Testing download speed..."))
            download_result = speedtest.test_download_speed(self.interface)

            self.update_progress(70, _("Testing upload speed..."))
            upload_result = speedtest.test_upload_speed(self.interface)

            self.update_progress(100, _("Quick test completed"))

            # Formatta i risultati
            results_text = _("=== QUICK SPEED TEST RESULTS ===\n\n")
            results_text += _("Ping/Latency: {ping}\n").format(ping=ping_result)
            results_text += _("Download Speed: {download}\n").format(download=download_result)
            results_text += _("Upload Speed: {upload}\n").format(upload=upload_result)
            results_text += self._evaluate_connection_quality(download_result, ping_result)

            self.show_results_success(results_text)

        except Exception as e:
            self.show_error(_("Quick test error: {error}").format(error=str(e)))

    def _run_full_test(self):
        """Runs full test in a separate thread with timeout handling"""
        try:
            self.current_test = "full"
            results_text = _("=== COMPREHENSIVE SPEED TEST ===\n\n")

            # 0. Client information
            if not self._check_cancellation():
                return
            self.update_progress(5, _("Gathering client information..."))
            client_info = self._get_client_information()
            results_text += _("=== CLIENT INFORMATION ===\n{info}\n\n").format(info=client_info)

            # 1. Extended ping test
            if not self._check_cancellation():
                return
            self.update_progress(15, _("Testing latency to multiple hosts..."))
            extended_ping = speedtest.extended_ping_test()
            results_text += _("=== LATENCY TEST ===\n{ping}\n\n").format(ping=extended_ping)

            # 2. Server information
            if not self._check_cancellation():
                return
            self.update_progress(25, _("Finding best server..."))
            server_info = self._get_server_information()
            results_text += _("=== SERVER INFORMATION ===\n{server}\n\n").format(server=server_info)

            # 3. Multiple download tests
            if not self._check_cancellation():
                return
            self.update_progress(30, _("Testing download speed (multiple servers)..."))
            multi_download = speedtest.multi_server_download_test(self.interface)
            results_text += _("=== DOWNLOAD SPEED TEST ===\n{download}\n\n").format(download=multi_download)

            # 4. Upload test
            if not self._check_cancellation():
                return
            self.update_progress(60, _("Testing upload speed..."))
            upload_result = speedtest.test_upload_speed(self.interface)
            results_text += _("=== UPLOAD SPEED TEST ===\n{upload}\n\n").format(upload=upload_result)

            # 5. Stability test
            if not self._check_cancellation():
                return
            self.update_progress(80, _("Testing connection stability..."))
            stability = speedtest.connection_stability_test(self.interface)
            results_text += _("=== CONNECTION STABILITY ===\n{stability}\n\n").format(stability=stability)

            # 6. Network information
            if not self._check_cancellation():
                return
            self.update_progress(85, _("Gathering network details..."))
            network_info = self._get_network_information()
            results_text += _("=== NETWORK INFORMATION ===\n{network}\n\n").format(network=network_info)

            # 7. Final connectivity test
            if not self._check_cancellation():
                return
            self.update_progress(90, _("Final connectivity check..."))
            connectivity = speedtest.test_connectivity()
            results_text += _("=== FINAL CHECK ===\nConnectivity: {conn}\n").format(conn=connectivity)

            # Complete
            self.update_progress(100, _("Full test completed"))
            self.show_results_success(results_text)

        except Exception as e:
            self.show_error(_("Full test error: {error}").format(error=str(e)))

    def _run_detailed_test(self):
        """Run detailed test using SpeedtestSimple"""
        try:
            self.current_test = "detailed"

            if not Enigma2Speedtest:
                self.show_error(_("SpeedtestSimple not available"))
                return

            def callback(stage, message=None):
                stages = {
                    'checking_connection': (10, _("Checking internet connection...")),
                    'client_info_start': (20, _("Getting client information...")),
                    'client_info_complete': (25, _("Client info completed")),
                    'ping_start': (30, _("Testing latency...")),
                    'ping_complete': (40, _("Latency test completed")),
                    'server_selection_start': (45, _("Finding best server...")),
                    'server_found': (50, _("Server found")),
                    'download_start': (60, _("Testing download speed...")),
                    'download_complete': (80, _("Download test completed")),
                    'upload_start': (85, _("Estimating upload speed...")),
                    'upload_complete': (95, _("Upload estimation completed")),
                    'error': (0, _("Test failed")),
                }
                if stage in stages:
                    progress, default_status = stages[stage]
                    status = message if message else default_status
                    self.update_progress(progress, status)

            self.update_progress(5, _("Initializing detailed speed test..."))
            speedtest_simple = Enigma2Speedtest()

            results = speedtest_simple.run_test(callback=callback)

            if results:
                self.update_progress(100, _("Detailed test completed"))
                results_text = speedtest_simple.format_results()
                self.show_results_success(results_text)
            else:
                self.show_error(_("Detailed speed test failed - Check internet connection"))

        except Exception as e:
            self.show_error(_("Detailed test error: {error}").format(error=str(e)))

    def _evaluate_connection_quality(self, download_result, ping_result):
        """Evaluate connection quality based on test results"""
        evaluation = _("\n=== CONNECTION QUALITY ===\n")

        try:
            # Analyze download
            if "Mbps" in download_result:
                download_speed = float(download_result.split()[0])
                if download_speed > 50:
                    evaluation += _("Excellent download speed\n")
                elif download_speed > 20:
                    evaluation += _("Good download speed\n")
                elif download_speed > 5:
                    evaluation += _("Average download speed\n")
                else:
                    evaluation += _("Poor download speed\n")
            else:
                evaluation += _("Download speed unavailable\n")

            # Analyze ping
            if "ms" in ping_result:
                ping_time = float(ping_result.split()[0])
                if ping_time < 50:
                    evaluation += _("Excellent latency\n")
                elif ping_time < 100:
                    evaluation += _("Good latency\n")
                elif ping_time < 200:
                    evaluation += _("Average latency\n")
                else:
                    evaluation += _("Poor latency\n")
            else:
                evaluation += _("Latency unavailable\n")

        except:
            evaluation += _("Quality assessment unavailable\n")

        return evaluation

    def update_progress(self, value, status):
        """Update progress and status (thread-safe)"""
        self["progress"].setValue(value)
        self["status_label"].setText(status)

    def _format_results(self, download, upload, ping):
        """Format speed test results"""
        results = _("=== SPEED TEST RESULTS ===\n\n")
        results += _("Download Speed: %s\n") % (download if download else _("Failed"))
        results += _("Upload Speed: %s\n") % (upload if upload else _("Failed"))
        results += _("Latency: %s\n") % (ping if ping else _("Failed"))

        # Quality evaluation
        results += _("\n=== QUALITY ASSESSMENT ===\n")
        if download and isinstance(download, str) and 'Mbps' in download:
            try:
                download_value = float(download.split()[0])
                if download_value > 10:
                    results += _("Excellent download speed\n")
                elif download_value > 5:
                    results += _("Good download speed\n")
                else:
                    results += _("Poor download speed\n")
            except:
                results += _("Unable to assess download quality\n")
        else:
            results += _("Unable to assess download quality\n")
        return results

    def show_results_success(self, results):
        """Show results successfully"""
        self.is_testing = False
        self.update_buttons()
        self["results"].setText(results)
        self["status_label"].setText(_("Test completed - See results below"))

        try:
            def callback(result=None):
                pass

            self.session.openWithCallback(callback, MessageBox,
                                          _("Test completed!"),
                                          MessageBox.TYPE_INFO,
                                          timeout=4)
        except:
            pass

    def show_error(self, message):
        """Show error"""
        self.is_testing = False
        self.update_buttons()
        self["status_label"].setText(_("Test failed"))

        def error_callback(result=None):
            pass

        self.session.openWithCallback(error_callback, MessageBox,
                                      message,
                                      MessageBox.TYPE_ERROR)

    def show_results(self):
        """Show/hide detailed results"""
        if self["results"].isVisible():
            self["results"].hide()
        else:
            self["results"].show()

    def close(self):
        """Close the screen with proper test termination"""
        if self.is_testing:
            # Stop the test gracefully
            self.is_testing = False
            self["status_label"].setText(_("Cancelling test..."))

            # Wait a bit for thread to terminate
            import time
            for i in range(5):
                if not self.is_testing:
                    break
                time.sleep(0.1)

            self.session.open(MessageBox, _("Test cancelled"), MessageBox.TYPE_WARNING)
            # Don't close immediately, let user see the cancellation
            return

        Screen.close(self)
