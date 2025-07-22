import streamlit as st
import easyocr
import os
import re
from PIL import Image
import numpy as np
from io import BytesIO
import shutil

# Folder untuk upload dan hasil rename
UPLOAD_DIR = "upload_images"
RENAMED_DIR = "renamed_images"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

# Inisialisasi EasyOCR
reader = easyocr.Reader(['en'], gpu=False)

# Fungsi deteksi kode wilayah menggunakan rotasi sudut
def detect_full_kode(image):
    for angle in [0, 90, 180, 270]:
        rotated = image.rotate(angle, expand=True)
        img_np = np.array(rotated)
        results = reader.readtext(img_np)
        for (bbox, text, prob) in results:
            match = re.search(r'1209\d+', text)
            if match:
                return match.group(0)
    return None

# Fungsi untuk menyimpan file hasil rename
def save_image(img, filename):
    img.save(os.path.join(RENAMED_DIR, filename))

# Judul aplikasi
st.title("📸 Rename Gambar Otomatis dengan OCR")
st.write("Unggah gambar, dan aplikasi ini akan otomatis membaca kode wilayah dan mengganti nama file.")

# Upload gambar
uploaded_files = st.file_uploader("Unggah gambar (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    renamed_files = []
    failed_files = []

    for file in uploaded_files:
        img = Image.open(file).convert("RGB")
        kode = detect_full_kode(img)
        if kode:
            new_name = f"Hasil_{kode}_beres.jpg"
            save_image(img, new_name)
            renamed_files.append(new_name)
        else:
            failed_files.append(file.name)

    st.success(f"✅ {len(renamed_files)} gambar berhasil di-rename.")
    if failed_files:
        st.warning(f"⚠️ Gagal membaca kode wilayah dari {len(failed_files)} gambar:")
        for f in failed_files:
            st.write(f"- {f}")

    if renamed_files:
        st.subheader("📥 Unduh Gambar yang Sudah Di-Rename")
        for file in renamed_files:
            with open(os.path.join(RENAMED_DIR, file), "rb") as f:
                st.download_button(label=f"Unduh {file}", data=f, file_name=file, mime="image/jpeg")

    # Bersihkan folder upload
    for file in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, file))
