import streamlit as st
import os
import re
import shutil
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import easyocr
from io import BytesIO

reader = easyocr.Reader(['id', 'en'])

# Folder setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "upload_images")
RENAMED_DIR = os.path.join(BASE_DIR, "renamed_images")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

# Kompresi gambar
def compress_image(img, output_path, max_size=(1024, 1024), quality=70):
    img.thumbnail(max_size)
    img.save(output_path, format='JPEG', optimize=True, quality=quality)

# Preprocessing
def preprocess(img):
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img

# OCR dari 4 arah
def detect_full_kode(img):
    for angle in [0, 90, 180, 270]:
        rotated = img.rotate(angle, expand=True)
        processed = preprocess(rotated)
        texts = reader.readtext(np.array(processed), detail=0)
        result = " ".join(texts)
        matches = re.findall(r"1209\d{3,}", result)
        if matches:
            return max(matches, key=len)
    return None

# UI
st.set_page_config(page_title="OCR Rename App", layout="centered")
st.title("📸 Rename Gambar Otomatis")

uploaded_files = st.file_uploader("Upload gambar (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    renamed = []
    skipped = []

    for file in uploaded_files:
        file_bytes = BytesIO(file.read())
        try:
            img = Image.open(file_bytes).convert("RGB")
            temp_path = os.path.join(UPLOAD_DIR, file.name)
            compress_image(img, temp_path)

            img = Image.open(temp_path)
            kode = detect_full_kode(img)

            if kode:
                new_name = f"Hasil_{kode}_beres.jpg"
                target_path = os.path.join(RENAMED_DIR, new_name)

                # Hindari overwrite
                i = 1
                while os.path.exists(target_path):
                    new_name = f"Hasil_{kode}_{i}_beres.jpg"
                    target_path = os.path.join(RENAMED_DIR, new_name)
                    i += 1

                shutil.move(temp_path, target_path)
                renamed.append(new_name)
            else:
                skipped.append(file.name)

        except Exception as e:
            skipped.append(file.name)
            st.error(f"❌ Error saat proses {file.name}: {str(e)}")

    st.success(f"✅ Berhasil rename: {len(renamed)} file")
    if skipped:
        st.warning("❗ Gagal dibaca (mungkin tidak ada kode):")
        st.code("\n".join(skipped))

    if renamed:
        st.subheader("📥 Unduh hasil:")
        for fname in renamed:
            path = os.path.join(RENAMED_DIR, fname)
            with open(path, "rb") as f:
                st.download_button(f"Download {fname}", f, file_name=fname)

