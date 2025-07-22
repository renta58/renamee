import streamlit as st
import easyocr
import os
import re
from PIL import Image
import shutil

# Buat folder untuk menyimpan hasil dan upload
os.makedirs("uploads", exist_ok=True)
os.makedirs("renamed", exist_ok=True)

# Inisialisasi pembaca OCR
reader = easyocr.Reader(['en'])

st.title("🔠 Rename Gambar Otomatis Berdasarkan Kode yang Mengandung '1209'")

uploaded_files = st.file_uploader("Upload gambar", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

def extract_1209_code(texts):
    # Ambil hanya bagian teks yang mengandung "1209" (case-insensitive)
    matches = []
    for t in texts:
        found = re.findall(r'\b\S*1209\S*\b', t, re.IGNORECASE)
        matches.extend(found)
    if matches:
        return "_".join(matches)
    else:
        return "TIDAK_TEMU_1209"

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = os.path.join("uploads", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            result = reader.readtext(file_path)
            all_text = [r[1] for r in result]

            # Filter hanya teks yang mengandung '1209'
            final_code = extract_1209_code(all_text)

            # Rename file berdasarkan hasil OCR
            ext = os.path.splitext(uploaded_file.name)[1]
            new_filename = f"Hasil_{final_code}_beres{ext}"
            new_path = os.path.join("renamed", new_filename)
            shutil.copy(file_path, new_path)

            st.success(f"✅ {uploaded_file.name} → {new_filename}")
            st.image(Image.open(file_path), caption=new_filename, width=250)

        except Exception as e:
            st.error(f"❌ Gagal memproses {uploaded_file.name}: {e}")

    # Tampilkan hasil download
    with st.expander("📁 Lihat & Unduh File Hasil Rename"):
        for filename in os.listdir("renamed"):
            file_path = os.path.join("renamed", filename)
            with open(file_path, "rb") as f:
                st.download_button(label=f"⬇️ Unduh {filename}", data=f, file_name=filename)
