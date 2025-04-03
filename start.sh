#!/bin/bash

# Mengaktifkan virtual environment (opsional jika Railway sudah menangani dependencies)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Menjalankan aplikasi dengan gunicorn menggunakan PORT dari environment variable
exec gunicorn -w 4 --timeout 120 -b 0.0.0.0:$PORT app:app