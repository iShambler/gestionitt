#!/usr/bin/env bash
set -o errexit

echo "🚀 Instalando Google Chrome estable en Render..."

# Instalar dependencias
apt-get update
apt-get install -y wget gnupg unzip curl

# Agregar repo oficial de Chrome estable
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Instalar Chrome
apt-get update
apt-get install -y google-chrome-stable

echo "✅ Chrome instalado en:"
which google-chrome || echo "⚠️ Chrome no encontrado"
google-chrome --version || echo "⚠️ No se pudo obtener versión de Chrome"
