"""
algoritma/steganografi.py
=========================
LSB Image Steganography — Sisip & Ekstrak Pesan Rahasia
========================================================

Menggunakan teknik Least Significant Bit (LSB):
  • 1 bit pesan disisipkan ke bit paling kecil tiap channel pixel
  • Perubahan pada gambar tidak terlihat oleh mata manusia

API Publik:
-----------
  embed_message(image_path, message, output_path, bits_per_channel=1) → stats
  extract_message(image_path) → str
  embed_bytes(image_path, payload_bytes, output_path, bits_per_channel=1) → stats
  extract_bytes(image_path) → bytes
  get_capacity(image_path) → dict

Format Header Pesan (disisipkan sebelum data):
-----------------------------------------------
  [4 bytes]  magic   : 0xDEADBEEF  (untuk validasi)
  [4 bytes]  length  : panjang payload dalam byte (little-endian uint32)
  [N bytes]  payload : isi pesan (UTF-8 untuk embed_message)

Dukungan format gambar: PNG, BMP, TIFF (lossless).
JPEG tidak disarankan karena kompresi lossy akan merusak LSB.
"""

import struct
from pathlib import Path
from typing import Tuple, Union

try:
    from PIL import Image
except ImportError:
    raise ImportError(
        "Pillow belum terinstal. Jalankan: pip install Pillow"
    )


# ──────────────────────────────────────────────
# Konstanta
# ──────────────────────────────────────────────

_MAGIC = 0xDEADBEEF
_HEADER_SIZE = 8          # 4 byte magic + 4 byte length
_SUPPORTED_FORMATS = {".png", ".bmp", ".tiff", ".tif"}
_LOSSY_FORMATS = {".jpg", ".jpeg", ".webp"}


# ──────────────────────────────────────────────
# 1.  Validasi & utilitas
# ──────────────────────────────────────────────

def _validate_image_path(path: str) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File gambar tidak ditemukan: {path}")
    suffix = p.suffix.lower()
    if suffix in _LOSSY_FORMATS:
        raise ValueError(
            f"Format {suffix} tidak didukung untuk steganografi (lossy compression "
            "akan merusak data tersembunyi). Gunakan PNG atau BMP."
        )
    return p


def _open_rgb(path: Path) -> Image.Image:
    """Buka gambar dan pastikan mode RGB."""
    img = Image.open(path)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    elif img.mode == "RGBA":
        img = img.convert("RGB")
    return img


def get_capacity(image_path: str, bits_per_channel: int = 1) -> dict:
    """
    Hitung kapasitas maksimum pesan yang bisa disisipkan.

    Returns:
        dict dengan keys: width, height, channels, max_bytes, max_chars
    """
    p = _validate_image_path(image_path)
    img = _open_rgb(p)
    w, h = img.size
    channels = 3  # RGB
    total_bits = w * h * channels * bits_per_channel
    max_bytes = total_bits // 8 - _HEADER_SIZE
    return {
        "width": w,
        "height": h,
        "channels": channels,
        "bits_per_channel": bits_per_channel,
        "max_bytes": max_bytes,
        "max_chars": max_bytes,   # UTF-8 ASCII = 1 char/byte worst case
    }


# ──────────────────────────────────────────────
# 2.  Core LSB embed / extract (bytes level)
# ──────────────────────────────────────────────

def _bits_from_bytes(data: bytes) -> list:
    """Ubah bytes → list bit integer (MSB first)."""
    bits = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def _bytes_from_bits(bits: list) -> bytes:
    """Ubah list bit → bytes."""
    result = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            chunk += [0] * (8 - len(chunk))
        byte = 0
        for bit in chunk:
            byte = (byte << 1) | bit
        result.append(byte)
    return bytes(result)


