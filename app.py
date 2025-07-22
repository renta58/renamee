import os
import shutil
import streamlit as st
import easyocr
from PIL import Image

# Direktori penyimpanan
UPLOAD_DIR = "uploaded"
RENAMED_DIR = "renamed"

# Membuat folder jika belum ada
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

# Inisialisasi pembaca OCR
reader = easyocr.Reader(['en'])

# Judul App
st.title("📸 Rename Otomatis Gambar Berdasarkan Kode OCR")

# Upload file gambar
uploaded_files = st.file_uploader("Unggah satu atau lebih gambar", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    st.write("📂 Hasil Proses Rename:")

    for uploaded_file in uploaded_files:
        # Simpan file ke folder upload
        original_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(original_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Buka gambar dan lakukan OCR
        try:
            image = Image.open(original_path).convert("RGB")
            result = reader.readtext(original_path)

            # Ambil kode terdeteksi (teks pertama saja)
            if result:
                kode = result[0][1].replace(" ", "_")  # Hilangkan spasi
                # Format nama baru
                new_filename = f"Hasil_{kode}_beres{os.path.splitext(uploaded_file.name)[1]}"
                new_path = os.path.join(RENAMED_DIR, new_filename)
                shutil.copy(original_path, new_path)

                st.success(f"✅ {uploaded_file.name} → {new_filename}")
            else:
                st.warning(f"⚠️ Gagal deteksi teks dari {uploaded_file.name}")

        except Exception as e:
            st.error(f"❌ Gagal memproses {uploaded_file.name}: {e}")

# Tombol download massal (opsional)
if os.listdir(RENAMED_DIR):
    with st.expander("📥 Download semua file hasil rename"):
        for filename in os.listdir(RENAMED_DIR):
            with open(os.path.join(RENAMED_DIR, filename), "rb") as f:
                st.download_button(f"Download {filename}", f, file_name=filename)
