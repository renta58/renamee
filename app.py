import streamlit as st
import os
import re
import uuid
import shutil
import zipfile
import numpy as np
import requests
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
import easyocr

# Inisialisasi OCR
reader = easyocr.Reader(['id', 'en'])

# Buat session user unik
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

# Buat direktori upload dan rename per user
UPLOAD_DIR = os.path.join("uploaded", st.session_state.user_id)
RENAMED_DIR = os.path.join("renamed", st.session_state.user_id)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

# Fungsi kompresi

def compress_image(input_path, output_path, max_size=(1024, 1024), quality=70):
    try:
        img = Image.open(input_path)
        img.thumbnail(max_size)
        img.save(output_path, optimize=True, quality=quality)
        return output_path
    except:
        return input_path

# Preprocessing gambar

def preprocess(img):
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img

# Deteksi kode wilayah (regex 1209xxxxx)

def detect_kode(img):
    ocr_results = []
    for angle in [0, 90, 180, 270]:
        rotated = img.rotate(angle, expand=True)
        processed = preprocess(rotated)
        img_array = np.array(processed)
        texts = reader.readtext(img_array, detail=0)
        ocr_results.extend(texts)
    combined = " ".join(ocr_results)
    matches = re.findall(r"1209\\d{3,}", combined)
    return max(matches, key=len) if matches else None

# Proses file: rename dan pindah

def process_file(file_path, original_name):
    compressed_path = os.path.join(UPLOAD_DIR, f"compressed_{original_name}")
    used_path = compress_image(file_path, compressed_path)
    try:
        img = Image.open(used_path)
        kode = detect_kode(img)
        if kode:
            ext = os.path.splitext(original_name)[1]
            new_name = f"Hasil_{kode}_beres{ext}"
            target_path = os.path.join(RENAMED_DIR, new_name)
            counter = 1
            while os.path.exists(target_path):
                new_name = f"Hasil_{kode}_{counter}_beres{ext}"
                target_path = os.path.join(RENAMED_DIR, new_name)
                counter += 1
            shutil.move(file_path, target_path)
            return new_name, target_path
    except:
        pass
    return None, None

# UI utama
st.set_page_config(page_title="OCR Rename App", layout="centered")
st.title("📸 Rename Gambar Otomatis dengan OCR (Multi-Source)")

uploaded_files = st.file_uploader("Unggah gambar atau file ZIP:", type=["jpg", "jpeg", "png", "zip"], accept_multiple_files=True)
gdrive_url = st.text_input("Atau masukkan link Google Drive (direct public):")

if uploaded_files or gdrive_url:
    st.session_state.to_process = []

    # Proses file dari uploader
    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if uploaded_file.name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(UPLOAD_DIR)
            except:
                st.warning(f"Gagal ekstrak ZIP: {uploaded_file.name}")
        else:
            st.session_state.to_process.append((file_path, uploaded_file.name))

    # Proses dari Google Drive
    if gdrive_url.strip():
        try:
            r = requests.get(gdrive_url.strip())
            if r.status_code == 200:
                filename = gdrive_url.split("/")[-1] + ".jpg"
                gdrive_path = os.path.join(UPLOAD_DIR, filename)
                with open(gdrive_path, "wb") as f:
                    f.write(r.content)
                st.session_state.to_process.append((gdrive_path, filename))
            else:
                st.error("Gagal mengunduh dari link. Pastikan file bisa diakses publik.")
        except:
            st.error("Terjadi kesalahan saat mengambil file dari Google Drive.")

    if st.button("🔁 Lakukan Proses Rename"):
        renamed_files = []
        skipped = []

        for root, _, files in os.walk(UPLOAD_DIR):
            for fname in files:
                if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                    fpath = os.path.join(root, fname)
                    new_name, new_path = process_file(fpath, fname)
                    if new_path:
                        renamed_files.append((new_name, new_path))
                    else:
                        skipped.append(fname)

        # Ringkasan hasil
        st.success(f"✅ Total berhasil di-rename: {len(renamed_files)}")
        if skipped:
            st.warning(f"⚠️ Gagal dibaca dari: {len(skipped)} file")
            st.code("\n".join(skipped))

        # Unduhan hasil satu per satu
        if renamed_files:
            st.subheader("📁 Unduh File Rename")
            for fname, fpath in renamed_files:
                with open(fpath, "rb") as f:
                    st.download_button(f"⬇️ {fname}", f, file_name=fname)

            # Unduhan ZIP seluruh hasil
            zip_output = f"renamed/{st.session_state.user_id}.zip"
            with zipfile.ZipFile(zip_output, "w") as zipf:
                for fname, fpath in renamed_files:
                    zipf.write(fpath, arcname=fname)
            with open(zip_output, "rb") as f:
                st.download_button("📦 Unduh Semua (ZIP)", f, file_name="hasil_rename.zip")

st.markdown("---")
st.markdown("📌 Aplikasi mendukung unggahan gambar, ZIP folder, dan link Google Drive publik.")
