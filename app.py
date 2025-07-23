import os
import shutil
import sqlite3
import streamlit as st
from datetime import datetime
from PIL import Image
import easyocr

# 🚀 Konfigurasi awal
st.set_page_config(page_title="OCR Rename App", layout="centered")

# 📂 Folder upload dan output
UPLOAD_FOLDER = "uploads"
RENAMED_FOLDER = "renamed_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RENAMED_FOLDER, exist_ok=True)

# 🧠 Inisialisasi EasyOCR
reader = easyocr.Reader(['en'])

# 🗃️ Inisialisasi Database SQLite
def init_db():
    conn = sqlite3.connect("rename_history.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS rename_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT,
            new_filename TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 🔍 Fungsi OCR dan Rename
def ocr_and_rename(file_path):
    try:
        # Baca teks dari gambar
        result = reader.readtext(file_path, detail=0)
        joined_text = "_".join(result).replace(" ", "").replace("\n", "").replace("/", "_")
        
        # Hanya ambil kode yang dimulai dengan 1209
        kode_list = [t for t in joined_text.split("_") if t.startswith("1209") and len(t) <= 20]
        if not kode_list:
            return None  # Tidak ada kode yang cocok

        kode = kode_list[0]
        new_filename = f"Hasil_{kode}_beres.png"
        new_path = os.path.join(RENAMED_FOLDER, new_filename)

        # Salin file tanpa menambahkan (1), (2), dst. Timpa saja jika sudah ada
        shutil.copy(file_path, new_path)

        # Simpan data ke database
        conn = sqlite3.connect("rename_history.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO rename_history (original_filename, new_filename, timestamp)
            VALUES (?, ?, ?)
        """, (os.path.basename(file_path), new_filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

        return new_filename
    except Exception as e:
        return f"ERROR: {str(e)}"

# 🎯 Judul halaman
st.title("📄 OCR Rename App (Tanpa Login)")

# 📤 Upload file
uploaded_files = st.file_uploader("Upload gambar PNG/JPG/JPEG", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    st.info("🔄 Sedang diproses... Harap tunggu.")

    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

        # Simpan file sementara
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        renamed_filename = ocr_and_rename(file_path)

        if renamed_filename and not renamed_filename.startswith("ERROR"):
            st.success(f"✅ Berhasil di-rename: `{renamed_filename}`")
        elif renamed_filename is None:
            st.warning(f"⚠️ Tidak ditemukan kode yang dimulai dengan '1209' di `{uploaded_file.name}`")
        else:
            st.error(f"❌ Terjadi kesalahan pada `{uploaded_file.name}`: {renamed_filename}")

# 📜 Riwayat Rename
st.subheader("📑 Riwayat Rename")

conn = sqlite3.connect("rename_history.db")
c = conn.cursor()
c.execute("SELECT original_filename, new_filename, timestamp FROM rename_history ORDER BY id DESC LIMIT 100")
rows = c.fetchall()
conn.close()

if rows:
    for row in rows:
        st.write(f"🗂️ **{row[0]}** ➡️ **{row[1]}** ({row[2]})")
else:
    st.info("Belum ada file yang berhasil di-rename.")
