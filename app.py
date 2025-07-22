import streamlit as st
import os
import zipfile
import pandas as pd
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import easyocr
import re
import io
import shutil

# Inisialisasi OCR reader
reader = easyocr.Reader(['id', 'en'])

# File log
LOG_PATH = "rename_log.csv"
TEMP_FOLDER = "temp_upload"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Fungsi Preprocessing Gambar
def preprocess(img):
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img

# Fungsi Deteksi Kode: "1209xxxxx"
def detect_full_kode(img):
    ocr_results = []
    for angle in [0, 90, 180, 270]:
        rotated = img.rotate(angle, expand=True)
        processed = preprocess(rotated)
        img_array = np.array(processed)
        texts = reader.readtext(img_array, detail=0)
        ocr_results.extend(texts)

    combined_text = " ".join(ocr_results)
    matches = re.findall(r"1209\d{3,}", combined_text)
    return max(matches, key=len) if matches else None

# Fungsi simpan log
def log_rename(old_name, new_name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame([[old_name, new_name, now]], columns=["Old Name", "New Name", "Time"])
    if os.path.exists(LOG_PATH):
        old_log = pd.read_csv(LOG_PATH)
        log_df = pd.concat([old_log, new_row], ignore_index=True)
    else:
        log_df = new_row
    log_df.to_csv(LOG_PATH, index=False)

# ==============================
# STREAMLIT UI
# ==============================
st.set_page_config(page_title="OCR Rename App", layout="centered")
st.title("📄🔁 Auto Rename Gambar berdasarkan OCR")

# Tampilkan histori jika tersedia
if os.path.exists(LOG_PATH):
    st.subheader("🕓 Riwayat Rename Sebelumnya")
    log_df = pd.read_csv(LOG_PATH)
    st.dataframe(log_df)

    # Tombol unduh log CSV
    st.download_button("⬇️ Unduh Log (.csv)", log_df.to_csv(index=False), file_name="rename_log.csv")

    # Buat ZIP semua file hasil rename (jika ada)
    if len(log_df) > 0:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for new_file in log_df["New Name"]:
                if os.path.exists(new_file):
                    zf.write(new_file, arcname=os.path.basename(new_file))
        zip_buffer.seek(0)
        st.download_button("📦 Unduh Semua Gambar (ZIP)", zip_buffer, file_name="semua_rename.zip")

mode = st.radio("Pilih Mode:", ["📦 Upload ZIP", "📤 Upload Gambar Jamak"])

uploaded_files = []

if mode == "📦 Upload ZIP":
    uploaded_zip = st.file_uploader("Upload file ZIP berisi gambar", type=["zip"])
    if uploaded_zip is not None:
        with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
            zip_ref.extractall(TEMP_FOLDER)
        uploaded_files = [
            os.path.join(TEMP_FOLDER, f) for f in os.listdir(TEMP_FOLDER)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

elif mode == "📤 Upload Gambar Jamak":
    manual_files = st.file_uploader("Upload beberapa gambar", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    if manual_files:
        for img_file in manual_files:
            temp_path = os.path.join(TEMP_FOLDER, img_file.name)
            with open(temp_path, "wb") as f:
                f.write(img_file.read())
            uploaded_files.append(temp_path)

if uploaded_files:
    st.success(f"{len(uploaded_files)} gambar berhasil dimuat. Siap untuk diproses!")
    for file_path in uploaded_files:
        try:
            img = Image.open(file_path)
            kode = detect_full_kode(img)
            if kode:
                ext = os.path.splitext(file_path)[1]
                new_name = f"Hasil_{kode}_beres{ext}"
                folder = os.path.dirname(file_path)
                new_path = os.path.join(folder, new_name)
                counter = 1
                while os.path.exists(new_path):
                    new_name = f"Hasil_{kode}_{counter}_beres{ext}"
                    new_path = os.path.join(folder, new_name)
                    counter += 1
                os.rename(file_path, new_path)
                log_rename(os.path.basename(file_path), new_name)
            else:
                st.warning(f"❌ Kode tidak ditemukan dalam gambar: {os.path.basename(file_path)}")
        except Exception as e:
            st.error(f"⚠️ Gagal memproses gambar: {file_path}\n{e}")

    # ZIP hasil rename
    renamed_files = [f for f in os.listdir(TEMP_FOLDER) if f.lower().startswith("Hasil_")]
    if renamed_files:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for f in renamed_files:
                file_path = os.path.join(TEMP_FOLDER, f)
                zipf.write(file_path, arcname=f)
        zip_buffer.seek(0)
        st.download_button("⬇️ Unduh Semua Hasil Rename", zip_buffer, file_name="hasil_rename.zip")

    # Bersihkan folder sementara
    shutil.rmtree(TEMP_FOLDER)
    os.makedirs(TEMP_FOLDER, exist_ok=True)
else:
    st.info("Silakan upload gambar untuk diproses.")
