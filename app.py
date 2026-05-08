import os
import uuid
import pymysql
import boto3
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_key_untuk_flask"

# Konfigurasi S3 Client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
CLOUDFRONT_URL = os.getenv('CLOUDFRONT_URL')

# Fungsi Koneksi Database (RDS)
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor
    )

# Buat tabel otomatis jika belum ada di RDS
def init_db():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laporan (
                id INT AUTO_INCREMENT PRIMARY KEY,
                judul VARCHAR(255) NOT NULL,
                deskripsi TEXT NOT NULL,
                lokasi VARCHAR(255) NOT NULL,
                foto_url VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'Menunggu'
            )
        ''')
    conn.commit()
    conn.close()

# Inisialisasi DB saat aplikasi dijalankan
try:
    init_db()
except Exception as e:
    print(f"Gagal inisialisasi DB (Cek koneksi RDS): {e}")

@app.route('/')
def index():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM laporan ORDER BY id DESC")
        laporan_list = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', laporan_list=laporan_list, cloudfront_url=CLOUDFRONT_URL)

@app.route('/submit', methods=['POST'])
def submit():
    judul = request.form['judul']
    deskripsi = request.form['deskripsi']
    lokasi = request.form['lokasi']
    foto = request.files['foto']
    
    foto_filename = ""
    
    # Logika Upload ke Amazon S3
    if foto:
        file_extension = foto.filename.split('.')[-1]
        foto_filename = f"{uuid.uuid4().hex}.{file_extension}"
        try:
            s3_client.upload_fileobj(
                foto,
                BUCKET_NAME,
                foto_filename,
                ExtraArgs={'ContentType': foto.content_type}
            )
        except Exception as e:
            flash(f"Gagal upload ke S3: {e}")
            return redirect(url_for('index'))

    # Logika Simpan Data ke Amazon RDS
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO laporan (judul, deskripsi, lokasi, foto_url) VALUES (%s, %s, %s, %s)",
            (judul, deskripsi, lokasi, foto_filename)
        )
    conn.commit()
    conn.close()
    
    flash("Laporan berhasil dikirim!")
    return redirect(url_for('index'))

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    status_baru = request.form['status']
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE laporan SET status = %s WHERE id = %s", (status_baru, id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)