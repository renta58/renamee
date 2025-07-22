import streamlit as st
import os
import pytesseract
from PIL import Image
import re
from datetime import datetime
from pathlib import Path

# Folder penyimpanan upload
UPLOAD_FOLDER = "uploaded_images"
HISTORY_FILE = "rename_history.txt"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Fungsi ekstraksi kode dari gambar menggunakan pytesseract
def extract_code_from_image(image_path):
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        match = re.search(r"\d{3,}", text)
        return match.group(0) if match else "UNKNOWN"
    except Exception as e:
        return "ERROR"

# Fungsi menyimpan riwayat rename
def save_history(original_name, new_name, username):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{now}\t{username}\t{original_name}\t{new_name}\n")

# Fungsi untuk melihat riwayat rename
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        lines = f.readlines()
    return [line.strip().split("\t") for line in lines]

# Login sederhana (tanpa database)
USERS = {"admin": "admin123", "user": "user123"}

if "username" not in st.session_state:
    st.session_state.username = None

if st.session_state.username is None:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state.username = username
            st.success("Login berhasil")
            st.experimental_rerun()
        else:
            st.error("Username atau password salah")
else:
    st.sidebar.success(f"Login sebagai {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.username = None
        st.experimental_rerun()

    st.title("Aplikasi Rename Gambar Otomatis dengan OCR")

    uploaded_files = st.file_uploader("Unggah satu atau beberapa gambar", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            code = extract_code_from_image(file_path)
            ext = os.path.splitext(uploaded_file.name)[1]
            new_filename = f"Hasil_{code}_beres{ext}"
            new_path = os.path.join(UPLOAD_FOLDER, new_filename)
            os.rename(file_path, new_path)

            st.success(f"Berhasil rename: {uploaded_file.name} -> {new_filename}")
            save_history(uploaded_file.name, new_filename, st.session_state.username)

    st.subheader("Riwayat Rename")
    history = load_history()
    if history:
        for time, user, original, new in reversed(history):
            if st.session_state.username == "admin" or st.session_state.username == user:
                st.write(f"[{time}] {user}: {original} → {new}")
    else:
        st.info("Belum ada riwayat rename.")
