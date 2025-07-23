import streamlit as st
import os
import re
import uuid
import shutil
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import easyocr
from datetime import datetime
from filelock import FileLock

# Inisialisasi OCR Reader
reader = easyocr.Reader(['id', 'en'])

# Konstanta Direktori Global
BASE_UPLOAD_DIR = "uploaded"
BASE_RENAMED_DIR = "renamed"

# Buat Session User Unik
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

UPLOAD_DIR = os.path.join(BASE_UPLOAD_DIR, st.session_state.user_id)
RENAMED_DIR = os.path.join(BASE_RENAMED_DIR, st.session_state.user_id)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RENAMED_DIR, exist_ok=True)

# Fungsi Kompresi
def compress_image(input_path, output_path, max_size=(1024, 1024), quality=70):
    try:
        img = Image.open(input_path)
        img.thumbnail(max_size)
        img.save(output_path, optimize=True, quality=quality)
        return output_path
    except Exception as e:
        print(f"[ERROR] Kompresi gagal: {e}")
        return input_path

# Fungsi Preprocessing Gambar
def preprocess(img):
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img

# Deteksi Kode dari Gambar
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

# Judul
st.set_page_config(page_title="OCR Rename Otomatis", layout="centered")
st.title("📸 Rename Gambar Otomatis per User dengan OCR")

uploaded_files = st.file_uploader("Unggah gambar (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    renamed_count = 0
    skipped_files = []
    renamed_files = []

    with FileLock("rename.lock"):
        for uploaded_file in uploaded_files:
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            compressed_path = os.path.join(UPLOAD_DIR, f"compressed_{uploaded_file.name}")
            used_path = compress_image(file_path, compressed_path)

            try:
                img = Image.open(used_path)
                kode = detect_full_kode(img)

                if kode and len(kode) >= 8:
                    ext = os.path.splitext(uploaded_file.name)[1]
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    new_filename = f"Hasil_{kode}_beres_{timestamp}{ext}"
                    new_path = os.path.join(RENAMED_DIR, new_filename)

                    shutil.move(file_path, new_path)
                    renamed_files.append((new_filename, new_path))
                    renamed_count += 1
                else:
                    skipped_files.append(uploaded_file.name)

            except Exception as e:
                skipped_files.append(uploaded_file.name)
                st.error(f"Gagal memproses {uploaded_file.name}: {e}")
            finally:
                if os.path.exists(compressed_path):
                    try:
                        os.remove(compressed_path)
                    except:
                        pass

    # Tampilkan Hasil
    st.success(f"✅ Total berhasil di-rename: {renamed_count}")
    if skipped_files:
        st.warning(f"⚠️ Gagal membaca kode dari {len(skipped_files)} file:")
        st.code("\n".join(skipped_files))

    if renamed_files:
        st.subheader("📥 Unduh File Hasil Rename:")
        for filename, path in renamed_files:
            with open(path, "rb") as f:
                st.download_button(f"⬇️ {filename}", f, file_name=filename)

# Reset Session
if st.button("🔄 Reset Aplikasi"):
    st.session_state.clear()
    st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("📌 Aplikasi ini mendeteksi kode wilayah dari gambar dan mengganti nama file secara otomatis. Cocok untuk kebutuhan administrasi atau dokumen wilayah.")
