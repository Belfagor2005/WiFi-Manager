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
from re import search
from json import loads
from six.moves.urllib.request import urlopen
from .. import _


def test_download_speed(interface=None, timeout=10):
    """Test download speed with better timeout handling"""
    try:
        test_servers = [
            "http://ipv4.download.thinkbroadband.com/5MB.zip",
            "http://speedtest.tele2.net/5MB.zip",
            "http://proof.ovh.net/files/10Mb.dat",
        ]

        # Quick connectivity check first
        try:
            ping_result = subprocess.run(['ping', '-c', '1', '-W', '2', '8.8.8.8'],
                                         capture_output=True, text=True, timeout=5)
            if ping_result.returncode != 0:
                return _("No internet connection")
        except subprocess.TimeoutExpired:
            return _("Connection timeout")

        for test_url in test_servers:
            try:
                print(f"Testing download from: {test_url}")
                start_time = time.time()

                # Usa timeout più aggressivo
                result = subprocess.run([
                    'wget', '-O', '/dev/null',
                    '--timeout=8', '--tries=1', test_url
                ], capture_output=True, text=True, timeout=timeout)

                end_time = time.time()

                if result.returncode == 0:
                    duration = end_time - start_time
                    # File size estimation
                    if "10Mb" in test_url:
                        file_size_mb = 10 / 8
                    elif "5MB" in test_url:
                        file_size_mb = 5
                    else:
                        file_size_mb = 1

                    speed_mbps = (file_size_mb * 8) / duration
                    return f"{speed_mbps:.2f} Mbps"

            except subprocess.TimeoutExpired:
                print(f"Timeout with server: {test_url}")
                continue
            except Exception as e:
                print(f"Error with server {test_url}: {e}")
                continue

        return "All download servers failed"

    except Exception as e:
        return _("Error: {error}").format(error=str(e))


def test_upload_speed(interface=None, timeout=10):
    """Test upload speed - simple version"""
    try:
        test_file = "/tmp/upload_test.bin"
        test_data = b'0' * 1024 * 100  # 100KB di dati

        with open(test_file, 'wb') as f:
            f.write(test_data)

        start_time = time.time()
        result = subprocess.run([
            'curl', '-X', 'POST', '--data-binary', f'@{test_file}',
            'http://httpbin.org/post', '--max-time', '10'
        ], capture_output=True, text=True, timeout=timeout)
        end_time = time.time()

        # Pulisci
        subprocess.run(['rm', '-f', test_file], capture_output=True)

        if result.returncode == 0:
            duration = end_time - start_time
            file_size_mb = 0.1  # 100KB = 0.1MB
            speed_mbps = (file_size_mb * 8) / duration
            return _("{speed:.2f} Mbps").format(speed=speed_mbps)
        else:
            return _("Upload test not available")

    except Exception as e:
        return _("Upload test failed: {error}").format(error=str(e))


def test_ping(host="8.8.8.8", count=3):
    """Test latency/ping"""
    try:
        result = subprocess.run(['ping', '-c', str(count), host],
                                capture_output=True, text=True)
        if result.returncode == 0:
            # DEBUG: print output to check format
            print(f"[DEBUG] Ping output: {result.stdout}")
            
            # MULTIPLE REGEX PATTERNS to cover different output formats
            patterns = [
                r'min/avg/max/[^=]*=\s*[\d.]+/([\d.]+)/[\d.]+/[\d.]+',  # Standard Linux format
                r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+',  # Alternative Linux format
                r'= [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms',  # Simplified format
                r'Average = ([\d.]+)ms',  # Windows format
                r'(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)',  # Raw numbers format
            ]

            for pattern in patterns:
                match = search(pattern, result.stdout)
                if match:
                    # For the raw numbers format, take the second group (average)
                    if len(match.groups()) >= 2:
                        ping_avg = match.group(2) if pattern == patterns[-1] else match.group(1)
                    else:
                        ping_avg = match.group(1)
                    return f"{ping_avg} ms"

            return _("Ping data not found")

        else:
            print(f"[DEBUG] Ping failed: {result.stderr}")
            return _("Ping failed")

    except Exception as e:
        print(f"[DEBUG] Ping error: {e}")
        return _("Error: {error}").format(error=str(e))


