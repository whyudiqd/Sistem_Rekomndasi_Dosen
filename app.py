from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session
from rekomendasi import rekomendasi_dosen
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'rahasia123'  # dibutuhkan untuk flash message

# Konfigurasi upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Username dan password admin
USERNAME = 'admin'
PASSWORD = 'admin123'


# Halaman awal: Form input topik
@app.route('/')
def index():
    nama_mhs = session.get('mahasiswa_nama')
    is_admin = session.get('logged_in')

    return render_template('index.html', 
                           nama_mahasiswa=nama_mhs,
                           is_admin=is_admin)

    

# Halaman hasil rekomendasi
@app.route('/rekomendasi', methods=['POST'])
def hasil():
    topik_mahasiswa = request.form['topik']
    hasil_rekomendasi = rekomendasi_dosen(topik_mahasiswa)

# Ambil nama dan NIM dari session
    nama_mhs = session.get('mahasiswa_nama')
    nim_mhs = session.get('mahasiswa_nim')
    
    # Baca riwayat sebelumnya
    riwayat_path = 'data/riwayat.csv'
    if os.path.exists(riwayat_path):
        riwayat_df = pd.read_csv(riwayat_path)
    else:
        riwayat_df = pd.DataFrame(columns=['id', 'waktu', 'topik_mahasiswa', 'nama_dosen', 'bidang', 'skor'])

    id_awal = riwayat_df['id'].max() + 1 if not riwayat_df.empty else 1
    waktu = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Simpan setiap dosen rekomendasi ke riwayat
    for i, d in enumerate(hasil_rekomendasi):
        riwayat_df.loc[len(riwayat_df)] = [
            id_awal + i,
            waktu,
            f"{nama_mhs} ({nim_mhs}) - {topik_mahasiswa}",
            d['nama'],
            d['bidang'],
            round(d['skor'], 4)
        ]

    # Simpan kembali ke file
    riwayat_df.to_csv(riwayat_path, index=False)
    return render_template('hasil.html', rekomendasi=hasil_rekomendasi)

# Route upload CSV
@app.route('/upload', methods=['GET', 'POST'])
def upload_csv():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Tidak ada file di form!')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('File belum dipilih!')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filepath = os.path.join('data', 'dosen.csv')
            file.save(filepath)
            flash('Data dosen berhasil diupdate.')
            return redirect(url_for('lihat_dosen'))
    return render_template('upload.html')

# Dashboard dosen (opsional)
@app.route('/dosen')
def lihat_dosen():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    df = pd.read_csv('data/dosen.csv')
    data = df.to_dict(orient='records')
    return render_template('dosen.html', data=data)

@app.route('/tambah-dosen', methods=['GET', 'POST'])
def tambah_dosen():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        nama = request.form['nama']
        bidang = request.form['bidang']
        topik = request.form['topik']

        # Baca data lama
        df = pd.read_csv('data/dosen.csv')

        # Buat ID baru
        new_id = df['id'].max() + 1 if not df.empty else 1

        # Tambahkan data baru
        df.loc[len(df)] = [new_id, nama, bidang, topik]

        # Simpan kembali
        df.to_csv('data/dosen.csv', index=False)

        return redirect(url_for('lihat_dosen'))

    return render_template('tambah_dosen.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_input = request.form['username']
        password_input = request.form['password']

        if username_input == USERNAME and password_input == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('lihat_dosen'))
        else:
            return render_template('login.html', error="Username atau password salah.")
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/login-mahasiswa', methods=['GET', 'POST'])
def login_mahasiswa():
    if request.method == 'POST':
        nim_input = request.form['nim']
        password_input = request.form['password']
        print("Input NIM:", nim_input)
        print("Input Password:", password_input)

        df = pd.read_csv('data/mahasiswa.csv')
        df['nim'] = df['nim'].astype(str).str.strip()
        df['password'] = df['password'].astype(str).str.strip()
        print(df.head())  # debugging

        mahasiswa = df[(df['nim'] == nim_input) & (df['password'] == password_input)]

        if not mahasiswa.empty:
            session['mahasiswa_login'] = True
            session['mahasiswa_nama'] = mahasiswa.iloc[0]['nama']
            session['mahasiswa_nim'] = mahasiswa.iloc[0]['nim']
            return redirect(url_for('index'))
        else:
            return render_template('login_mahasiswa.html', error="NIM atau Password salah.")
    
    return render_template('login_mahasiswa.html')

@app.route('/admin/mahasiswa')
def halaman_mahasiswa():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('mahasiswa.html')


@app.route('/logout-mahasiswa')
def logout_mahasiswa():
    session.pop('mahasiswa_login', None)
    session.pop('mahasiswa_nama', None)
    session.pop('mahasiswa_nim', None)
    return redirect(url_for('login_mahasiswa'))


# Jalankan server
if __name__ == '__main__':
    print("Menjalankan Flask di http://127.0.0.1:5000")
    app.run(debug=True)

