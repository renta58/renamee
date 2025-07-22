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
import gdown

st.set_page_config(page_title="OCR Rename App", layout="wide")
st.title("\U0001F4C1 Rename File Otomatis dengan OCR")

reader = easyocr.Reader(['en'], gpu=False)

def preprocess(img):
    img = ImageOps.grayscale(img)
    img = img.resize((img.width * 2, img.height * 2))
    return img

def detect_full_kode(img):
    for angle in [0, 90, 180, 270]:
        rotated = img.rotate(angle, expand=True)
        try:
            text_list = reader.readtext(np.array(preprocess(rotated)), detail=0)
        except Exception as e:
            st.error(f"OCR gagal membaca gambar (rotasi {angle}): {e}")
            return None
        for text in text_list:
            match = re.search(r'1209\d{4}', text)
            if match:
                return match.group(0)
    return None

@st.cache_data

def compress_folder_to_zip(folder_path, output_path):
    try:
        with zipfile.ZipFile(output_path, 'w') as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        zipf.write(os.path.join(root, file), arcname=file)
        return output_path
    except Exception as e:
        st.error(f"Gagal membuat ZIP: {e}")
        return None

option = st.radio("Pilih metode input:", ["Upload banyak gambar", "Upload file .zip", "Link Google Drive"])

def process_images(temp_dir):
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
    return renamed, failed

if option == "Upload banyak gambar":
    uploaded_files = st.file_uploader("Upload beberapa gambar:", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
    if uploaded_files:
        temp_dir = tempfile.mkdtemp()
        for file in uploaded_files:
            with open(os.path.join(temp_dir, file.name), "wb") as f:
                f.write(file.read())

        if st.button("\U0001F504 Proses Rename Gambar"):
            renamed, failed = process_images(temp_dir)
            zip_path = os.path.join(temp_dir, "rename_result.zip")
            zip_result = compress_folder_to_zip(temp_dir, zip_path)
            if zip_result:
                with open(zip_result, "rb") as f:
                    st.download_button("\U0001F4E6 Download Hasil Rename (ZIP)", f, file_name="rename_result.zip")
                st.success(f"Berhasil rename {renamed} file. Gagal: {len(failed)}")
                if failed:
                    st.write("Gagal rename:", failed)

elif option == "Upload file .zip":
    zip_file = st.file_uploader("Upload file ZIP yang berisi gambar:", type="zip")
    if zip_file:
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_file.read())
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        except Exception as e:
            st.error(f"Gagal mengekstrak ZIP: {e}")

        if st.button("\U0001F504 Proses Rename Gambar"):
            renamed, failed = process_images(temp_dir)
            zip_output = os.path.join(temp_dir, "rename_result.zip")
            zip_result = compress_folder_to_zip(temp_dir, zip_output)
            if zip_result:
                with open(zip_result, "rb") as f:
                    st.download_button("\U0001F4E6 Download Hasil Rename (ZIP)", f, file_name="rename_result.zip")
                st.success(f"Berhasil rename {renamed} file. Gagal: {len(failed)}")
                if failed:
                    st.write("Gagal rename:", failed)

elif option == "Link Google Drive":
    gdrive_link = st.text_input("Masukkan link file ZIP di Google Drive (format berbagi publik):")
    if gdrive_link:
        match = re.search(r"/d/(.*?)/", gdrive_link)
        if match:
            file_id = match.group(1)
        else:
            file_id = gdrive_link.split("id=")[-1]
        gdown_url = f"https://drive.google.com/uc?id={file_id}"

        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "downloaded.zip")
        try:
            gdown.download(gdown_url, output_path, quiet=False)
            with zipfile.ZipFile(output_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            if st.button("\U0001F504 Proses Rename Gambar"):
                renamed, failed = process_images(temp_dir)
                zip_output = os.path.join(temp_dir, "rename_result.zip")
                zip_result = compress_folder_to_zip(temp_dir, zip_output)
                if zip_result:
                    with open(zip_result, "rb") as f:
                        st.download_button("\U0001F4E6 Download Hasil Rename (ZIP)", f, file_name="rename_result.zip")
                    st.success(f"Berhasil rename {renamed} file. Gagal: {len(failed)}")
                    if failed:
                        st.write("Gagal rename:", failed)
        except Exception as e:
            st.error(f"Gagal mengunduh atau memproses file: {e}")