def _embed_bits(img: Image.Image, bits: list,
                bits_per_channel: int = 1) -> Image.Image:
    """
    Sisipkan bit-list ke pixel gambar menggunakan LSB.
    Modifikasi in-place pada salinan pixels.
    """
    w, h = img.size
    pixels = [img.getpixel((x, y)) for y in range(h) for x in range(w)]
    flat = []
    for pixel in pixels:
        flat.extend(pixel[:3])   # R, G, B

    total_slots = len(flat) * bits_per_channel
    if len(bits) > total_slots:
        raise ValueError(
            f"Pesan terlalu besar! "
            f"Butuh {len(bits)} bit, tersedia {total_slots} bit."
        )

    mask = ~((1 << bits_per_channel) - 1) & 0xFF

    bit_idx = 0
    for i in range(len(flat)):
        if bit_idx >= len(bits):
            break
        chunk = bits[bit_idx: bit_idx + bits_per_channel]
        # Pad ke bits_per_channel jika kurang
        while len(chunk) < bits_per_channel:
            chunk.append(0)
        value = 0
        for b in chunk:
            value = (value << 1) | b
        flat[i] = (flat[i] & mask) | value
        bit_idx += bits_per_channel

    # Susun kembali jadi tuples RGB
    new_pixels = [
        (flat[i], flat[i+1], flat[i+2])
        for i in range(0, len(flat) - 2, 3)
    ]
    out = img.copy()
    out.putdata(new_pixels)
    return out


def _extract_bits(img: Image.Image, n_bits: int,
                  bits_per_channel: int = 1) -> list:
    """Ekstrak sejumlah n_bits dari LSB pixel gambar."""
    w, h = img.size
    pixels = [img.getpixel((x, y)) for y in range(h) for x in range(w)]
    flat = []
    for pixel in pixels:
        flat.extend(pixel[:3])

    bits = []
    bit_mask = (1 << bits_per_channel) - 1
    for value in flat:
        extracted = value & bit_mask
        for shift in range(bits_per_channel - 1, -1, -1):
            bits.append((extracted >> shift) & 1)
            if len(bits) >= n_bits:
                return bits
    return bits


# ──────────────────────────────────────────────
# 3.  Public API — bytes level
# ──────────────────────────────────────────────

def embed_bytes(image_path: str, payload: bytes,
                output_path: str, bits_per_channel: int = 1) -> dict:
    """
    Sisipkan payload bytes ke dalam gambar.

    Args:
        image_path      : path gambar sumber (PNG/BMP/TIFF)
        payload         : data bytes yang akan disembunyikan
        output_path     : path gambar output
        bits_per_channel: 1 (tidak terlihat) atau 2 (kapasitas 2x, sedikit terlihat)

    Returns:
        stats dict      : {image_size, payload_size, capacity, output_path}
    """
    p = _validate_image_path(image_path)
    img = _open_rgb(p)

    # Buat header
    header = struct.pack("<IQ", _MAGIC, len(payload))  # 4+8 bytes
    full_payload = header[:4] + struct.pack("<I", len(payload)) + payload

    bits = _bits_from_bytes(full_payload)
    out_img = _embed_bits(img, bits, bits_per_channel)

    out_path = Path(output_path)
    out_img.save(str(out_path), format="PNG")   # selalu simpan sebagai PNG

    cap = get_capacity(image_path, bits_per_channel)
    return {
        "image_size": f"{img.width}x{img.height}",
        "payload_size_bytes": len(payload),
        "capacity_bytes": cap["max_bytes"],
        "usage_percent": round(len(payload) / cap["max_bytes"] * 100, 2),
        "output_path": str(out_path),
        "bits_per_channel": bits_per_channel,
    }


