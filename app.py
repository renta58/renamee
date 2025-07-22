import streamlit as st
import os
import easyocr
import re
import datetime
from PIL import Image
import numpy as np

# Inisialisasi EasyOCR Reader
reader = easyocr.Reader(['en'])

# Direktori upload dan rename
UPLOAD_DIR = "uploaded_images"
RENAMED_DIR = "renamed_images"

# Buat folder jika belum ada
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

# Fungsi mendeteksi kode dari gambar

def detect_full_kode(img):
    img_array = np.array(img)
    texts = reader.readtext(img_array, detail=0)
    combined_text = " ".join(texts)
    matches = re.findall(r"1209\d{3,}", combined_text)
    return max(matches, key=len) if matches else None

# Halaman login sederhana
if 'login' not in st.session_state:
    st.session_state.login = False
    st.session_state.username = ""

# Simulasi login multi-user
if not st.session_state.login:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username and password:
            st.session_state.login = True
            st.session_state.username = username
            st.success(f"Selamat datang, {username}!")
        else:
            st.error("Username dan password harus diisi.")
    st.stop()

# Halaman utama aplikasi
st.title("Aplikasi Rename Gambar Otomatis dengan OCR")

uploaded_files = st.file_uploader(
    "Unggah gambar (bisa lebih dari satu)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read()
        img = Image.open(uploaded_file)

        # Simpan file asli untuk sementara
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # Jalankan OCR
        detected_kode = detect_full_kode(img)

        if detected_kode:
            new_filename = f"Hasil_{detected_kode}_beres.jpg"
        else:
            new_filename = f"Hasil_TIDAK_TERBACA_{datetime.datetime.now().strftime('%H%M%S')}.jpg"

        # Simpan dengan nama baru
        renamed_path = os.path.join(RENAMED_DIR, new_filename)
        img.save(renamed_path)

        st.image(img, caption=f"Berhasil diganti: {new_filename}", use_column_width=True)
else:
    st.info("Silakan unggah gambar terlebih dahulu.")
