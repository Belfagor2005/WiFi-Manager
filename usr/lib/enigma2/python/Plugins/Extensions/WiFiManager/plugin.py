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

from Plugins.Plugin import PluginDescriptor


def main(session, **kwargs):
    from .WiFiManager import WiFiManagerMain
    return session.open(WiFiManagerMain)


def Plugins(**kwargs):
    return PluginDescriptor(
        name="WiFi Manager",
        description="Advanced WiFi diagnostic tools",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        icon="plugin.png",
        fnc=main,
        needsRestart=True,
    )


# /usr/lib/enigma2/python/Plugins/Extensions/WiFiManager/
# ├── __init__.py
# ├── plugin.py                 # Main plugin descriptor
# ├── plugin.png                # Icon Plugin
# ├── WiFiManager.py            # Main screen manager
# ├── modules/
# │   ├── __init__.py
# │   ├── scanner.py           # Scanner reti WiFi
# │   ├── monitor.py           # Monitor qualità segnale
# │   ├── config.py            # Configurazione avanzata
# │   ├── diagnostics.py       # Diagnostic
# │   ├── flags.py             # Diagnostic
# │   ├── iwlibs.py            # Diagnostic
# │   ├── iwconfig.py          # Utilities
# │   ├── iwlist.py            # Utilities
# │   ├── connect.py           # Connect to
# │   ├── speedtest_managerpy  # Utilities
# │   ├── speedtest.py         # Connect to
# │   ├── speedtest_simple.py  # Connect to
# │   ├── detailed_info.py     # Detailed info
# │   ├── iwlist_tools.py      # Not Used
# │   └── tools.py             # Utilities
# ├── locale
# │   ├── WiFiManager.pot
# │   ├── locale\en\LC_MESSAGES\
# │   └── .....
# └── icons/
    # ├── plugin.png            # Not Used
    # ├── selected-border.png
    # ├── wifi-connect.png
    # ├── wifi-scan.png
    # ├── wifi-monitor.png
    # ├── wifi-config
    # ├── wifi-tools
    # ├── wifi-off.png
    # ├── wifi-on.png
    # ├── wifi-scan.png
    # ├── wifi-info.png
    # └── wifi-diagnostic.png
    
