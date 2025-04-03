#!/bin/bash

# Mengaktifkan virtual environment di Linux
source venv/bin/activate

# Menjalankan aplikasi dengan gunicorn pada port 3000
exec gunicorn -b 0.0.0.0:3000 app:app
