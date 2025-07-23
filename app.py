import streamlit as st
import easyocr
import os
import zipfile
import tempfile
import shutil
import re
from datetime import datetime
from PIL import Image
from io import BytesIO

# Inisialisasi EasyOCR sekali
reader = easyocr.Reader(['en'], gpu=False)

# Buat folder sesi sementara untuk setiap user
TEMP_DIR = "temp_sessions"
os.makedirs(TEMP_DIR, exist_ok=True)

# Fungsi membuat nama hasil
def generate_new_filename(text_detected):
    match = re.search(r'\d{3,}', text_detected)
    if match:
        return f"Hasil_{match.group(0)}_beres"
    return None

# Fungsi untuk membaca gambar dengan OCR
def extract_text(image_path):
    try:
        result = reader.readtext(image_path, detail=0)
        return ' '.join(result)
    except Exception as e:
        return ""

# Fungsi rename file
def process_and_rename_images(image_files, session_dir):
    renamed_files = []
    failed_files = []
    for file in image_files:
        img_path = os.path.join(session_dir, file.name)
        with open(img_path, "wb") as f:
            f.write(file.read())
        text = extract_text(img_path)
        new_name = generate_new_filename(text)
        if new_name:
            new_path = os.path.join(session_dir, new_name + os.path.splitext(file.name)[1])
            os.rename(img_path, new_path)
            renamed_files.append(new_path)
        else:
            failed_files.append(file.name)
    return renamed_files, failed_files

# Fungsi ekstrak ZIP
def handle_zip_upload(zip_file, session_dir):
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        image_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                if ext in [".jpg", ".jpeg", ".png"]:
                    dest_path = os.path.join(session_dir, file)
                    shutil.copy(path, dest_path)
                    image_files.append(dest_path)
        return image_files

# Fungsi ZIP hasil

def zip_renamed_files(renamed_paths):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for path in renamed_paths:
            zipf.write(path, arcname=os.path.basename(path))
    zip_buffer.seek(0)
    return zip_buffer

# STREAMLIT APP
st.set_page_config(page_title="OCR Rename App", layout="centered")
st.title("📸 Rename Otomatis Gambar Berdasarkan Teks (EasyOCR)")

# Buat session folder unik
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")

session_dir = os.path.join(TEMP_DIR, st.session_state.session_id)
os.makedirs(session_dir, exist_ok=True)

uploaded_files = st.file_uploader("Upload gambar (jpg/jpeg/png) atau ZIP:", type=["jpg", "jpeg", "png", "zip"], accept_multiple_files=True)

st.markdown("Atau masukkan link Google Drive (direct public):")
gdrive_link = st.text_input(" ")

# Tombol proses manual
if st.button("🚀 Lakukan Proses Rename"):
    all_image_paths = []
    failed_total = []

    # Tangani upload
    if uploaded_files:
        for file in uploaded_files:
            if file.name.lower().endswith(".zip"):
                extracted = handle_zip_upload(file, session_dir)
                all_image_paths.extend(extracted)
            else:
                file_path = os.path.join(session_dir, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.read())
                all_image_paths.append(file_path)

    # Jalankan OCR dan rename
    renamed_paths = []
    failed_files = []
    for path in all_image_paths:
        text = extract_text(path)
        new_name = generate_new_filename(text)
        if new_name:
            new_path = os.path.join(session_dir, new_name + os.path.splitext(path)[1])
            os.rename(path, new_path)
            renamed_paths.append(new_path)
        else:
            failed_files.append(os.path.basename(path))

    # Tampilkan hasil
    st.success(f"Total berhasil di-rename: {len(renamed_paths)}")
    if failed_files:
        st.warning(f"Gagal dibaca dari: {len(failed_files)} file")
        for f in failed_files:
            st.code(f)

    # Unduh hasil satuan
    for renamed in renamed_paths:
        with open(renamed, "rb") as f:
            btn = st.download_button(
                label=f"⬇️ Unduh: {os.path.basename(renamed)}",
                data=f,
                file_name=os.path.basename(renamed)
            )

    # Unduh semua ZIP
    if renamed_paths:
        zip_file = zip_renamed_files(renamed_paths)
        st.download_button("📦 Unduh Semua Hasil (ZIP)", data=zip_file, file_name="hasil_rename.zip")

st.caption("\n© 2025 - App by Renta with EasyOCR + Streamlit")
