import os
import shutil
import streamlit as st
import easyocr
from PIL import Image
import re

# === PENGATURAN FOLDER ===
UPLOAD_DIR = "uploaded"
RENAMED_DIR = "renamed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

# === INISIALISASI OCR ===
reader = easyocr.Reader(['en'])

# === JUDUL APLIKASI ===
st.title("🔍 Rename Otomatis Gambar Berdasarkan Kode yang Mengandung '1209'")

# === UNGGAH GAMBAR ===
uploaded_files = st.file_uploader("Unggah satu atau lebih gambar", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# === FUNGSI EKSTRAK KODE YANG MENGANDUNG '1209' ===
def extract_kode_1209(texts):
    gabungan = " ".join(texts)
    # Ambil semua kata yang mengandung '1209' (case-insensitive)
    kode_terdeteksi = re.findall(r'\b\S*1209\S*\b', gabungan, re.IGNORECASE)
    return "_".join(kode_terdeteksi) if kode_terdeteksi else "TIDAK_TEMU_1209"

# === PROSES SETIAP FILE ===
if uploaded_files:
    st.write("📂 Hasil Rename:")

    for uploaded_file in uploaded_files:
        original_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(original_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            # Jalankan OCR
            result = reader.readtext(original_path)
            all_texts = [r[1] for r in result]

            if all_texts:
                # Ambil hanya kode yang mengandung '1209'
                kode_1209 = extract_kode_1209(all_texts)
                ext = os.path.splitext(uploaded_file.name)[1]
                new_filename = f"Hasil_{kode_1209}_beres{ext}"
                new_path = os.path.join(RENAMED_DIR, new_filename)

                shutil.copy(original_path, new_path)
                st.success(f"✅ {uploaded_file.name} → {new_filename}")
            else:
                st.warning(f"⚠️ Tidak ada teks terbaca di {uploaded_file.name}")

        except Exception as e:
            st.error(f"❌ Gagal memproses {uploaded_file.name}: {e}")

# === TOMBOL DOWNLOAD HASIL ===
if os.listdir(RENAMED_DIR):
    with st.expander("📥 Download file hasil rename"):
        for filename in os.listdir(RENAMED_DIR):
            with open(os.path.join(RENAMED_DIR, filename), "rb") as f:
                st.download_button(f"Download {filename}", f, file_name=filename)
