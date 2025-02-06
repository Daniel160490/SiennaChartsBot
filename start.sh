#!/bin/bash
echo "Iniciando bot de SiennaCharts..."
pip show python-telegram-bot
pip install --no-cache-dir -r requirements.txt
python3 bot.py
