# Gunakan image Python versi 3.9 sebagai dasar
FROM python:3.9-slim

# Tentukan direktori kerja di dalam container
WORKDIR /app

# Salin file requirements.txt ke dalam container
COPY requirements.txt /app/

# Install dependensi dari requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Salin seluruh aplikasi ke dalam container
COPY . /app/

# Tentukan port yang akan digunakan oleh aplikasi Flask
EXPOSE 8000

# Tentukan perintah untuk menjalankan aplikasi menggunakan gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
