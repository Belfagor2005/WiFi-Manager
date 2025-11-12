#!/bin/bash

##setup command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/WiFi-Manager/main/installer.sh -O - | /bin/sh

######### Only These 2 lines to edit with new version ######
version='1.0'
changelog='\n- Init version Wifi Manager'
##############################################################

TMPPATH=/tmp/WiFi-Manager-main
FILEPATH=/tmp/main.tar.gz

# Determine plugin path based on architecture
if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/WiFi-Manager
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/WiFi-Manager
fi

# Cleanup function
cleanup() {
    echo "Cleaning up temporary files..."
    [ -d "$TMPPATH" ] && rm -rf "$TMPPATH"
    [ -f "$FILEPATH" ] && rm -f "$FILEPATH"
}

# Check package manager type
if [ -f /var/lib/dpkg/status ]; then
    STATUS=/var/lib/dpkg/status
    OSTYPE=DreamOs
    PKG_MANAGER="apt-get"
    echo "❌ WiFi-Manager package does not work on DreamOS!"
    exit 1
else
    STATUS=/var/lib/opkg/status
    OSTYPE=Enigma2
    PKG_MANAGER="opkg"
    INSTALL_CMD="install"
fi

echo "Starting WiFi-Manager installation..."
cleanup

# Create temporary directory
mkdir -p "$TMPPATH" || { echo "❌ Failed to create temp directory"; exit 1; }

# Install wget if missing
if ! command -v wget >/dev/null 2>&1; then
    echo "📦 Installing wget..."
    opkg update || { echo "❌ Failed to update package lists"; exit 1; }
    opkg install wget || { echo "❌ Failed to install wget"; exit 1; }
fi

# Detect Python version
if python --version 2>&1 | grep -q '^Python 3\.'; then
    echo "🐍 Python3 image detected"
    PYTHON=PY3
    Packagesix=python3-six
    Packagerequests=python3-requests
else
    echo "🐍 Python2 image detected"
    PYTHON=PY2
    Packagerequests=python-requests
fi

# Install required packages
install_pkg() {
    local pkg=$1
    if ! grep -qs "Package: $pkg" "$STATUS"; then
        echo "📦 Installing $pkg..."
        opkg update && opkg install "$pkg" || { echo "❌ Failed to install $pkg"; exit 1; }
    else
        echo "✅ $pkg is already installed"
    fi
}

# Install dependencies
[ "$PYTHON" = "PY3" ] && install_pkg "$Packagesix"
install_pkg "$Packagerequests"

# Download WiFi-Manager
echo "⬇️ Downloading WiFi-Manager..."
wget --no-check-certificate --timeout=30 'https://github.com/Belfagor2005/WiFi-Manager/archive/refs/heads/main.tar.gz' -O "$FILEPATH"
if [ $? -ne 0 ]; then
    echo "❌ Failed to download WiFi-Manager package!"
    cleanup
    exit 1
fi

# Extract package
echo "📦 Extracting package..."
tar -xzf "$FILEPATH" -C "$TMPPATH"
if [ $? -ne 0 ]; then
    echo "❌ Failed to extract WiFi-Manager package!"
    cleanup
    exit 1
fi

# Install files
echo "🔧 Installing plugin files..."
if [ -d "$TMPPATH/WiFi-Manager-main/usr" ]; then
    cp -r "$TMPPATH/WiFi-Manager-main/usr" /
    sync
else
    echo "❌ Source directory not found after extraction!"
    cleanup
    exit 1
fi

# Verify installation
if [ -d "$PLUGINPATH" ]; then
    echo "✅ Plugin installed successfully to: $PLUGINPATH"
else
    echo "❌ Error: Plugin installation failed - destination directory not found!"
    cleanup
    exit 1
fi

# Cleanup
cleanup

# System info
echo "📊 Gathering system information..."
FILE="/etc/image-version"
box_type=$(head -n 1 /etc/hostname 2>/dev/null || echo "Unknown")
distro_value=$(grep '^distro=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
distro_version=$(grep '^version=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
python_vers=$(python --version 2>&1)

cat <<EOF

#########################################################
#               INSTALLED SUCCESSFULLY                  #
#                developed by LULULLA                   #
#               https://corvoboys.org                   #
#########################################################
#           your Device will RESTART Now                #
#########################################################
^^^^^^^^^^Debug information:
BOX MODEL: $box_type
OS SYSTEM: $OSTYPE
PYTHON: $python_vers
IMAGE NAME: ${distro_value:-Unknown}
IMAGE VERSION: ${distro_version:-Unknown}
EOF

echo "🔄 Restarting enigma2 in 5 seconds..."
sleep 5
killall -9 enigma2
exit 0