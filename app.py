import streamlit as st
import os
import sqlite3
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter
import easyocr
import numpy as np
import zipfile
import tempfile
import shutil

# === OCR dengan preprocessing dan rotasi ===
def extract_kode_wilayah(image_path):
    img = Image.open(image_path)

    def preprocess(img):
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
        return img

    kode_pattern = r'\b\d{14}\b'
    best_result = None

    for angle in [0, 90, 180, 270]:
        rotated = img.rotate(angle, expand=True)
        processed = preprocess(rotated)
        np_img = np.array(processed)
        result = reader.readtext(np_img, detail=0)
        for text in result:
            if any(c.isdigit() for c in text):
                match = [t for t in result if len(t) == 14 and t.isdigit() and t.startswith("1209")]
                if match:
                    return match[0]
                elif not best_result:
                    best_result = text

    return best_result if best_result else None

# === Setup ===
st.set_page_config(layout="wide")
st.title("📝 Rename File Gambar")
reader = easyocr.Reader(['id', 'en'])
UPLOAD_FOLDER = 'uploaded_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === DB ===
conn = sqlite3.connect('riwayat.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS riwayat (
    username TEXT,
    waktu TEXT,
    nama_awal TEXT,
    nama_akhir TEXT
)
''')
conn.commit()

def insert_riwayat(username, waktu, awal, akhir):
    c.execute("INSERT INTO riwayat VALUES (?, ?, ?, ?)", (username, waktu, awal, akhir))
    conn.commit()

def get_user_riwayat(username):
    c.execute("SELECT waktu, nama_awal, nama_akhir FROM riwayat WHERE username = ? ORDER BY waktu DESC", (username,))
    return c.fetchall()

username = "default_user"

# Tabs


# === Tab 1 ===
tab1, tab2, tab3 = st.tabs(["📄 Upload Gambar", "📁 Rename dari Arsip ZIP", "📜 Riwayat Rename"])

with tab1:
    st.header("📝 Upload dan Rename File")  
    uploaded_file = st.file_uploader("Unggah Gambar", type=['jpg', 'jpeg', 'png'])
    temp_info = {}

    if uploaded_file:
        filename = uploaded_file.name
        save_path = os.path.join(UPLOAD_FOLDER, filename)

        with open(save_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"\u2705 File diunggah: {filename}")

        kode = extract_kode_wilayah(save_path)

        if kode:
            ext = os.path.splitext(filename)[-1]
            new_name = f"Hasil_{kode}_beres{ext}"
            new_path = os.path.join(UPLOAD_FOLDER, new_name)

            st.markdown(f"**Hasil Deteksi OCR:** `{kode}`")

            if st.button("🔄 Proses Rename"):
                shutil.copy(save_path, new_path)  # Overwrite langsung jika ada
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                insert_riwayat(username, now, filename, new_name)

                st.success(f"\u2705 Berhasil rename menjadi: {new_name}")
                with open(new_path, "rb") as f:
                    st.download_button("Download File Hasil", f.read(), file_name=new_name, mime="image/jpeg")
        else:
            st.warning("\u26a0\ufe0f Gagal mendeteksi kode wilayah (harus diawali 1209 dan 14 digit).")


# === Tab 2 ===
with tab2:
    st.header(" Rename Gambar dari Arsip ZIP")
    archive_file = st.file_uploader("Unggah file .zip", type=["zip"])

    if archive_file:
        with st.spinner("\ud83d\udcc2 Mengekstrak file..."):
            temp_dir = tempfile.mkdtemp()
            archive_path = os.path.join(temp_dir, archive_file.name)

            with open(archive_path, "wb") as f:
                f.write(archive_file.read())

            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)

            try:
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                    st.success("\u2705 ZIP berhasil diekstrak.")
            except Exception as e:
                st.error(f"\u274c Gagal ekstrak ZIP: {e}")
                shutil.rmtree(temp_dir)
                st.stop()

            renamed_dir = os.path.join(temp_dir, "renamed")
            os.makedirs(renamed_dir, exist_ok=True)
            count = 0

            image_found = False

            for root, _, files in os.walk(extract_dir):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        image_found = True
                        full_path = os.path.join(root, file)
                        st.write(f"\ud83d\udd0d Memproses file: {file}")

                        try:
                            kode = extract_kode_wilayah(full_path)
                            if kode:
                                ext = os.path.splitext(file)[-1]
                                new_name = f"Hasil_{kode}_beres{ext}"
                                new_path = os.path.join(renamed_dir, new_name)

                                # Langsung timpa jika ada
                                shutil.copy(full_path, new_path)
                                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                insert_riwayat(username, now, file, new_name)
                                count += 1
                            else:
                                st.warning(f"\u26a0\ufe0f Tidak ditemukan kode wilayah di: {file}")
                        except Exception as e:
                            st.error(f"\u274c Gagal proses {file}: {e}")

            if not image_found:
                st.warning("\u26a0\ufe0f Tidak ditemukan file gambar (.jpg/.jpeg/.png) dalam ZIP.")
                shutil.rmtree(temp_dir)
                st.stop()

            try:
                zip_output_path = os.path.join(temp_dir, "hasil_rename.zip")
                with zipfile.ZipFile(zip_output_path, 'w') as zipf:
                    for file in os.listdir(renamed_dir):
                        file_path = os.path.join(renamed_dir, file)
                        zipf.write(file_path, arcname=file)

                st.success(f"\u2705 Selesai! {count} gambar berhasil di-rename.")

                with open(zip_output_path, "rb") as f:
                    st.download_button(
                        label="\u2b07\ufe0f Download Hasil Rename (ZIP)",
                        data=f.read(),
                        file_name="hasil_rename.zip",
                        mime="application/zip"
                    )
            except Exception as e:
                st.error(f"\u274c Gagal membuat ZIP hasil: {e}")

            shutil.rmtree(temp_dir)


# === Tab 3 ===
with tab3:
    st.header("Riwayat Rename")
    riwayat = get_user_riwayat(username)

    if not riwayat:
        st.info("Belum ada riwayat rename.")
        st.stop()

    opsi_download = st.radio("Pilih cara unduh:", ("\u2b07\ufe0f Per File", "\ud83d\udcc6 Unduh Semua (ZIP)"))

    if opsi_download == "\u2b07\ufe0f Per File":
        for waktu, awal, akhir in riwayat:
            path_file = os.path.join(UPLOAD_FOLDER, akhir)
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"{waktu} | {awal} \u2794 {akhir}")
            with col2:
                if os.path.exists(path_file):
                    with open(path_file, "rb") as f:
                        st.download_button("\u2b07\ufe0f", f.read(), file_name=akhir, mime="image/jpeg", key=path_file)
                else:
                    st.error(f"\u274c File tidak ditemukan: {akhir}")
    else:
        with st.spinner(" Menyiapkan file ZIP..."):
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "riwayat_rename.zip")

            with zipfile.ZipFile(zip_path, "w") as zipf:
                for _, _, nama_akhir in riwayat:
                    file_path = os.path.join(UPLOAD_FOLDER, nama_akhir)
                    if os.path.exists(file_path):
                        zipf.write(file_path, arcname=nama_akhir)

            with open(zip_path, "rb") as f:
                st.download_button(
                    label="Download Semua Riwayat (ZIP)",
                    data=f.read(),
                    file_name="riwayat_rename.zip",
                    mime="application/zip"
                )
            shutil.rmtree(temp_dir)
