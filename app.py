import streamlit as st
import os
import re
import shutil
import uuid
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import easyocr

# Inisialisasi EasyOCR
reader = easyocr.Reader(['id', 'en'])

# Konstanta Direktori Base
BASE_UPLOAD_DIR = "uploaded"
BASE_RENAMED_DIR = "renamed"

# Session unik per user
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

UPLOAD_DIR = os.path.join(BASE_UPLOAD_DIR, st.session_state.user_id)
RENAMED_DIR = os.path.join(BASE_RENAMED_DIR, st.session_state.user_id)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

# Kompresi gambar
def compress_image(input_path, output_path, max_size=(1024, 1024), quality=70):
    try:
        img = Image.open(input_path)
        img.thumbnail(max_size)
        img.save(output_path, optimize=True, quality=quality)
        return output_path
    except Exception as e:
        print(f"[ERROR] Kompresi gagal untuk {input_path}: {e}")
        return input_path

# Preprocessing gambar
def preprocess(img):
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img

# Deteksi kode wilayah dengan regex
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

# UI
st.set_page_config(page_title="OCR Rename App", layout="centered")
st.title("📸 Rename Gambar Otomatis dengan OCR (Per User)")

uploaded_files = st.file_uploader("Unggah gambar (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    renamed_count = 0
    skipped_files = []
    renamed_files = []

    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            compressed_path = os.path.join(UPLOAD_DIR, f"compressed_{uploaded_file.name}")
            used_path = compress_image(file_path, compressed_path)

            img = Image.open(used_path)
            kode = detect_full_kode(img)

            if kode and len(kode) >= 8:
                ext = os.path.splitext(uploaded_file.name)[1]
                base_name = f"Hasil_{kode}_beres{ext}"
                new_path = os.path.join(RENAMED_DIR, base_name)

                counter = 1
                while os.path.exists(new_path):
                    base_name = f"Hasil_{kode}_{counter}_beres{ext}"
                    new_path = os.path.join(RENAMED_DIR, base_name)
                    counter += 1

                shutil.move(file_path, new_path)
                renamed_files.append((base_name, new_path))
                renamed_count += 1
            else:
                skipped_files.append(uploaded_file.name)

        except Exception as e:
            skipped_files.append(uploaded_file.name)

        finally:
            if os.path.exists(compressed_path):
                try:
                    os.remove(compressed_path)
                except:
                    pass

    # Ringkasan
    st.success(f"✅ Total berhasil di-rename: {renamed_count}")
    if skipped_files:
        st.warning("⚠️ Gagal membaca kode dari file berikut:")
        st.code("\n".join(skipped_files))

    if renamed_files:
        st.subheader("📁 Unduh File yang Telah Diubah")
        for fname, fpath in renamed_files:
            with open(fpath, "rb") as f:
                st.download_button(f"⬇️ {fname}", f, file_name=fname)

# Reset Session
if st.button("🔄 Reset Aplikasi"):
    st.session_state.clear()
    st.experimental_rerun()

st.markdown("---")
st.markdown("📌 Aplikasi ini membaca kode wilayah dalam gambar dan mengganti namanya secara otomatis. Kode yang dikenali: 1209xxxxx.")