def extract_bytes(image_path: str, bits_per_channel: int = 1) -> bytes:
    """
    Ekstrak payload bytes dari gambar yang sudah disisipi.

    Args:
        image_path      : path gambar (harus PNG/BMP/TIFF dengan data tersembunyi)
        bits_per_channel: harus sama dengan nilai saat embed

    Returns:
        payload bytes
    """
    p = _validate_image_path(image_path)
    img = _open_rgb(p)

    # Baca header dulu: 8 byte = 64 bit
    header_bits = _HEADER_SIZE * 8
    bits = _extract_bits(img, header_bits, bits_per_channel)
    header_bytes = _bytes_from_bits(bits)

    magic, length = struct.unpack("<II", header_bytes)
    if magic != _MAGIC:
        raise ValueError(
            "Tidak ditemukan data tersembunyi di gambar ini, "
            "atau gambar telah dimodifikasi/dikompresi."
        )

    # Baca payload
    total_bits = (length + _HEADER_SIZE) * 8
    all_bits = _extract_bits(img, total_bits, bits_per_channel)
    all_bytes = _bytes_from_bits(all_bits)
    payload = all_bytes[_HEADER_SIZE: _HEADER_SIZE + length]
    return payload


# ──────────────────────────────────────────────
# 4.  Public API — text level (untuk Flask)
# ──────────────────────────────────────────────

def embed_message(image_path: str, message: str,
                  output_path: str, bits_per_channel: int = 1) -> dict:
    """
    Sisipkan pesan teks rahasia ke dalam gambar.

    Args:
        image_path      : path gambar sumber
        message         : pesan string (akan di-encode UTF-8)
        output_path     : path gambar output
        bits_per_channel: 1 (default) atau 2

    Returns:
        stats dict
    """
    if not message:
        raise ValueError("Pesan tidak boleh kosong.")

    payload = message.encode("utf-8")
    stats = embed_bytes(image_path, payload, output_path, bits_per_channel)
    stats["message_length_chars"] = len(message)
    return stats


def extract_message(image_path: str, bits_per_channel: int = 1) -> str:
    """
    Ekstrak pesan teks tersembunyi dari gambar.

    Returns:
        pesan string (UTF-8)
    """
    payload = extract_bytes(image_path, bits_per_channel)
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(
            "Data yang diekstrak bukan teks UTF-8 yang valid. "
            "Pastikan gambar mengandung pesan teks."
        )


# ──────────────────────────────────────────────
# 5.  Helper untuk Flask routes
# ──────────────────────────────────────────────

def is_supported_image(filename: str) -> bool:
    """Cek apakah ekstensi file didukung untuk steganografi."""
    return Path(filename).suffix.lower() in _SUPPORTED_FORMATS


def get_image_info(image_path: str) -> dict:
    """
    Ambil info gambar: dimensi, mode, kapasitas penyimpanan.
    Berguna untuk ditampilkan di halaman hasil web.
    """
    p = Path(image_path)
    img = Image.open(p)
    cap1 = get_capacity(image_path, bits_per_channel=1)
    cap2 = get_capacity(image_path, bits_per_channel=2)
    return {
        "filename": p.name,
        "width": img.width,
        "height": img.height,
        "mode": img.mode,
        "format": img.format,
        "capacity_1bit_bytes": cap1["max_bytes"],
        "capacity_2bit_bytes": cap2["max_bytes"],
        "capacity_1bit_kb": round(cap1["max_bytes"] / 1024, 2),
        "capacity_2bit_kb": round(cap2["max_bytes"] / 1024, 2),
    }


# ──────────────────────────────────────────────
# Quick self-test (python steganografi.py)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile, os

    # Buat gambar uji sederhana (100×100 merah)
    test_img_path = tempfile.mktemp(suffix=".png")
    test_out_path = tempfile.mktemp(suffix=".png")

    img = Image.new("RGB", (200, 200), color=(180, 50, 60))
    img.save(test_img_path)

    secret = "Halo MEDIA_CORE! Ini pesan rahasia 🔐"
    print(f"Pesan asli  : {secret}")

    stats = embed_message(test_img_path, secret, test_out_path)
    print(f"Embed stats : {stats}")

    recovered = extract_message(test_out_path)
    print(f"Pesan keluar: {recovered}")
    assert recovered == secret, "EKSTRAK GAGAL!"
    print("Test steganografi: LULUS ✓")

    # Bersihkan
    os.remove(test_img_path)
    os.remove(test_out_path)