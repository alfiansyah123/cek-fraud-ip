import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import time
import random
import re
import pandas as pd

# --- KONFIGURASI HALAMAN WEBSITE ---
st.set_page_config(page_title="IP Fraud Checker", page_icon="🛡️")

st.title("🛡️ IP Fraud Checker - Ccp Engine")
st.markdown("""
**Hanya IP dengan Score 0 (Clean) yang akan disimpan.**
""")

# --- FUNGSI SCRAPING (Sama seperti sebelumnya) ---
def get_fraud_score(scraper, ip):
    base_url = "https://scamalytics.com/ip/"
    url = f"{base_url}{ip}"
    try:
        response = scraper.get(url, timeout=10)
        
        if response.status_code == 429:
            return "RATE_LIMIT"
        if response.status_code != 200:
            return "ERROR"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Mencari Score
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
        
        # Inisialisasi Scraper
        scraper = cloudscraper.create_scraper(browser='chrome')
        
        # Tempat menyimpan hasil
        clean_ips = []
        logs = []
        
        # Membuat Progress Bar & Status Text
        progress_bar = st.progress(0)
        status_text = st.empty()
        table_placeholder = st.empty()
        
        total_ips = len(ip_list)
        
        for i, ip in enumerate(ip_list):
            # Update status
            status_text.text(f"Sedang mengecek [{i+1}/{total_ips}]: {ip} ...")
            
            # Cek Score
            score = get_fraud_score(scraper, ip)
            
            # Logika Hasil
            status = "Unknown"
            if score == "RATE_LIMIT":
                st.warning("Terlalu cepat! Istirahat 60 detik...")
                time.sleep(60)
                status = "Rate Limit"
            elif score == "ERROR":
                status = "Error"
            elif score is not None:
                status = f"Score: {score}"
                if score == 0:
                    clean_ips.append(ip)
                    status += " ✅ (CLEAN)"
                else:
                    status += " ❌ (HIGH RISK)"
            
            # Simpan log kecil untuk debug (opsional, bisa dihapus agar ringan)
            # logs.append({"IP": ip, "Status": status})
            
            # Update Progress Bar
            progress_bar.progress((i + 1) / total_ips)
            
            # Tampilkan tabel hasil sementara (hanya yang clean)
            if clean_ips:
                df = pd.DataFrame(clean_ips, columns=["Clean IP Address (Score 0)"])
                table_placeholder.dataframe(df, height=200)

            # JEDA WAKTU (PENTING)
            time.sleep(random.uniform(3, 6))
            
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
            st.warning("Tidak ada IP dengan score 0 ditemukan.")
