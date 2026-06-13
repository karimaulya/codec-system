# ShrinkLab

ShrinkLab adalah aplikasi web codec system sederhana yang dirancang untuk memanipulasi file media (Image, Audio, Video, dan Teks). Aplikasi ini mengimplementasikan algoritma Huffman Coding untuk kompresi dan dekompresi data tingkat byte (lossless), serta algoritma Least Significant Bit (LSB) untuk steganografi gambar. 

Proyek ini dibangun menggunakan Python (Flask) sebagai pemenuhan tugas Capstone Project.

---

## Fitur Utama

1. Compress & Decompress File (Huffman Algorithm)
   Menyusutkan ukuran file dan mengembalikannya ke bentuk mentahnya secara utuh (lossless). Proses membaca dan menulis dilakukan secara byte-per-byte.
2. Hide & Reveal Message (Steganography LSB)
   Menyisipkan pesan teks rahasia ke dalam susunan piksel file gambar tanpa mengubah visual gambar secara kasatmata, serta mengekstrak kembali pesan tersebut.

---

## Cara Menjalankan di Localhost (Local Environment)

Pastikan Python 3.x dan pip sudah terinstal di komputer Anda.

1. Clone Repository
   git clone https://github.com/username/codec-system.git
   cd codec-system

2. Aktifkan Virtual Environment (Direkomendasikan)
   - Pengguna Windows: env\Scripts\activate
   - Pengguna Mac/Linux: source env/bin/activate

3. Install Dependencies
   pip install flask pillow
   (Atau pip install -r requirements.txt jika file tersedia)

4. Jalankan Aplikasi
   python app.py

Buka browser dan akses alamat: http://127.0.0.1:5000

---

## Panduan File Uji Coba (Sangat Penting)

Karena algoritma ini dibangun murni menggunakan Python untuk mengolah data binary tingkat rendah, mohon perhatikan spesifikasi file berikut agar aplikasi berjalan optimal saat pengujian:

### Kompresi & Dekompresi (Huffman)
Algoritma Huffman menyusutkan data dengan mencari pola byte yang berulang.
- Sangat Direkomendasikan: File .wav (audio mentah), .bmp (gambar mentah), dan .txt. File-file ini belum terkompresi, sehingga persentase penyusutannya akan terlihat jelas.
- Untuk File Video: Gunakan video berformat .avi (uncompressed) dengan ukuran sangat kecil (di bawah 1 MB) atau durasi 1-2 detik agar proses komputasi tidak membebani sistem.
- Catatan untuk Video/File Kompleks: Jika memasukkan file yang sudah dikompresi tingkat tinggi (seperti .mp4, .mp3, .jpg, atau .png), ukuran hasil output .shrink mungkin akan sedikit lebih besar dari aslinya. Hal ini wajar secara matematis karena algoritma lossless tidak dapat merapatkan data yang sudah padat, ditambah adanya beban penyimpanan struktur kamus pohon Huffman ke dalam file output.

### Steganografi (Hide/Reveal)
Fitur ini memanipulasi nilai RGB dari sebuah gambar diam secara langsung.
- Wajib Gunakan: File .png atau .bmp dengan resolusi wajar (maksimal 500x500 px agar proses memuat lebih cepat).
- Jangan Gunakan: File .jpg atau .jpeg (karena sistem kompresi bawaannya akan merusak pesan rahasia) atau format video.

---

## Teknologi yang Digunakan

- Backend: Python 3, Flask, Pillow (Python Imaging Library)
- Frontend: HTML5, CSS3, Vanilla JavaScript
- Deployment: PythonAnywhere

---
Dibuat untuk penyelesaian Capstone Project.
