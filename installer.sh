#!/bin/bash

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

echo "Starting WiFi-Manager installation..."
cleanup

# Create temporary directory
mkdir -p "$TMPPATH" || { echo "❌ Failed to create temp directory"; exit 1; }

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

# Remove old installation if exists
echo "🧹 Removing old installation..."
[ -d "$PLUGINPATH" ] && rm -rf "$PLUGINPATH"

# Create destination directory
mkdir -p "$PLUGINPATH" || { echo "❌ Failed to create plugin directory"; cleanup; exit 1; }

# Copy plugin files
echo "🔧 Installing plugin files..."
if [ -d "$TMPPATH/WiFi-Manager-main/usr/lib/enigma2/python/Plugins/Extensions/WiFi-Manager" ]; then
    cp -r "$TMPPATH/WiFi-Manager-main/usr/lib/enigma2/python/Plugins/Extensions/WiFi-Manager"/* "$PLUGINPATH/"
elif [ -d "$TMPPATH/WiFi-Manager-main/usr" ]; then
    cp -r "$TMPPATH/WiFi-Manager-main/usr"/* /usr/
else
    # Try to find any Python files in the extracted structure
    find "$TMPPATH" -name "*.py" -exec cp --parents {} /usr/ \; 2>/dev/null
fi

sync

# VERIFICA MIGLIORATA - Controlla se ci sono file Python nella directory
echo "🔍 Verifying installation..."
if [ -d "$PLUGINPATH" ]; then
    FILE_COUNT=$(find "$PLUGINPATH" -name "*.py" -type f | wc -l)
    if [ $FILE_COUNT -gt 0 ]; then
        echo "✅ Plugin installed SUCCESSFULLY!"
        echo "📁 Location: $PLUGINPATH"
        echo "📄 Number of Python files found: $FILE_COUNT"
        echo "📋 Files installed:"
        find "$PLUGINPATH" -name "*.py" -type f | head -10
        
        # Cleanup
        cleanup
        
        # System info
        echo ""
        echo "#########################################################"
        echo "#               INSTALLED SUCCESSFULLY                  #"
        echo "#########################################################"
        echo "🔄 Restarting enigma2 in 3 seconds..."
        sleep 3
        killall -9 enigma2
        exit 0
    else
        echo "❌ Plugin directory exists but contains no Python files!"
    fi
else
    echo "❌ Plugin directory was not created!"
fi

echo "❌ Installation verification failed!"
cleanup
exit 1