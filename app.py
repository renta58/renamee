import os
import streamlit as st
from PIL import Image
import pytesseract

# Direktori
UPLOAD_DIR = "uploaded_images"
RENAMED_DIR = "renamed_images"

# Periksa dan buat folder dengan aman
def safe_mkdir(directory):
    if os.path.exists(directory):
        if not os.path.isdir(directory):
            os.remove(directory)  # hapus file yang bentrok
            os.makedirs(directory)
    else:
        os.makedirs(directory)

safe_mkdir(UPLOAD_DIR)
safe_mkdir(RENAMED_DIR)

# Judul aplikasi
st.title("📷 OCR Rename App Sederhana")

# Upload gambar
uploaded_files = st.file_uploader("Unggah satu atau beberapa gambar", accept_multiple_files=True, type=["jpg", "png", "jpeg"])

if uploaded_files:
    for uploaded_file in uploaded_files:
        # Simpan sementara
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Jalankan OCR
        try:
            image = Image.open(file_path)
            ocr_result = pytesseract.image_to_string(image)

            # Ambil hasil 1 baris pertama yang non-kosong
            for line in ocr_result.split("\n"):
                clean_line = line.strip().replace(" ", "")
                if clean_line:
                    ocr_code = clean_line
                    break
            else:
                ocr_code = "NOCODE"

            # Buat nama baru
            new_name = f"Hasil_{ocr_code}_beres{os.path.splitext(uploaded_file.name)[1]}"
            new_path = os.path.join(RENAMED_DIR, new_name)
            os.rename(file_path, new_path)

            st.success(f"✔️ {uploaded_file.name} ➜ {new_name}")
            st.image(new_path, width=300)
        except Exception as e:
            st.error(f"❌ Gagal memproses {uploaded_file.name}: {e}")
