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
    /* 1. Background Halaman Utama (Light Grey) */
    .stApp {
        background-color: #F0F2F6;
    }

    /* 2. Membuat Container Utama Menjadi Seperti "Card" */
    [data-testid="stAppViewContainer"] > .main > .block-container {
        background-color: #FFFFFF;
        padding: 3rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        max-width: 800px;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* 3. Styling Header & Text */
    h1 {
        color: #1E1E1E;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    p, li, .stMarkdown {
        color: #4B5563;
        font-family: 'Inter', sans-serif;
    }
    
    /* 4. Styling Input Uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #E5E7EB;
        border-radius: 10px;
        padding: 1rem;
        background-color: #F9FAFB;
    }
    
    /* 5. Styling Tombol (Button) */
    .stButton button {
        background-color: #2563EB; /* Blue 600 */
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    }
    .stButton button:hover {
        background-color: #1D4ED8; /* Blue 700 */
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
    }

    /* 6. Menyembunyikan Elemen Bawaan Streamlit (Menu, Footer) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 7. Styling Sidebar (Opsional) */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)


st.title("🛡️ IP Fraud Checker")
st.markdown("""
<div style="text-align: center; color: #6B7280; margin-bottom: 2rem;">
    <b>Ccp Engine - Cloud Version</b> <br>
    <small>Hanya IP dengan Score 0 (Clean) yang akan disimpan.</small>
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
    
    st.write(f"Total IP ditemukan: **{len(ip_list)}**")

    # Tombol Mulai
    if st.button("Mulai Pengecekan 🚀"):
        
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
                status_text.text(f"Sedang mengecek [{i+1}/{total_ips}]: {ip} via Proxy ...")
                
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
                
                # Tampilkan tabel hasil sementara (hanya yang clean)
                if clean_ips:
                    df = pd.DataFrame(clean_ips, columns=["Clean IP Address (Score 0)"])
                    table_placeholder.dataframe(df, height=200)

                time.sleep(1) 
                
            status_text.success("Pengecekan Selesai!")
            
            # --- HASIL AKHIR ---
            st.divider()
            st.subheader("Hasil Pengecekan")
            st.write(f"Ditemukan **{len(clean_ips)}** IP Bersih.")
            
            if clean_ips:
                # Membuat string untuk didownload
                result_text = "\n".join(clean_ips)
                
                st.download_button(
                    label="📥 Download List IP Bersih (.txt)",
                    data=result_text,
                    file_name="clean_ips_result.txt",
                    mime="text/plain"
                )
            else:
                st.warning("Tidak ada IP dengan score 0 ditemukan (atau gagal mengambil data).")
