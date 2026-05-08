# Pake base image Python versi 3.11 yang ringan
FROM python:3.11-slim

# Bikin folder /app di dalem container sebagai tempat kerja
WORKDIR /app

# Copy file requirements.txt duluan buat diinstall
COPY requirements.txt .

# Install semua library yang dibutuhin
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua sisa codingan web kamu ke dalem container
COPY . .

# Buka port 5000 biar bisa diakses dari luar
EXPOSE 5000

# Perintah buat ngejalanin aplikasinya pas container idup
CMD ["python", "app.py"]