import streamlit as st
import os
import re
import shutil
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import easyocr

# Inisialisasi OCR
reader = easyocr.Reader(['id', 'en'])

# Direktori penyimpanan
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "upload_images")
RENAMED_DIR = os.path.join(BASE_DIR, "renamed_images")

# Cek & buat direktori aman
for folder in [UPLOAD_DIR, RENAMED_DIR]:
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except FileExistsError:
            pass

# Fungsi kompresi
def compress_image(input_path, output_path, max_size=(1024, 1024), quality=70):
    try:
        img = Image.open(input_path)
        img.thumbnail(max_size)
        img.save(output_path, optimize=True, quality=quality)
        return output_path
    except Exception as e:
        print(f"[ERROR] Kompresi gagal untuk {input_path}: {e}")
        return input_path

# Fungsi preprocessing
def preprocess(img):
    img = img.convert("L")  # grayscale
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img

# Deteksi kode wilayah dari 4 sudut
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

# Konfigurasi halaman
st.set_page_config(page_title="OCR Rename App", layout="centered")
st.title("📸 Rename Gambar Otomatis dengan OCR")

# Upload file
uploaded_files = st.file_uploader("Unggah gambar (JPG, JPEG, PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    renamed_count = 0
    skipped_files = []

    for uploaded_file in uploaded_files:
        original_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(original_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            compressed_path = os.path.join(UPLOAD_DIR, f"compressed_{uploaded_file.name}")
            used_path = compress_image(original_path, compressed_path)

            img = Image.open(used_path)
            kode = detect_full_kode(img)

            if kode and len(kode) >= 8:
                ext = os.path.splitext(uploaded_file.name)[1]
                new_filename = f"Hasil_{kode}_beres{ext}"
                new_path = os.path.join(RENAMED_DIR, new_filename)

                counter = 1
                while os.path.exists(new_path):
                    new_filename = f"Hasil_{kode}_{counter}_beres{ext}"
                    new_path = os.path.join(RENAMED_DIR, new_filename)
                    counter += 1

                shutil.move(original_path, new_path)
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

    # Download hasil rename
    if renamed_count:
        st.subheader("⬇️ Unduh File yang Telah Diubah")
        for fname in os.listdir(RENAMED_DIR):
            fpath = os.path.join(RENAMED_DIR, fname)
            with open(fpath, "rb") as f:
                st.download_button(label=f"📥 {fname}", data=f, file_name=fname)

# Footer
st.markdown("---")
st.markdown("📌 Aplikasi ini membaca kode wilayah dari gambar dan mengganti namanya otomatis. Dibuat dengan ❤️ menggunakan EasyOCR dan Streamlit.")
