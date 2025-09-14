#!/bin/bash
# Скрипт для запуска Streamlit приложения

cd /var/parsing_vesti42
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0