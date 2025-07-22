import streamlit as st
import os
import shutil
import easyocr
from PIL import Image

reader = easyocr.Reader(['en'])

UPLOAD_DIR = "uploaded_images"
RENAMED_DIR = "renamed_images"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

st.set_page_config(page_title="OCR Rename App", layout="wide")
st.title("📸 Rename Otomatis Gambar Berdasarkan Kode OCR")

uploaded_files = st.file_uploader("Unggah gambar", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

if uploaded_files:
    st.success(f"{len(uploaded_files)} gambar berhasil diunggah.")
    for file in uploaded_files:
        with open(os.path.join(UPLOAD_DIR, file.name), "wb") as f:
            f.write(file.getbuffer())

if st.button("🔁 Jalankan Rename Otomatis"):
    renamed_count = 0
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        try:
            result = reader.readtext(file_path, detail=0)
            if result:
                kode = result[0].replace(" ", "").upper()
                new_name = f"Hasil_{kode}_beres.jpg"
                new_path = os.path.join(RENAMED_DIR, new_name)
                shutil.copy(file_path, new_path)
                renamed_count += 1
            else:
                st.warning(f"Tidak ada teks terbaca dari: {filename}")
        except Exception as e:
            st.error(f"Gagal rename {filename} | Error: {str(e)}")

    st.success(f"✅ Total berhasil di-rename: {renamed_count}")

if os.listdir(RENAMED_DIR):
    st.subheader("📁 Hasil Rename:")
    for file in os.listdir(RENAMED_DIR):
        st.image(os.path.join(RENAMED_DIR, file), width=250, caption=file)
