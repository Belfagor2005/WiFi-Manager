#!/bin/bash

TMPPATH=/tmp/WiFiManager-main
FILEPATH=/tmp/main.tar.gz
PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/WiFiManager

echo "Starting WiFiManager installation..."

# Cleanup
rm -rf "$TMPPATH" "$FILEPATH"

# Download
echo "⬇️ Downloading WiFiManager..."
wget --no-check-certificate 'https://github.com/Belfagor2005/WiFi-Manager/archive/refs/heads/main.tar.gz' -O "$FILEPATH" || {
    echo "❌ Download failed!"
    exit 1
}

# Extract
echo "📦 Extracting package..."
mkdir -p "$TMPPATH"
tar -xzf "$FILEPATH" -C "$TMPPATH" || {
    echo "❌ Extraction failed!"
    exit 1
}

# Install - ora con il nome CORRETTO WiFiManager
echo "🔧 Installing plugin files..."
mkdir -p "$PLUGINPATH"

# Cerca la directory con il nome corretto
if [ -d "$TMPPATH/WiFi-Manager-main/usr/lib/enigma2/python/Plugins/Extensions/WiFiManager" ]; then
    cp -r "$TMPPATH/WiFi-Manager-main/usr/lib/enigma2/python/Plugins/Extensions/WiFiManager"/* "$PLUGINPATH/" 2>/dev/null
    echo "✅ Copied from WiFiManager directory"
else
    # Copia tutto l'albero usr
    cp -r "$TMPPATH/WiFi-Manager-main/usr"/* /usr/ 2>/dev/null
    echo "✅ Copied entire usr structure"
fi

sync

# Verifica
echo "🔍 Verifying installation..."
if [ -d "$PLUGINPATH" ]; then
    echo "✅ Plugin directory found: $PLUGINPATH"
    echo "📁 Contents:"
    ls -la "$PLUGINPATH/"
    
    echo ""
    echo "#########################################################"
    echo "#               INSTALLED SUCCESSFULLY                  #"
    echo "#########################################################"
    echo "🔄 Restarting enigma2..."
    
    # Cleanup
    rm -rf "$TMPPATH" "$FILEPATH"
    
    sleep 2
    killall -9 enigma2
    exit 0
else
    echo "❌ Plugin directory not found at: $PLUGINPATH"
    echo "📋 Available directories in tmp:"
    find "$TMPPATH" -type d -name "*WiFi*" | head -10
    exit 1
fi