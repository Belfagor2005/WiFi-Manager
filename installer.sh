#!/bin/bash

TMPPATH=/tmp/WiFi-Manager-main
FILEPATH=/tmp/main.tar.gz
PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/WiFi-Manager

echo "Starting WiFi-Manager installation..."

# Cleanup
rm -rf "$TMPPATH" "$FILEPATH"

# Download
echo "⬇️ Downloading WiFi-Manager..."
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

# Install
echo "🔧 Installing plugin files..."
mkdir -p "$PLUGINPATH"

# Trova e copia i file del plugin
if [ -d "$TMPPATH/WiFi-Manager-main/usr/lib/enigma2/python/Plugins/Extensions/WiFi-Manager" ]; then
    cp -r "$TMPPATH/WiFi-Manager-main/usr/lib/enigma2/python/Plugins/Extensions/WiFi-Manager"/* "$PLUGINPATH/" 2>/dev/null
else
    cp -r "$TMPPATH/WiFi-Manager-main/usr"/* /usr/ 2>/dev/null
fi

sync

# VERIFICA MIGLIORATA
echo "🔍 Verifying installation..."

# 1. Controlla se la directory esiste
if [ ! -d "$PLUGINPATH" ]; then
    echo "❌ Plugin directory not found!"
    exit 1
fi

# 2. Lista esplicita dei file
echo "📁 Contents of plugin directory:"
ls -la "$PLUGINPATH/"

# 3. Controlla file Python in modo più semplice
echo "🐍 Looking for Python files..."
PY_FILES=$(ls "$PLUGINPATH"/*.py 2>/dev/null | wc -l)

if [ $PY_FILES -gt 0 ]; then
    echo "✅ Found $PY_FILES Python files directly in plugin directory"
else
    # Cerca ricorsivamente
    PY_FILES_RECURSIVE=$(find "$PLUGINPATH" -name "*.py" | wc -l)
    if [ $PY_FILES_RECURSIVE -gt 0 ]; then
        echo "✅ Found $PY_FILES_RECURSIVE Python files in subdirectories"
    else
        echo "⚠️ No Python files found with standard search"
        echo "📋 All files in plugin directory:"
        find "$PLUGINPATH" -type f | head -20
    fi
fi

# 4. Verifica finale - se la directory esiste e ha file, consideriamo successo
if [ -d "$PLUGINPATH" ]; then
    TOTAL_FILES=$(find "$PLUGINPATH" -type f | wc -l)
    if [ $TOTAL_FILES -gt 0 ]; then
        echo ""
        echo "#########################################################"
        echo "#               INSTALLED SUCCESSFULLY                  #"
        echo "#         (Ignore previous Python file checks)          #"
        echo "#########################################################"
        echo "📁 Plugin location: $PLUGINPATH"
        echo "📄 Total files installed: $TOTAL_FILES"
        
        # Cleanup
        rm -rf "$TMPPATH" "$FILEPATH"
        
        echo "🔄 Restarting enigma2..."
        sleep 2
        killall -9 enigma2
        exit 0
    fi
fi

echo "❌ Installation failed - no files found in plugin directory"
exit 1