def extended_ping_test():
    """Extended ping test to multiple hosts"""
    hosts = [
        (_("Google DNS"), "8.8.8.8"),
        (_("Cloudflare"), "1.1.1.1"),
        (_("OpenDNS"), "208.67.222.222")
    ]

    results = []
    for name, host in hosts:
        ping_result = test_ping(host, 2)
        results.append(_("{name} ({host}): {ping}").format(name=name, host=host, ping=ping_result))

    return "\n".join(results)


def get_public_ip_info():
    """Get public IP information"""
    try:
        response = urlopen('http://ipinfo.io/json', timeout=10)
        data = loads(response.read().decode())
        return data
    except:
        return None


def get_network_interfaces():
    """Get network interface information"""
    try:
        result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
        interfaces = []
        current_interface = None

        for line in result.stdout.split('\n'):
            if line and not line.startswith(' '):
                current_interface = line.split()[1].rstrip(':')
                interfaces.append(current_interface)

        return interfaces
    except:
        return []


def multi_server_download_test(interface=None):
    """Test downloads from multiple servers"""
    servers = [
        ("Otenet Greece", "http://speedtest.ftp.otenet.gr/files/test1Mb.db"),
        ("Linode Frankfurt", "http://speedtest.frankfurt.linode.com/100MB-frankfurt.bin"),
    ]

    results = []
    for name, url in servers:
        try:
            start_time = time.time()
            result = subprocess.run(['wget', '-O', '/dev/null', url],
                                    capture_output=True, text=True, timeout=15)
            end_time = time.time()

            if result.returncode == 0:
                duration = end_time - start_time
                # URL-based size estimation
                if "100MB" in url:
                    size_mb = 100
                else:
                    size_mb = 1
                speed = (size_mb * 8) / duration
                results.append(_("{name}: {speed:.2f} Mbps").format(name=name, speed=speed))
            else:
                results.append(_("{name}: Failed").format(name=name))

        except subprocess.TimeoutExpired:
            results.append(_("{name}: Timeout").format(name=name))
        except Exception as e:
            results.append(_("{name}: Error {error}").format(name=name, error=e))

    return "\n".join(results)


def multi_server_upload_test(interface=None):
    """Multi-server upload test (simulated)"""
    # For uploading we use a simplified approach
    upload_result = test_upload_speed(interface)
    return _("Upload test: {result}").format(result=upload_result)


def connection_stability_test(interface=None, duration=5):
    """Connection stability test with timeout"""
    try:
        start_time = time.time()
        packets_sent = 0
        packets_lost = 0
        max_packets = 5

        while time.time() - start_time < duration and packets_sent < max_packets:
            try:
                result = subprocess.run(['ping', '-c', '1', '-W', '2', '8.8.8.8'],
                                        capture_output=True, text=True, timeout=5)
                packets_sent += 1
                if result.returncode != 0:
                    packets_lost += 1
                time.sleep(1)
            except subprocess.TimeoutExpired:
                packets_lost += 1
                packets_sent += 1
                continue

        if packets_sent > 0:
            loss_percentage = (packets_lost / packets_sent) * 100
            stability = _("Stable") if loss_percentage < 10 else _("Unstable")
            return _("Packets: {sent}, Lost: {lost} ({percentage:.1f}%) - {stability}").format(
                sent=packets_sent, lost=packets_lost, percentage=loss_percentage, stability=stability)
        else:
            return _("No packets sent")

    except Exception as e:
        return _("Stability test error: {error}").format(error=str(e))


def format_speed_result(speed_value):
    """Format the speed result in a readable way"""
    if isinstance(speed_value, (int, float)):
        if speed_value >= 1000:
            return f"{speed_value / 1000:.2f} Gbps"
        else:
            return f"{speed_value:.2f} Mbps"
    return speed_value


def test_connectivity():
    """Basic connectivity test"""
    return test_ping()


def quick_speed_test(interface=None):
    """Quick speed test"""
    download = test_download_speed(interface, timeout=15)
    upload = test_upload_speed(interface, timeout=15)
    ping = test_ping()

    return {
        'download': download,
        'upload': upload,
        'ping': ping
    }
