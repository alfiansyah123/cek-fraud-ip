import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import pandas as pd

# --- 1. KONFIGURASI HALAMAN ---
# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="IP Fraud Checker", page_icon="🛡️", layout="centered")

# --- CUSTOM CSS FOR "CARD" UI ---
st.markdown("""
<style>
    /* 1. Background Halaman Utama */
    .stApp {
        background-color: #F0F4F8; /* Light Blue-Grey */
    }

    /* 2. Container "Card" Putih - Mengatur seluruh area konten */
    [data-testid="stAppViewContainer"] > .main > .block-container {
        background-color: #FFFFFF;
        padding: 3rem; 
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.05); /* Soft Shadow */
        max-width: 700px; /* Lebar card diperkecil biar proporsional */
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* 3. Styling Header & Text */
    h1 {
        color: #111827;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        text-align: center;
        margin-top: 0;
        margin-bottom: 0.5rem;
        font-size: 2.2rem;
    }
    
    .subtitle {
        text-align: center;
        color: #6B7280;
        font-family: 'Inter', sans-serif;
        margin-bottom: 2.5rem;
        font-size: 0.95rem;
    }

    /* 4. Styling Input Uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #D1D5DB;
        border-radius: 12px;
        padding: 1.5rem;
        background-color: #F9FAFB;
        transition: border-color 0.3s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #3B82F6;
    }
    
    /* 5. Styling Tombol (Button) */
    .stButton button {
        background-color: #0F172A; /* Dark Navy for premium feel */
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        width: 100%;
        margin-top: 1rem;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background-color: #1E293B;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* 6. Hapus elemen default */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* 7. Hasil Style */
    .success-box {
        padding: 1rem;
        background-color: #ECFDF5;
        border: 1px solid #10B981;
        border-radius: 8px;
        color: #064E3B;
        text-align: center;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER (Sekarang manual pake HTML biar masuk Card) ---
st.markdown("""
<h1>🛡️ IP Fraud Checker</h1>
<div class="subtitle">
    <b>Ccp Engine - Cloud Version</b> <br>
    Hanya IP dengan Score 0 (Clean) yang akan disimpan.
</div>
""", unsafe_allow_html=True)


st.sidebar.header("Konfigurasi API")

DEFAULT_API_KEY = "6b3af5fa676dfad17873b78c6e1117f1" 
api_key_input = st.sidebar.text_input("Masukkan ScraperAPI Key", value=DEFAULT_API_KEY, type="password")

st.sidebar.info("Daftar di [ScraperAPI.com](https://www.scraperapi.com) untuk dapat key gratis.")


def get_fraud_score(ip, api_key):
    
    target_url = f"https://scamalytics.com/ip/{ip}"
    
    
    payload = {
        'api_key': api_key,
        'url': target_url, 
        'country_code': 'us', 
        'device_type': 'desktop' 
    }

    try:
        
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
        
        # Cek jika quota habis atau error auth
        if response.status_code == 403:
            return "AUTH_ERROR" # Key salah atau kuota habis
        
        if response.status_code != 200:
            return "ERROR"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        score_div = soup.find('div', class_='score')
        score_text = score_div.get_text().strip() if score_div else ""
        
        if not score_text:
             for elem in soup.find_all(string=True):
                if "Fraud Score:" in elem:
                    score_text = elem
                    break
        
        # Ambil angka dengan Regex
        match = re.search(r'(\d+)', score_text)
        if match:
            return int(match.group(1))
        return None

    except Exception as e:
        return None

# --- BAGIAN UTAMA WEBSITE ---

# 1. Upload File
uploaded_file = st.file_uploader("Upload file list IP (.txt)", type=["txt"])

if uploaded_file is not None:
    # Membaca file yang diupload
    stringio = uploaded_file.getvalue().decode("utf-8")
    ip_list = [line.strip() for line in stringio.splitlines() if line.strip()]
    
    st.markdown(f"<p style='text-align:center; color:#6B7280; font-size:0.9rem;'>Total IP ditemukan: <b>{len(ip_list)}</b></p>", unsafe_allow_html=True)

    # Tombol Mulai
    if st.button("MULAI CEK SEKARANG ✨"):
        
        if not api_key_input:
            st.error("⚠️ Harap masukkan ScraperAPI Key di menu sebelah kiri (Sidebar)!")
        else:
            # Tempat menyimpan hasil
            clean_ips = []
            
            # Membuat Progress Bar & Status Text
            progress_bar = st.progress(0)
            status_text = st.empty()
            table_placeholder = st.empty()
            
            total_ips = len(ip_list)
            
            for i, ip in enumerate(ip_list):
                # Update status
                status_text.text(f"Sedang mengecek [{i+1}/{total_ips}]: {ip}...")
                
                # Cek Score (Panggil fungsi baru)
                score = get_fraud_score(ip, api_key_input)
                
                # Logika Hasil
                status_msg = ""
                if score == "AUTH_ERROR":
                    st.error("Gagal! API Key salah atau Kuota ScraperAPI habis.")
                    break # Stop looping
                elif score == "ERROR":
                    status_msg = "Error/Gagal Load"
                elif score is not None:
                    status_msg = f"Score: {score}"
                    if score == 0:
                        clean_ips.append(ip)
                        status_msg += " ✅"
                    else:
                        status_msg += " ❌"
                
                # Update Progress Bar
                progress_bar.progress((i + 1) / total_ips)
                
                time.sleep(1) 
                
            status_text.empty() # Hapus text loading setelah selesai
            progress_bar.empty() # Hapus progress bar
            
            # --- HASIL AKHIR ---
            st.divider()
            
            if clean_ips:
                st.markdown(f"""
                <div class="success-box">
                    <h3>✅ Selesai!</h3>
                    <p>Ditemukan <b>{len(clean_ips)}</b> IP Bersih.</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("") # Spacer
                
                st.subheader("📋 Hasil (Copy All)")
                # Tampilkan sebagai Code Block agar bisa langsung di-Copy
                result_text = "\n".join(clean_ips)
                st.code(result_text, language="text")
                
            else:
                st.warning("Tidak ada IP dengan score 0 ditemukan (atau gagal mengambil data).")
