import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import pandas as pd

# --- 1. KONFIGURASI HALAMAN ---
# --- CUSTOM CSS FOR "CLEAN CARD" UI ---
st.markdown("""
<style>
    /* IMPORT FONT INTER */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* 1. Global Background & Text Color Reset */
    .stApp {
        background-color: #F3F4F6 !important; /* Light Grey */
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Force text color to dark (override Dark Mode defaults) */
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown {
        color: #111827 !important;
    }

    /* 2. Main Card Container */
    [data-testid="stAppViewContainer"] > .main > .block-container {
        background-color: #FFFFFF !important;
        padding: 40px !important;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        max-width: 800px;
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* 3. Header Styling */
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 800 !important;
        font-size: 26px !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
        margin-top: 0 !important;
    }
    
    .header-subtitle {
        text-align: center;
        color: #6B7280 !important; /* Lighter grey for subtitle */
        font-size: 14px;
        margin-bottom: 2rem;
    }

    /* 4. Upload Area Styling */
    [data-testid="stFileUploader"] {
        border: 2px dashed #E5E7EB;
        border-radius: 8px;
        padding: 20px;
        background-color: #FAFAFA;
    }
    [data-testid="stFileUploader"] section {
        padding: 0;
    }
    /* Fix text inside uploader which might be white in dark mode */
    [data-testid="stFileUploader"] div, [data-testid="stFileUploader"] span {
        color: #111827 !important;
    }
    [data-testid="stFileUploader"] small {
        color: #6B7280 !important;
    }

    /* 5. Button Styling (Dark/Black) */
    .stButton button {
        background-color: #1F2937 !important; /* Dark Grey/Black */
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 15px;
        width: 100%;
        transition: transform 0.1s ease-in-out;
    }
    .stButton button:hover {
        background-color: #000000 !important; /* Pure Black on hover */
        transform: scale(1.01);
    }
    
    /* 6. Success Message Box */
    .success-box {
        background-color: #ECFDF5 !important;
        border: 1px solid #10B981;
        color: #064E3B !important;
        padding: 16px;
        border-radius: 8px;
        text-align: center;
        margin: 20px 0;
    }
    .success-box span {
        font-size: 1.2rem;
    }
    
    /* 7. Footer / Copyright */
    .footer-copyright {
        text-align: center;
        color: #9CA3AF !important;
        font-size: 12px;
        margin-top: 40px;
        border-top: 1px solid #E5E7EB;
        padding-top: 20px;
    }

    /* Hide standard elements */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Remove padding to pull everything into the card */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

</style>
""", unsafe_allow_html=True)

# --- APP LAYOUT ---

# 1. Header Section
st.markdown("""
<h1>🛡️ IP Fraud Checker</h1>
<div class="header-subtitle">
    <b>Ccp Engine - Cloud Version</b><br>
    Hanya IP dengan Score 0 (Clean) yang akan disimpan.
</div>
""", unsafe_allow_html=True)


st.sidebar.header("Konfigurasi API")
DEFAULT_API_KEY = "837bd81811ea8fcf5aecc3f3c219424d" 
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
        if response.status_code == 403: return "AUTH_ERROR"
        if response.status_code != 200: return "ERROR"

        soup = BeautifulSoup(response.text, 'html.parser')
        score_div = soup.find('div', class_='score')
        score_text = score_div.get_text().strip() if score_div else ""
        
        if not score_text:
             for elem in soup.find_all(string=True):
                if "Fraud Score:" in elem:
                    score_text = elem
                    break
        match = re.search(r'(\d+)', score_text)
        if match: return int(match.group(1))
        return None
    except Exception: return None


# 2. Main Content
uploaded_file = st.file_uploader("Upload file list IP (.txt)", type=["txt"])

if uploaded_file is not None:
    stringio = uploaded_file.getvalue().decode("utf-8")
    ip_list = [line.strip() for line in stringio.splitlines() if line.strip()]
    
    st.write(f"Total IP ditemukan: **{len(ip_list)}**")

    if st.button("Mulai Pengecekan 🚀"):
        
        if not api_key_input:
            st.error("⚠️ Harap masukkan ScraperAPI Key di sidebar!")
        else:
            clean_ips = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Placeholder untuk tabel hasil (biar muncul di bawah tombol)
            success_msg_placeholder = st.empty()
            table_placeholder = st.empty()
            results_header_placeholder = st.empty()
            download_btn_placeholder = st.empty()
            
            total_ips = len(ip_list)
            
            for i, ip in enumerate(ip_list):
                status_text.text(f"Processing {i+1}/{total_ips}: {ip}...")
                
                score = get_fraud_score(ip, api_key_input)
                
                if score == "AUTH_ERROR":
                    st.error("Gagal! API Key salah atau Kuota habis.")
                    break
                
                if score == 0:
                    clean_ips.append(ip)
                
                progress_bar.progress((i + 1) / total_ips)
                
                # Update table real-time
                if clean_ips:
                    df = pd.DataFrame(clean_ips, columns=["CLEAN IP ADDRESS (SCORE 0)"])
                    table_placeholder.dataframe(df, use_container_width=True, hide_index=False)
                
                time.sleep(0.5) 
            
            # Clear progress ui elements
            status_text.empty()
            progress_bar.empty()
            
            # 3. Success State
            success_msg_placeholder.markdown("""
            <div class="success-box">
                <span>✅</span> Pengecekan Selesai!
            </div>
            """, unsafe_allow_html=True)
            
            # 4. Results Footer
            results_header_placeholder.subheader("Hasil Pengecekan")
            st.write(f"Ditemukan **{len(clean_ips)}** IP Bersih.")
            
            if clean_ips:
                result_text = "\n".join(clean_ips)
                
                # Download Button with custom styling implies standard st.download_button 
                # but we rely on the global button style we set earlier (dark).
                st.download_button(
                    label="⬇️ Download List IP Bersih (.txt)",
                    data=result_text,
                    file_name="clean_ips_result.txt",
                    mime="text/plain"
                )
            else:
                st.warning("Tidak ada IP Clean ditemukan.")

# 5. Copyright Footer
st.markdown("""
<div class="footer-copyright">
    &copy; 2023 IP Fraud Checker Tool. All rights reserved.
</div>
""", unsafe_allow_html=True)
