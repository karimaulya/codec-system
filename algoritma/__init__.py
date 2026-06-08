"""
Exposes the two core modules so Flask (app.py) can import them cleanly:
    from algoritma import huffman, steganografi
    from algoritma.huffman import compress_file, decompress_file
    from algoritma.steganografi import embed_message, extract_message
"""
 
from algoritma import huffman       # noqa: F401  – Huffman compression / decompression
from algoritma import steganografi  # noqa: F401  – LSB image steganography
 
__all__ = ["huffman", "steganografi"]
__version__ = "1.0.0"