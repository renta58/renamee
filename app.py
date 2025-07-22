import streamlit as st
import os
import re
import shutil
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import easyocr

# Inisialisasi OCR
reader = easyocr.Reader(['id', 'en'], gpu=False)

# Direktori tetap
UPLOAD_DIR = "upload_images"
RENAMED_DIR = "renamed_images"
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
        print(f"[ERROR] Gagal kompres {input_path}: {e}")
        return input_path

# Preprocessing
def preprocess(img):
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(2.5)
    img = img.filter(ImageFilter.SHARPEN)
    return img

# Deteksi hanya kode dengan pola "1209xxx"
def detect_kode_1209(img):
    ocr_results = []
    for angle in [0, 90, 180, 270]:
        rotated = img.rotate(angle, expand=True)
        processed = preprocess(rotated)
        img_array = np.array(processed)
        texts = reader.readtext(img_array, detail=0)
        ocr_results.extend(texts)

    all_text = " ".join(ocr_results)
    
    # Temukan hanya pola 1209 diikuti 3 digit atau lebih
    matches = re.findall(r"1209\d{3,}", all_text)

    if matches:
        # Ambil yang terpanjang atau pertama
        return sorted(matches, key=len, reverse=True)[0]
    return None

# UI Streamlit
st.set_page_config(page_title="OCR Rename 1209", layout="centered")
st.title("📸 Rename Otomatis Gambar Berdasarkan Kode 1209xxx")

uploaded_files = st.file_uploader("Unggah Gambar", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    renamed_count = 0
    skipped_files = []

    for uploaded_file in uploaded_files:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            compressed_path = os.path.join(UPLOAD_DIR, f"compressed_{uploaded_file.name}")
            used_path = compress_image(file_path, compressed_path)

            img = Image.open(used_path)
            kode = detect_kode_1209(img)

            if kode:
                ext = os.path.splitext(uploaded_file.name)[1]
                new_filename = f"Hasil_{kode}_beres{ext}"
                new_path = os.path.join(RENAMED_DIR, new_filename)

                counter = 1
                while os.path.exists(new_path):
                    new_filename = f"Hasil_{kode}_{counter}_beres{ext}"
                    new_path = os.path.join(RENAMED_DIR, new_filename)
                    counter += 1

                shutil.move(file_path, new_path)
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

    # Ringkasan hasil
    st.success(f"✅ Total gambar berhasil di-rename: {renamed_count}")
    if skipped_files:
        st.warning(f"⚠️ Gagal membaca kode dari {len(skipped_files)} file:")
        st.code("\n".join(skipped_files))

    # Tampilkan hasil
    if renamed_count:
        st.subheader("📁 Unduh File yang Telah Diubah Namanya")
        for fname in os.listdir(RENAMED_DIR):
            fpath = os.path.join(RENAMED_DIR, fname)
            with open(fpath, "rb") as f:
                st.download_button(label=f"⬇️ {fname}", data=f, file_name=fname)

# Footer
st.markdown("---")
st.markdown("📌 Aplikasi ini mendeteksi dan menamai ulang gambar berdasarkan kode wilayah 1209xxx yang terdeteksi secara otomatis dari gambar.")
