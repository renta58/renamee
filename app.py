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

# Inisialisasi OCR reader
reader = easyocr.Reader(['id', 'en'])

# File log
LOG_PATH = "rename_log.csv"

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

mode = st.radio("Pilih Mode:", ["📁 Scan Folder", "📤 Upload Gambar Satuan"])

# === Mode 1: Scan Folder ===
if mode == "📁 Scan Folder":
    folder_path = st.text_input("Masukkan path folder berisi gambar:")

    if st.button("🚀 Mulai Proses Folder"):
        if not os.path.exists(folder_path):
            st.error("❌ Folder tidak ditemukan.")
        else:
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            renamed = 0
            failed = []

            for file in files:
                try:
                    path = os.path.join(folder_path, file)
                    img = Image.open(path)
                    kode = detect_full_kode(img)

                    if kode:
                        ext = os.path.splitext(file)[1]
                        new_name = f"Hasil_{kode}_beres{ext}"
                        new_path = os.path.join(folder_path, new_name)

                        counter = 1
                        while os.path.exists(new_path):
                            new_name = f"Hasil_{kode}_{counter}_beres{ext}"
                            new_path = os.path.join(folder_path, new_name)
                            counter += 1

                        os.rename(path, new_path)
                        log_rename(file, new_name)
                        renamed += 1
                    else:
                        failed.append(file)
                except Exception as e:
                    failed.append(file)

            st.success(f"✅ {renamed} file berhasil di-rename.")
            if failed:
                st.warning(f"{len(failed)} file gagal diproses:")
                st.code("\n".join(failed))

# === Mode 2: Upload Gambar Tunggal ===
elif mode == "📤 Upload Gambar Satuan":
    uploaded_file = st.file_uploader("Upload satu gambar", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Gambar yang Diupload", use_column_width=True)

        kode = detect_full_kode(img)
        if kode:
            ext = os.path.splitext(uploaded_file.name)[1]
            new_name = f"Hasil_{kode}_beres{ext}"

            # Simpan file hasil rename
            with open(new_name, "wb") as f:
                f.write(uploaded_file.read())

            log_rename(uploaded_file.name, new_name)
            st.success(f"✅ Gambar berhasil dinamai ulang: `{new_name}`")

            with open(new_name, "rb") as f:
                st.download_button("⬇️ Unduh Gambar", f, file_name=new_name)

        else:
            st.error("❌ Kode wilayah tidak ditemukan dalam gambar.")
