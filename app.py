import streamlit as st
import os
import shutil
import zipfile
import tempfile
import easyocr
import numpy as np
from PIL import Image, ImageOps
import datetime
import re

st.set_page_config(page_title="OCR Rename App", layout="wide")
st.title("📁 Rename File Otomatis dengan OCR")

# Inisialisasi EasyOCR
reader = easyocr.Reader(['en'], gpu=False)

# Fungsi untuk praproses gambar (opsional)
def preprocess(img):
    img = ImageOps.grayscale(img)
    img = img.resize((img.width * 2, img.height * 2))
    return img

# Fungsi untuk mendeteksi teks dengan berbagai rotasi
def detect_full_kode(img):
    for angle in [0, 90, 180, 270]:
        rotated = img.rotate(angle, expand=True)
        text_list = reader.readtext(np.array(preprocess(rotated)), detail=0)
        for text in text_list:
            match = re.search(r'1209\d{4}', text)
            if match:
                return match.group(0)
    return None

# Fungsi untuk simpan hasil zip
@st.cache_data
def compress_folder_to_zip(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w') as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    zipf.write(os.path.join(root, file), arcname=file)
    return output_path

# Pilihan input
option = st.radio("Pilih metode input:", ["Upload banyak gambar", "Upload file .zip"])

# Upload multiple images
if option == "Upload banyak gambar":
    uploaded_files = st.file_uploader("Upload beberapa gambar:", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
    if uploaded_files:
        temp_dir = tempfile.mkdtemp()
        for file in uploaded_files:
            with open(os.path.join(temp_dir, file.name), "wb") as f:
                f.write(file.read())

        if st.button("🔄 Proses Rename Gambar"):
            renamed = 0
            failed = []
            for file in os.listdir(temp_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    path = os.path.join(temp_dir, file)
                    try:
                        img = Image.open(path)
                        kode = detect_full_kode(img)
                        if kode:
                            ext = os.path.splitext(file)[1]
                            new_name = f"Hasil_{kode}_beres{ext}"
                            new_path = os.path.join(temp_dir, new_name)
                            counter = 1
                            while os.path.exists(new_path):
                                new_name = f"Hasil_{kode}_{counter}_beres{ext}"
                                new_path = os.path.join(temp_dir, new_name)
                                counter += 1
                            os.rename(path, new_path)
                            renamed += 1
                        else:
                            failed.append(file)
                    except Exception as e:
                        failed.append(f"{file} (error: {str(e)})")

            zip_path = os.path.join(temp_dir, "rename_result.zip")
            compress_folder_to_zip(temp_dir, zip_path)
            with open(zip_path, "rb") as f:
                st.download_button("📦 Download Hasil Rename (ZIP)", f, file_name="rename_result.zip")
            st.success(f"Berhasil rename {renamed} file. Gagal: {len(failed)}")
            if failed:
                st.write("Gagal rename:", failed)

# Upload ZIP file
elif option == "Upload file .zip":
    zip_file = st.file_uploader("Upload file ZIP yang berisi gambar:", type="zip")
    if zip_file:
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_file.read())
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        if st.button("🔄 Proses Rename Gambar"):
            renamed = 0
            failed = []
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        try:
                            path = os.path.join(root, file)
                            img = Image.open(path)
                            kode = detect_full_kode(img)
                            if kode:
                                ext = os.path.splitext(file)[1]
                                new_name = f"Hasil_{kode}_beres{ext}"
                                new_path = os.path.join(root, new_name)
                                counter = 1
                                while os.path.exists(new_path):
                                    new_name = f"Hasil_{kode}_{counter}_beres{ext}"
                                    new_path = os.path.join(root, new_name)
                                    counter += 1
                                os.rename(path, new_path)
                                renamed += 1
                            else:
                                failed.append(file)
                        except Exception as e:
                            failed.append(f"{file} (error: {str(e)})")

            zip_output = os.path.join(temp_dir, "rename_result.zip")
            with zipfile.ZipFile(zip_output, 'w') as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            zipf.write(os.path.join(root, file), arcname=file)

            with open(zip_output, "rb") as f:
                st.download_button("📦 Download Hasil Rename (ZIP)", f, file_name="rename_result.zip")
            st.success(f"Berhasil rename {renamed} file. Gagal: {len(failed)}")
            if failed:
                st.write("Gagal rename:", failed)
