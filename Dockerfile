# Gunakan image Python yang sesuai
FROM python:3.10-slim

# Install PostgreSQL development libraries (untuk pg_config)
RUN apt-get update && \
    apt-get install -y libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Salin file requirements.txt ke container
COPY requirements.txt /app/

# Install dependensi
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Salin semua file aplikasi ke container
COPY . /app/

# Tentukan port yang digunakan oleh aplikasi
EXPOSE 5000

# Command untuk menjalankan aplikasi
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:$PORT", "app:app"]
