#!/usr/bin/env bash
set -o errexit

echo "🚀 Instalando Google Chrome para Selenium en Render..."
apt-get update
apt-get install -y wget gnupg unzip

# Agregar el repo oficial de Chrome estable
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

apt-get update
apt-get install -y google-chrome-stable

echo "✅ Chrome instalado en $(which google-chrome)"
google-chrome --version
