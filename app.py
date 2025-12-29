import streamlit as st
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import plotly.express as px
import plotly.graph_objects as go
import time
import sys
import io

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="BDDK ANALİZ", layout="wide", page_icon="🏦", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #F9F9F9; }
    [data-testid="stSidebar"] { background-color: #FCB131; border-right: 1px solid #e0e0e0; }
    [data-testid="stSidebar"] * { color: #000000 !important; font-family: 'Segoe UI', sans-serif; }

    div.stButton > button { 
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        font-weight: 900 !important; 
        border-radius: 8px; 
        border: 2px solid #000000 !important; 
        width: 100%; 
        padding: 15px; 
        font-size: 18px !important; 
        transition: all 0.3s ease; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover { 
        background-color: #000000 !important; 
        color: #FCB131 !important; 
        border-color: #000000 !important; 
        transform: scale(1.02); 
    }

    h1, h2, h3 { color: #d99000 !important; font-weight: 800; }
    .dataframe { font-size: 14px !important; }

    .bot-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #FCB131;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .bot-title { font-weight: bold; font-size: 18px; color: #333; }
    .bot-value { font-size: 24px; font-weight: bold; color: #000; }

    [data-testid="stSidebarCollapseButton"] { display: none; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIG ---
AY_LISTESI = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
TARAF_SECENEKLERI = ["Sektör", "Mevduat-Kamu", "Mevduat-Yerli Özel", "Mevduat-Yabancı"]

VERI_KONFIGURASYONU = {
    "📌 Toplam Aktifler": {"tab": "tabloListesiItem-1", "row_text": "TOPLAM AKTİFLER", "col_id": "grdRapor_Toplam"},
    "📌 Toplam Özkaynaklar": {"tab": "tabloListesiItem-1", "row_text": "TOPLAM ÖZKAYNAKLAR", "col_id": "grdRapor_Toplam"},
    "💰 Dönem Net Kârı": {"tab": "tabloListesiItem-2", "row_text": "DÖNEM NET KARI (ZARARI)", "col_id": "grdRapor_Toplam"},
    "📊 Sermaye Yeterliliği Rasyosu": {"tab": "tabloListesiItem-12", "row_text": "Sermaye Yeterliliği Standart Rasyosu", "col_id": "grdRapor_Toplam"},
    "🏦 Toplam Krediler": {"tab": "tabloListesiItem-3", "row_text": "Toplam Krediler", "col_id": "grdRapor_Toplam"},
    "⚠️ Takipteki Alacaklar": {"tab": "tabloListesiItem-1", "row_text": "Takipteki Alacaklar", "col_id": "grdRapor_Toplam"},
    "💳 Bireysel Kredi Kartları": {"tab": "tabloListesiItem-4", "row_text": "Bireysel Kredi Kartları (10+11)", "col_id": "grdRapor_Toplam"},
    "🏠 Tüketici Kredileri": {"tab": "tabloListesiItem-4", "row_text": "Tüketici Kredileri (2+3+4)", "col_id": "grdRapor_Toplam"},
    "⚠️ Toplam Takipteki Bireysel Krediler": {"tab": "tabloListesiItem-4", "row_text": "Toplam - Takipteki Tük. Krd. ve Takipteki Bireysel Kredi Kartları (13+17)", "col_id": "grdRapor_Toplam"},
    "🏠 Ticari Krediler": {"tab": "tabloListesiItem-4", "row_text": "Toplam - Taksitli Tic. Krd.(Dövize End. Dahil) ve Kurumsal Kredi Kartları (19+23+27)", "col_id": "grdRapor_Toplam"},
    "🏭 KOBİ Kredileri": {"tab": "tabloListesiItem-6", "row_text": "Toplam KOBİ Kredileri", "col_id": "grdRapor_NakdiKrediToplam"},
    "⚠️ Toplam Takipteki Ticari Krediler": {"tab": "tabloListesiItem-4", "row_text": "Takipteki Taksitli Tic.  Krd. ve Kurumsal Kredi Kartları Toplamı (31+35)", "col_id": "grdRapor_Toplam"},
}


# --- 3. DRIVER YÖNETİMİ ---
def get_driver():
    if sys.platform == "linux":
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.set_preference('permissions.default.image', 2)
        try:
            service = FirefoxService(GeckoDriverManager().install())
            return webdriver.Firefox(service=service, options=options)
        except Exception:
            return None
    else:
        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        try:
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except Exception:
            return None


# --- 4. VERİ ÇEKME MOTORU ---
def scrape_bddk_data(bas_yil, bas_ay, bit_yil, bit_ay, secilen_taraflar, secilen_veriler, status_text_obj, progress_bar_obj):
    driver = None
    data = []

    try:
        driver = get_driver()
        if not driver: return pd.DataFrame()

        driver.set_page_load_timeout(60)
        driver.get("https://www.bddk.org.tr/bultenaylik")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "ddlYil")))

        bas_idx = AY_LISTESI.index(bas_ay)
        bit_idx = AY_LISTESI.index(bit_ay)
        veriler_by_tab = {}
        for veri in secilen_veriler:
            tab_id = VERI_KONFIGURASYONU[veri]['tab']
            if tab_id not in veriler_by_tab: veriler_by_tab[tab_id] = []
            veriler_by_tab[tab_id].append(veri)
        
        total_steps = (bit_yil - bas_yil) * 12 + (bit_idx - bas_idx) + 1
        current_step = 0

        for yil in range(bas_yil, bit_yil + 1):
            s_m = bas_idx if yil == bas_yil else 0
            e_m = bit_idx if yil == bit_yil else 11

            for ay_i in range(s_m, e_m + 1):
                ay_str = AY_LISTESI[ay_i]
                donem = f"{ay_str} {yil}"
                if status_text_obj: status_text_obj.info(f"⏳ **İşleniyor:** {donem}")

                try:
                    driver.execute_script("document.getElementById('ddlYil').style.display = 'block';")
                    sel_yil = Select(driver.find_element(By.ID, "ddlYil"))
                    sel_yil.select_by_visible_text(str(yil))
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", driver.find_element(By.ID, "ddlYil"))
                    time.sleep(1)

                    driver.execute_script("document.getElementById('ddlAy').style.display = 'block';")
                    sel_ay_elem = driver.find_element(By.ID, "ddlAy")
                    sel_ay = Select(sel_ay_elem)
                    sel_ay.select_by_visible_text(ay_str)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", sel_ay_elem)
                    time.sleep(1)

                    for taraf in secilen_taraflar:
                        driver.execute_script("document.getElementById('ddlTaraf').style.display = 'block';")
                        taraf_elem = driver.find_element(By.ID, "ddlTaraf")
                        select_taraf = Select(taraf_elem)
                        try:
                            select_taraf.select_by_visible_text(taraf)
                        except:
                            for opt in select_taraf.options:
                                if taraf in opt.text:
                                    select_taraf.select_by_visible_text(opt.text)
                                    break
                        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", taraf_elem)
                        time.sleep(1)

                        for tab_id, veri_listesi in veriler_by_tab.items():
                            try:
                                target_tab = wait.until(EC.element_to_be_clickable((By.ID, tab_id)))
                                driver.execute_script("arguments[0].click();", target_tab)
                                time.sleep(0.5)
                            except: continue

                            soup = BeautifulSoup(driver.page_source, 'html.parser')
                            for veri in veri_listesi:
                                conf = VERI_KONFIGURASYONU[veri]
                                current_group = None
                                for row in soup.find_all("tr"):
                                    group_cell = row.find("td", colspan=True)
                                    if group_cell:
                                        text = group_cell.get_text(strip=True)
                                        if "Sektör" in text: current_group = "Sektör"
                                        elif "Kamu" in text: current_group = "Kamu"
                                        elif "Yerli" in text: current_group = "Mevduat-Yerli Özel"
                                        elif "Yabancı" in text: current_group = "Mevduat-Yabancı"
                                        continue

                                    ad = row.find("td", {"aria-describedby": "grdRapor_Ad"})
                                    toplam = row.find("td", {"aria-describedby": conf['col_id']})

                                    if ad and toplam:
                                        row_taraf = current_group if current_group else taraf
                                        if conf['row_text'] in ad.get_text(strip=True):
                                            try:
                                                found_val = float(toplam.get_text(strip=True).replace('.', '').replace(',', '.'))
                                            except: found_val = 0.0
                                            
                                            data.append({
                                                "Dönem": donem,
                                                "Taraf": row_taraf,
                                                "Kalem": veri,
                                                "Değer": found_val,
                                                "TarihObj": pd.to_datetime(f"{yil}-{ay_i + 1}-01")
                                            })
                except: pass
                current_step += 1
                if progress_bar_obj: progress_bar_obj.progress(min(current_step / max(1, total_steps), 1.0))
    except Exception as e: st.error(f"Hata: {e}")
    finally:
        if driver: driver.quit()
    return pd.DataFrame(data)


# --- ANA EKRAN ---
with st.sidebar:
    st.title("🎛️ KONTROL PANELİ")
    st.markdown("---")
    c1, c2 = st.columns(2)
    bas_yil = c1.number_input("Başlangıç Yılı", 2022, 2030, 2025, key="sb_bas_yil")
    bas_ay = c1.selectbox("Başlangıç Ayı", AY_LISTESI, index=0, key="sb_bas_ay")
    c3, c4 = st.columns(2)
    bit_yil = c3.number_input("Bitiş Yılı", 2022, 2030, 2025, key="sb_bit_yil")
    bit_ay = c4.selectbox("Bitiş Ayı", AY_LISTESI, index=0, key="sb_bit_ay")
    st.markdown("---")
    secilen_taraflar = st.multiselect("Karşılaştır:", TARAF_SECENEKLERI, default=["Sektör", "Mevduat-Kamu"], key="sb_taraflar")
    secilen_veriler = st.multiselect("Veri:", list(VERI_KONFIGURASYONU.keys()), default=["📌 Toplam Aktifler"], key="sb_veriler")
    st.markdown("---")
    btn = st.button("ANALİZİ BAŞLAT", key="sb_btn_baslat")

st.title("🏦 BDDK Analiz Botu")

if 'df_sonuc' not in st.session_state: st.session_state['df_sonuc'] = None

if btn:
    if not secilen_taraflar or not secilen_veriler:
        st.warning("Lütfen taraf ve veri seçin.")
    else:
        status_txt = st.empty()
        status_txt.info("🌐 Veriler çekiliyor...")
        my_bar = st.progress(0)
        df = scrape_bddk_data(bas_yil, bas_ay, bit_yil, bit_ay, secilen_taraflar, secilen_veriler, status_txt, my_bar)
        my_bar.empty()
        status_txt.empty()
        if not df.empty:
            st.session_state['df_sonuc'] = df
            st.success("✅ Veriler Hazır!")
            time.sleep(1)
            st.rerun()
        else: st.error("Veri bulunamadı.")

# --- DASHBOARD ---
if st.session_state['df_sonuc'] is not None:
    df = st.session_state['df_sonuc']
    df = df.drop_duplicates(subset=["Dönem", "Taraf", "Kalem"])
    df = df.sort_values("TarihObj")

    tab1, tab2, tab3, tab4 = st.tabs(["📉 Trend", "🧪 Senaryo", "📑 Excel Raporu", "🧠 Analiz Botu"])

    # 1. TREND
    with tab1:
        kalem_sec = st.selectbox("Veri Seç:", df["Kalem"].unique())
        df_chart = df[df["Kalem"] == kalem_sec]
        fig = px.line(df_chart, x="Dönem", y="Değer", color="Taraf", title=f"{kalem_sec} Trendi", markers=True)
        fig.update_yaxes(tickformat=",")
        st.plotly_chart(fig, use_container_width=True)

    # 2. SENARYO
    with tab2:
        c1, c2 = st.columns([1, 2])
        with c1:
            t_sim = st.selectbox("Taraf:", df["Taraf"].unique())
            k_sim = st.selectbox("Kalem:", df["Kalem"].unique())
            artis = st.slider("Değişim (%)", -50, 50, 10)
        with c2:
            row = df[(df["Taraf"] == t_sim) & (df["Kalem"] == k_sim) & (df["TarihObj"] == df["TarihObj"].max())]
            if not row.empty:
                val = row.iloc[0]["Değer"]
                new_val = val * (1 + artis / 100)
                st.metric("Yeni Değer", f"{new_val:,.0f}", f"{new_val-val:,.0f}")

    # 3. EXCEL VE TABLO (BURASI DÜZELTİLDİ)
    with tab3:
        st.markdown("#### 📑 Excel İndir (Yan Yana Karşılaştırmalı)")
        
        # Ekran görüntüsü için basit pivot
        st.markdown("**Önizleme (İlk Veri Kalemi İçin):**")
        first_kalem = df["Kalem"].unique()[0]
        preview_df = df[df["Kalem"] == first_kalem].pivot_table(index=["TarihObj", "Dönem"], columns="Taraf", values="Değer").reset_index().sort_values("TarihObj").drop(columns=["TarihObj"])
        st.dataframe(preview_df.style.format("{:,.0f}"))

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            num_format = workbook.add_format({'num_format': '#,##0'}) # Binlik ayracı formatı
            
            for kalem in df["Kalem"].unique():
                # Her kalem için veriyi al
                sub = df[df["Kalem"] == kalem].copy()
                
                # --- PIVOT İŞLEMİ (YAN YANA GETİRME) ---
                # Satırlar: Dönem, Sütunlar: Taraf (Sektör, Kamu vs.), Değerler: Sayılar
                pivot_table = sub.pivot_table(index=["TarihObj", "Dönem"], columns="Taraf", values="Değer")
                
                # İndeksi düzelt ve tarihe göre sırala
                pivot_table = pivot_table.sort_index(level="TarihObj").reset_index()
                
                # Excel'de TarihObj (sıralama için kullandığımız tarih nesnesi) görünmesin
                pivot_table = pivot_table.drop(columns=["TarihObj"])
                
                # Sütun isimlerini temizle
                pivot_table.columns.name = None
                
                # Sayfa ismi (Excel kısıtlaması max 31 karakter)
                sheet_name = kalem[:30].replace("/", "-").replace(":", "")
                
                # Excel'e yaz
                pivot_table.to_excel(writer, index=False, sheet_name=sheet_name)
                
                # Sütun Genişlikleri ve Format
                worksheet = writer.sheets[sheet_name]
                for i, col in enumerate(pivot_table.columns):
                    width = max(pivot_table[col].astype(str).map(len).max(), len(str(col))) + 2
                    if i > 0: # Dönem hariç diğerleri sayı
                        worksheet.set_column(i, i, width, num_format)
                    else:
                        worksheet.set_column(i, i, width)

        st.download_button("💾 Excel Raporunu İndir", buffer.getvalue(), "bddk_analiz_yan_yana.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 4. ANALİZ BOTU
    with tab4:
        st.info("İstatistiksel Analiz")
        b_k = st.selectbox("Analiz:", df["Kalem"].unique(), key="bot_k")
        b_t = st.selectbox("Taraf:", df["Taraf"].unique(), key="bot_t")
        if st.button("Analiz Et"):
            d = df[(df["Kalem"]==b_k) & (df["Taraf"]==b_t)].sort_values("TarihObj")
            if not d.empty:
                val0, val1 = d.iloc[0]["Değer"], d.iloc[-1]["Değer"]
                degisim = ((val1-val0)/val0)*100
                st.markdown(f"""<div class="bot-card"><div class="bot-title">Trend</div><div class="bot-value">%{degisim:.1f}</div></div>""", unsafe_allow_html=True)
                
                cv = (d["Değer"].std() / d["Değer"].mean()) * 100
                st.markdown(f"**Volatilite (Risk):** %{cv:.1f}")
