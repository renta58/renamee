import streamlit as st
import easyocr
import os
import re
from PIL import Image
import numpy as np

# Folder untuk upload dan hasil rename
UPLOAD_DIR = "upload_images"
RENAMED_DIR = "renamed_images"

# Fungsi memastikan direktori aman dibuat
def safe_mkdir(path):
    if os.path.isfile(path):
        os.remove(path)
    if not os.path.exists(path):
        os.makedirs(path)

# Buat direktori upload dan renamed (pastikan bukan file biasa)
safe_mkdir(UPLOAD_DIR)
safe_mkdir(RENAMED_DIR)

# Inisialisasi OCR
reader = easyocr.Reader(['en'], gpu=False)

# Fungsi deteksi kode wilayah
def detect_kode(image):
    for angle in [0, 90, 180, 270]:
        rotated = image.rotate(angle, expand=True)
        img_np = np.array(rotated)
        results = reader.readtext(img_np)
        for _, text, _ in results:
            match = re.search(r'1209\d+', text)
            if match:
                return match.group(0)
    return None

# Simpan gambar ke folder hasil rename
def save_image(img, filename):
    path = os.path.join(RENAMED_DIR, filename)
    img.save(path)

# Tampilan Streamlit
st.title("📸 Rename Otomatis Gambar dengan Kode Wilayah (OCR)")
st.write("Upload gambar, sistem akan membaca kode wilayah dan rename otomatis.")

uploaded_files = st.file_uploader("Unggah Gambar (jpg/jpeg/png)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    renamed = []
    gagal = []

    for file in uploaded_files:
        img = Image.open(file).convert("RGB")
        kode = detect_kode(img)
        if kode:
            new_name = f"Hasil_{kode}_beres.jpg"
            save_image(img, new_name)
            renamed.append(new_name)
        else:
            gagal.append(file.name)

    if renamed:
        st.success(f"{len(renamed)} gambar berhasil di-rename.")
        for name in renamed:
            with open(os.path.join(RENAMED_DIR, name), "rb") as f:
                st.download_button(f"Unduh {name}", data=f, file_name=name, mime="image/jpeg")

    if gagal:
        st.warning(f"{len(gagal)} gambar gagal dikenali kodenya:")
        for g in gagal:
            st.write(f"- {g}")
