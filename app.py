import streamlit as st
import os
import uuid
import easyocr
from PIL import Image
from datetime import datetime
from filelock import FileLock

# Konstanta Global
BASE_UPLOAD_DIR = "uploaded"
BASE_RENAMED_DIR = "renamed"

# Inisialisasi Folder Per User
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

UPLOAD_DIR = os.path.join(BASE_UPLOAD_DIR, st.session_state.user_id)
RENAMED_DIR = os.path.join(BASE_RENAMED_DIR, st.session_state.user_id)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

# Fungsi Deteksi Kode Wilayah (contoh logika dasar)
def detect_kode(file_path):
    reader = easyocr.Reader(['en'])
    results = reader.readtext(file_path)
    for (bbox, text, prob) in results:
        if "1209" in text:  # Misalnya kode wilayah selalu mengandung '1209'
            return text.strip()
    return "UNKNOWN"

# Fungsi Rename Otomatis
def process_and_rename(uploaded_files):
    renamed_files = []
    with FileLock("rename.lock"):
        for uploaded_file in uploaded_files:
            bytes_data = uploaded_file.read()
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(bytes_data)

            # Deteksi kode
            kode = detect_kode(file_path)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            new_filename = f"Hasil_{kode}_beres_{timestamp}.jpg"
            new_path = os.path.join(RENAMED_DIR, new_filename)

            try:
                img = Image.open(file_path)
                img.save(new_path)
                renamed_files.append((new_filename, new_path))
            except Exception as e:
                st.error(f"Gagal memproses file {uploaded_file.name}: {e}")
    return renamed_files

# Antarmuka Streamlit
st.set_page_config(page_title="OCR Rename Otomatis", layout="wide")
st.title("🧠 OCR Rename Otomatis dengan Kode Wilayah")

uploaded_files = st.file_uploader("Upload gambar", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Memproses file..."):
        renamed_files = process_and_rename(uploaded_files)

    st.success(f"Berhasil memproses {len(renamed_files)} file!")

    for filename, path in renamed_files:
        st.image(path, caption=filename, use_column_width=True)
        st.write(f"📂 Diunduh: [{filename}](/{path})")

# Tombol reset session
if st.button("🔄 Reset Aplikasi"):
    st.session_state.clear()
    st.experimental_rerun()
