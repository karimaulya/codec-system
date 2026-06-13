from flask import Flask, render_template, request, send_from_directory
import os

# Mengimpor mesin algoritma yang sudah kamu buat
from algoritma.huffman import compress_file, decompress_file
from algoritma.steganografi import embed_message, extract_message

app = Flask(__name__)

# ==========================================
# 1. SETUP FOLDER PENYIMPANAN
# ==========================================
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/outputs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# ==========================================
# 2. ROUTING HALAMAN UTAMA
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# 3. ROUTING EKSEKUSI ALGORITMA
# ==========================================
@app.route('/proses', methods=['POST'])
def proses():
    # Pengecekan file dasar
    if 'file_input' not in request.files:
        return "Tidak ada file yang di-upload", 400
    file = request.files['file_input']
    if file.filename == '':
        return "Nama file kosong", 400

    # Menangkap pilihan user dari form HTML
    algoritma = request.form.get('algoritma')
    pesan_rahasia = request.form.get('pesan_rahasia', '')

    # Simpan file asli yang di-upload
    input_filename = file.filename
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
    file.save(input_path)

    # Siapkan variabel dasar untuk dikirim ke UI
    ukuran_asli_mb = round(os.path.getsize(input_path) / (1024 * 1024), 3)
    ukuran_baru_mb = ukuran_asli_mb
    persentase = 0
    output_filename = input_filename
    pesan_terungkap = None  # Khusus untuk fitur Reveal Steganografi

    try:
        # CABANG 1: KOMPRESI (HUFFMAN)
        if algoritma == 'kompresi':
            output_filename = input_filename + '.shrink'
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            stats = compress_file(input_path, output_path)
            
            ukuran_baru_mb = round(stats['compressed_size'] / (1024 * 1024), 3)
            persentase = stats['reduction']

        # CABANG 2: DEKOMPRESI (HUFFMAN)
        elif algoritma == 'dekompresi':
            # Hilangkan akhiran .shrink kalau ada, misal: video.mp4.shrink -> video.mp4
            if input_filename.endswith('.shrink'):
                output_filename = input_filename.replace('.shrink', '')
            else:
                output_filename = 'decoded_' + input_filename
                
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            decompress_file(input_path, output_path)
            
            ukuran_baru_mb = round(os.path.getsize(output_path) / (1024 * 1024), 3)
            # Karena ini dekompresi (membesar lagi), persentase tidak terlalu relevan (bisa diset 0)

        # CABANG 3: STEGANO - HIDE MESSAGE
        elif algoritma == 'stegano_hide':
            # Hasil steganografi LSB wajib berformat .png agar tidak rusak
            nama_tanpa_ext = os.path.splitext(input_filename)[0]
            output_filename = nama_tanpa_ext + '_stego.png'
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            embed_message(input_path, pesan_rahasia, output_path)
            ukuran_baru_mb = round(os.path.getsize(output_path) / (1024 * 1024), 3)

        # CABANG 4: STEGANO - REVEAL MESSAGE
        elif algoritma == 'stegano_reveal':
            # Ini spesial, tidak menghasilkan file baru, tapi menghasilkan teks!
            pesan_terungkap = extract_message(input_path)
            output_path = input_path # Menghindari error saat tombol download ditekan

        # Lempar semua data ke halaman hasil.html
        return render_template(
            'hasil.html',
            nama_file=output_filename,
            ukuran_asli=ukuran_asli_mb,
            ukuran_baru=ukuran_baru_mb,
            persentase=persentase,
            pesan_terungkap=pesan_terungkap
        )

    except Exception as e:
        # Menangkap error kalau dosen iseng upload file aneh atau file corrupt
        return f"<h3>Terjadi Kesalahan!</h3><p>{str(e)}</p><a href='/'>Kembali</a>", 500

# ==========================================
# 4. ROUTING DOWNLOAD FILE
# ==========================================
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)