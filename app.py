import streamlit as st
import os
import easyocr
import shutil
import uuid
import json
from datetime import datetime

# ------------------ Konstanta ------------------
UPLOAD_DIR = "upload_images"
RENAMED_DIR = "renamed_images"
HISTORY_FILE = "rename_history.json"
CREDENTIALS = {"admin": "admin123", "user": "user123"}  # Ubah sesuai kebutuhan

# ------------------ Buat Folder ------------------
for path in [UPLOAD_DIR, RENAMED_DIR]:
    if os.path.exists(path) and not os.path.isdir(path):
        os.remove(path)  # hapus file jika bentrok
    os.makedirs(path, exist_ok=True)

# ------------------ Fungsi Utilitas ------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def add_history(username, original, renamed):
    history = load_history()
    if username not in history:
        history[username] = []
    history[username].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "original": original,
        "renamed": renamed
    })
    save_history(history)

# ------------------ Fungsi OCR ------------------
reader = easyocr.Reader(["en"])

def detect_code_from_image(image_path):
    try:
        result = reader.readtext(image_path, detail=0)
        for text in result:
            if any(char.isdigit() for char in text):  # Ambil teks yang mengandung angka
                return text.replace(" ", "_")
        return "no_code"
    except:
        return "error"

# ------------------ Login ------------------
def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in CREDENTIALS and CREDENTIALS[username] == password:
            st.session_state["username"] = username
            st.success(f"Logged in as {username}")
        else:
            st.error("Username atau password salah.")

# ------------------ Halaman Rename Gambar ------------------
def rename_page():
    st.title("OCR Rename Otomatis")
    uploaded_files = st.file_uploader("Unggah gambar", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

    if uploaded_files:
        for uploaded_file in uploaded_files:
            unique_id = str(uuid.uuid4())
            temp_path = os.path.join(UPLOAD_DIR, f"{unique_id}_{uploaded_file.name}")
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            detected = detect_code_from_image(temp_path)
            new_name = f"Hasil_{detected}_beres{os.path.splitext(uploaded_file.name)[1]}"
            new_path = os.path.join(RENAMED_DIR, new_name)
            shutil.copy(temp_path, new_path)

            add_history(st.session_state["username"], uploaded_file.name, new_name)
            st.success(f"✔️ {uploaded_file.name} ➜ {new_name}")

        st.info("✅ Semua gambar telah diubah namanya dan disimpan di folder 'renamed_images'.")

# ------------------ Halaman Riwayat Rename ------------------
def history_page():
    st.title("Riwayat Rename Gambar")
    history = load_history()
    username = st.session_state["username"]

    if username == "admin":
        st.subheader("👑 Admin - Semua Riwayat")
        for user, records in history.items():
            st.write(f"### 📁 Pengguna: {user}")
            for record in records:
                st.write(f"- ⏱️ {record['timestamp']}: `{record['original']}` → `{record['renamed']}`")
    else:
        user_history = history.get(username, [])
        st.subheader(f"📜 Riwayat {username}")
        if user_history:
            for record in user_history:
                st.write(f"- ⏱️ {record['timestamp']}: `{record['original']}` → `{record['renamed']}`")
        else:
            st.info("Belum ada riwayat.")

# ------------------ Main App ------------------
if "username" not in st.session_state:
    login()
else:
    st.sidebar.title("Navigasi")
    menu = st.sidebar.radio("Pilih halaman:", ["Rename Gambar", "Riwayat Rename", "Logout"])

    if menu == "Rename Gambar":
        rename_page()
    elif menu == "Riwayat Rename":
        history_page()
    elif menu == "Logout":
        del st.session_state["username"]
        st.experimental_rerun()
