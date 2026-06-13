"""
algoritma/huffman.py
=========================
Huffman Coding — Kompresi & Dekompresi Lossless
========================================================

API Publik:
-----------
  compress_file(input_path, output_path) → dict
  decompress_file(input_path, output_path) → bool
"""

import heapq
import os
import struct
from collections import Counter

# ──────────────────────────────────────────────
# 1. Struktur Node untuk Pohon Huffman
# ──────────────────────────────────────────────
class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    # Agar antrean prioritas (heapq) bisa membandingkan node berdasarkan frekuensinya
    def __lt__(self, other):
        return self.freq < other.freq

# ──────────────────────────────────────────────
# 2. Fungsi Pembantu (Helper)
# ──────────────────────────────────────────────
def _build_codes(node, current_code, mapping):
    if node is None:
        return
    # Jika ini adalah node daun (punya karakter)
    if node.char is not None:
        mapping[node.char] = current_code
        return
    # Rekursif ke kiri (tambah '0') dan kanan (tambah '1')
    _build_codes(node.left, current_code + "0", mapping)
    _build_codes(node.right, current_code + "1", mapping)

def _build_tree_from_freqs(freqs):
    heap = [HuffmanNode(char, freq) for char, freq in freqs.items()]
    heapq.heapify(heap)

    # Tangani kasus khusus jika file hanya berisi 1 jenis karakter
    if len(heap) == 1:
        node = heapq.heappop(heap)
        root = HuffmanNode(None, node.freq)
        root.left = node
        heapq.heappush(heap, root)

    # Gabungkan dua node dengan frekuensi terkecil sampai tersisa 1 root
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)

    return heap[0] if heap else None

# ──────────────────────────────────────────────
# 3. Fungsi Utama: KOMPRESI
# ──────────────────────────────────────────────
def compress_file(input_path: str, output_path: str) -> dict:
    """Mengecilkan file dan menyimpan struktur pohonnya di dalam header file hasil."""
    
    # 1. Baca seluruh byte file asli
    with open(input_path, 'rb') as f:
        data = f.read()
    
    if not data:
        with open(output_path, 'wb') as f:
            pass
        return {"original_size": 0, "compressed_size": 0, "reduction": 0}

    # 2. Hitung frekuensi dan bangun Pohon Huffman
    freqs = Counter(data)
    root = _build_tree_from_freqs(freqs)
    
    mapping = {}
    _build_codes(root, "", mapping)

    # 3. Ubah data asli menjadi string biner panjang
    encoded_str = "".join(mapping[byte] for byte in data)
    
    # Tambahkan padding agar jumlah bit kelipatan 8
    padding = 8 - (len(encoded_str) % 8)
    encoded_str += "0" * padding
    
    # Kelompokkan jadi array byte sungguhan
    b_array = bytearray()
    for i in range(0, len(encoded_str), 8):
        b_array.append(int(encoded_str[i:i+8], 2))

    # 4. Tulis ke file baru (*.shrink)
    with open(output_path, 'wb') as out:
        # Tulis Header: Magic Word "HUFF" agar mudah dikenali
        out.write(b'HUFF')
        # Tulis jumlah kamus unik (2 bytes)
        out.write(struct.pack('<H', len(freqs)))
        # Tulis pasangan Karakter dan Frekuensinya
        for char, freq in freqs.items():
            out.write(struct.pack('<BQ', char, freq)) # 1 byte char, 8 byte frekuensi
        # Tulis info padding (1 byte)
        out.write(struct.pack('<B', padding))
        # Tulis data yang sudah dikompresi
        out.write(b_array)

    orig_size = os.path.getsize(input_path)
    comp_size = os.path.getsize(output_path)
    reduction = round((1 - comp_size / orig_size) * 100, 2) if orig_size else 0

    return {
        "original_size": orig_size,
        "compressed_size": comp_size,
        "reduction": reduction
    }

# ──────────────────────────────────────────────
# 4. Fungsi Utama: DEKOMPRESI
# ──────────────────────────────────────────────
def decompress_file(input_path: str, output_path: str) -> bool:
    """Mengembalikan file .shrink ke bentuk aslinya."""
    
    with open(input_path, 'rb') as f:
        # 1. Baca Header dan Validasi
        magic = f.read(4)
        if magic != b'HUFF':
            raise ValueError("Bukan format file hasil kompresi ShrinkLab!")
            
        num_freqs = struct.unpack('<H', f.read(2))[0]
        
        freqs = {}
        for _ in range(num_freqs):
            char, freq = struct.unpack('<BQ', f.read(9))
            freqs[char] = freq
            
        padding = struct.unpack('<B', f.read(1))[0]
        
        # 2. Baca isi data biner
        compressed_data = f.read()

    # 3. Bangun ulang pohon dari frekuensi yang dibaca
    root = _build_tree_from_freqs(freqs)
    
    # 4. Ubah byte kembali jadi string biner panjang
    encoded_str = ""
    for byte in compressed_data:
        encoded_str += f"{byte:08b}"
        
    # Buang padding di akhir
    if padding > 0:
        encoded_str = encoded_str[:-padding]

    # 5. Telusuri pohon untuk mendapatkan byte asli
    decoded_bytes = bytearray()
    current_node = root
    
    for bit in encoded_str:
        if bit == '0':
            current_node = current_node.left
        else:
            current_node = current_node.right
            
        if current_node.char is not None:
            decoded_bytes.append(current_node.char)
            current_node = root

    # 6. Simpan hasil dekompresi
    with open(output_path, 'wb') as out:
        out.write(decoded_bytes)
        
    return True