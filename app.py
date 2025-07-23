import os
import shutil
import sqlite3
import streamlit as st
from datetime import datetime
from PIL import Image
import easyocr

# Set halaman Streamlit
st.set_page_config(page_title="OCR Rename App", layout="centered")

# Inisialisasi OCR reader
reader = easyocr.Reader(['en'])

# Inisialisasi folder
UPLOAD_FOLDER = "uploads"
RENAMED_FOLDER = "renamed_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RENAMED_FOLDER, exist_ok=True)

# Inisialisasi database
def init_db():
    conn = sqlite3.connect("rename_history.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rename_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_filename TEXT,
        new_filename TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# Fungsi OCR dan Rename
def ocr_and_rename(file_path):
    result = reader.readtext(file_path, detail=0)
    joined_text = "_".join(result).replace(" ", "").replace("\n", "").replace("/", "_")
    
    # Ambil kode yang diawali dengan '1209'
    target_text = [t for t in joined_text.split("_") if t.startswith("1209")]
    if not target_text:
        return None
    
    kode = target_text[0]
    new_name = f"Hasil_{kode}_beres.png"
    new_path = os.path.join(RENAMED_FOLDER, new_name)

    # Tidak menambahkan angka jika file sudah ada, cukup timpa ulang
    shutil.copy(file_path, new_path)

    # Simpan ke database
    conn = sqlite3.connect("rename_history.db")
    c = conn.cursor()
    c.execute("INSERT INTO rename_history (original_filename, new_filename, timestamp) VALUES (?, ?, ?)",
              (os.path.basename(file_path), new_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    return new_name

# Judul Aplikasi
st.title("📄 OCR Rename App (No Login)")

# Upload File
uploaded_files = st.file_uploader("📤 Upload Gambar (PNG/JPG/JPEG)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    st.info("Proses dimulai... mohon tunggu sebentar.")
    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        renamed = ocr_and_rename(file_path)
        if renamed:
            st.success(f"✅ Berhasil di-rename: {renamed}")
        else:
            st.warning(f"⚠️ Tidak ditemukan kode yang dimulai dengan '1209' pada: {uploaded_file.name}")

# Tampilkan Riwayat Rename
st.subheader("📜 Riwayat Rename")
conn = sqlite3.connect("rename_history.db")
c = conn.cursor()
c.execute("SELECT original_filename, new_filename, timestamp FROM rename_history ORDER BY id DESC")
rows = c.fetchall()
conn.close()

if rows:
    for row in rows:
        st.write(f"🗂️ **{row[0]}** ➡️ **{row[1]}** ({row[2]})")
else:
    st.info("Belum ada file yang berhasil di-rename.")
