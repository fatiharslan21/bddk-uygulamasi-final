import streamlit as st
import pandas as pd
import numpy as np  # İstatistiksel hesaplar için eklendi
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

    /* BUTON TASARIMI */
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

    /* KART TASARIMI (BOT İÇİN) */
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
AY_LISTESI = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım",
              "Aralık"]
TARAF_SECENEKLERI = ["Sektör", "Mevduat-Kamu"]

VERI_KONFIGURASYONU = {
    "📌 Toplam Aktifler": {"tab": "tabloListesiItem-1", "row_text": "TOPLAM AKTİFLER", "col_id": "grdRapor_Toplam"},

    "📌 Toplam Özkaynaklar": {"tab": "tabloListesiItem-1", "row_text": "TOPLAM ÖZKAYNAKLAR",
                             "col_id": "grdRapor_Toplam"},

    "💰 Dönem Net Kârı": {"tab": "tabloListesiItem-2", "row_text": "DÖNEM NET KARI (ZARARI)",
                          "col_id": "grdRapor_Toplam"},

    "📊 Sermaye Yeterliliği Rasyosu": {"tab": "tabloListesiItem-12", "row_text": "Sermaye Yeterliliği Standart Rasyosu",
                                     "col_id": "grdRapor_Toplam"},

    "🏦 Toplam Krediler": {"tab": "tabloListesiItem-3", "row_text": "Toplam Krediler", "col_id": "grdRapor_Toplam"},

    "⚠️ Takipteki Alacaklar": {"tab": "tabloListesiItem-1", "row_text": "Takipteki Alacaklar",
                               "col_id": "grdRapor_Toplam"},

    "💳 Bireysel Kredi Kartları": {"tab": "tabloListesiItem-4", "row_text": "Bireysel Kredi Kartları (10+11)",
                                  "col_id": "grdRapor_Toplam"},

    "🏠 Tüketici Kredileri": {"tab": "tabloListesiItem-4", "row_text": "Tüketici Kredileri (2+3+4)",
                             "col_id": "grdRapor_Toplam"},

    "⚠️ Toplam Takipteki Bireysel Krediler": {"tab": "tabloListesiItem-4", "row_text": "Toplam - Takipteki Tük. Krd. ve Takipteki Bireysel Kredi Kartları (13+17)",
                                  "col_id": "grdRapor_Toplam"},

    "🏠 Ticari Krediler": {"tab": "tabloListesiItem-4", "row_text": "Toplam - Taksitli Tic. Krd.(Dövize End. Dahil) ve Kurumsal Kredi Kartları (19+23+27)",
                             "col_id": "grdRapor_Toplam"},

    "🏭 KOBİ Kredileri": {"tab": "tabloListesiItem-6", "row_text": "Toplam KOBİ Kredileri",
                          "col_id": "grdRapor_NakdiKrediToplam"},

    "⚠️ Toplam Takipteki Ticari Krediler": {"tab": "tabloListesiItem-4", "row_text": "Takipteki Taksitli Tic.  Krd. ve Kurumsal Kredi Kartları Toplamı (31+35)",
                                                             "col_id": "grdRapor_Toplam"},
}


# --- 3. DRIVER YÖNETİMİ ---
def get_driver():
    # Linux / Sunucu Ortamı
    if sys.platform == "linux":
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        # Resimleri engelle (Firefox)
        options.set_preference('permissions.default.image', 2)
        options.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
        try:
            service = FirefoxService(GeckoDriverManager().install())
            return webdriver.Firefox(service=service, options=options)
        except Exception as e:
            st.error(f"Firefox Driver Başlatılamadı: {e}")
            return None
    # Windows / Local Ortam
    else:
        options = ChromeOptions()
        options.add_argument("--headless=new")  # Arka planda çalıştır
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        # HIZLANDIRMA AYARLARI (Gereksizleri Yükleme)
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Resimleri kapat
            "profile.default_content_setting_values.notifications": 2,  # Bildirimleri kapat
            "profile.managed_default_content_settings.stylesheets": 2,
            # CSS'i azalt (Opsiyonel, bazen yapıyı bozabilir, riskliyse bu satırı sil)
            "profile.managed_default_content_settings.cookies": 2,
            "profile.managed_default_content_settings.javascript": 1,  # JS mecburen açık kalmalı
            "profile.managed_default_content_settings.plugins": 1,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)

        try:
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            st.error(f"Chrome Driver Başlatılamadı: {e}")
            return None


# --- 4. VERİ ÇEKME MOTORU ---
def scrape_bddk_data(bas_yil, bas_ay, bit_yil, bit_ay, secilen_taraflar, secilen_veriler, status_text_obj,
                     progress_bar_obj):
    driver = None
    data = []

    try:
        driver = get_driver()
        if not driver:
            return pd.DataFrame()

        # Sayfa yükleme zaman aşımı
        driver.set_page_load_timeout(60)
        driver.get("https://www.bddk.org.tr/bultenaylik")

        # İlk açılışta yıl dropdown'ının gelmesini bekle
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "ddlYil")))

        bas_idx = AY_LISTESI.index(bas_ay)
        bit_idx = AY_LISTESI.index(bit_ay)

        total_steps = (bit_yil - bas_yil) * 12 + (bit_idx - bas_idx) + 1
        current_step = 0

        # --- OPTİMİZASYON: VERİLERİ SEKME (TAB) BAZINDA GRUPLA ---
        # Aynı sekmedeki veriler için sayfayı tekrar tekrar tıklamayalım.
        veriler_by_tab = {}
        for veri in secilen_veriler:
            tab_id = VERI_KONFIGURASYONU[veri]['tab']
            if tab_id not in veriler_by_tab:
                veriler_by_tab[tab_id] = []
            veriler_by_tab[tab_id].append(veri)

        for yil in range(bas_yil, bit_yil + 1):
            s_m = bas_idx if yil == bas_yil else 0
            e_m = bit_idx if yil == bit_yil else 11

            for ay_i in range(s_m, e_m + 1):
                ay_str = AY_LISTESI[ay_i]
                donem = f"{ay_str} {yil}"

                if status_text_obj:
                    status_text_obj.info(f"⏳ **İşleniyor:** {donem}")

                try:
                    # YIL SEÇİMİ
                    driver.execute_script("document.getElementById('ddlYil').style.display = 'block';")
                    sel_yil = Select(driver.find_element(By.ID, "ddlYil"))
                    sel_yil.select_by_visible_text(str(yil))
                    # JS ile change event tetikle (daha hızlı ve güvenli)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))",
                                          driver.find_element(By.ID, "ddlYil"))

                    # Dinamik bekleme: Ay dropdown'ı güncellenene kadar bekle
                    time.sleep(1)  # BDDK sunucusu bazen geç yanıt verir, kısa bir sleep güvenlidir

                    # AY SEÇİMİ
                    driver.execute_script("document.getElementById('ddlAy').style.display = 'block';")
                    sel_ay_elem = driver.find_element(By.ID, "ddlAy")
                    sel_ay = Select(sel_ay_elem)
                    sel_ay.select_by_visible_text(ay_str)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", sel_ay_elem)

                    time.sleep(1)

                    for taraf in secilen_taraflar:
                        # TARAF SEÇİMİ
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
                        time.sleep(1)  # Tablonun yüklenmesi için kısa bekleme

                        # --- OPTİMİZE EDİLMİŞ VERİ ÇEKME DÖNGÜSÜ ---
                        # Her bir veri için değil, her bir SEKME (TAB) için döngü kuruyoruz.

                        for tab_id, veri_listesi in veriler_by_tab.items():
                            # 1. İlgili sekmeye tıkla (Eğer birden fazla veri aynı sekmedeyse sadece 1 kere tıklar)
                            try:
                                target_tab = wait.until(EC.element_to_be_clickable((By.ID, tab_id)))
                                driver.execute_script("arguments[0].click();", target_tab)
                                time.sleep(0.5)  # Sekme geçiş animasyonu için minik bekleme
                            except Exception as e:
                                # Sekme bulunamazsa (o dönemde veri yoksa) bu grubu atla
                                continue

                            # 2. Sayfa kaynağını TEK SEFERDE al
                            soup = BeautifulSoup(driver.page_source, 'html.parser')

                            # 3. O sekmedeki tüm istenen verileri bu kaynaktan parse et
                            for veri in veri_listesi:
                                conf = VERI_KONFIGURASYONU[veri]

                                # Grup (Sektör/Kamu) algılama
                                current_group = None
                                for row in soup.find_all("tr"):
                                    group_cell = row.find("td", colspan=True)
                                    if group_cell:
                                        text = group_cell.get_text(strip=True)
                                        if "Sektör" in text:
                                            current_group = "Sektör"
                                        elif "Kamu" in text:
                                            current_group = "Kamu"
                                        continue

                                    ad = row.find("td", {"aria-describedby": "grdRapor_Ad"})
                                    # Dikkat: col_id her veri için farklı olabilir ama aynı tab'dalar
                                    toplam = row.find("td", {"aria-describedby": conf['col_id']})

                                    if ad and toplam:
                                        row_taraf = current_group if current_group else taraf

                                        # "contains" mantığı ile eşleşme (daha esnek)
                                        if conf['row_text'] in ad.get_text(strip=True):
                                            raw_text = toplam.get_text(strip=True)
                                            clean_text = raw_text.replace('.', '').replace(',', '.')
                                            try:
                                                found_val = float(clean_text)
                                            except:
                                                found_val = 0.0

                                            data.append({
                                                "Dönem": donem,
                                                "Taraf": row_taraf,
                                                "Kalem": veri,
                                                "Değer": found_val,
                                                "TarihObj": pd.to_datetime(f"{yil}-{ay_i + 1}-01")
                                            })
                                            # Veriyi bulduk, bu satırı işlemeyi bırak diğer veriye geç
                                            # (Bir tabloda aynı isimde tek satır olduğunu varsayıyoruz)
                                            # break # Break kullanmıyoruz çünkü alt kalemler olabilir
                except Exception as e:
                    # Hata durumunda log basılabilir ama akışı bozmasın
                    pass

                current_step += 1
                if progress_bar_obj:
                    progress_bar_obj.progress(min(current_step / max(1, total_steps), 1.0))

    except Exception as e:
        st.error(f"Kritik Hata: {e}")
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
    secilen_taraflar = st.multiselect("Karşılaştır:", TARAF_SECENEKLERI, default=["Sektör"], key="sb_taraflar")
    secilen_veriler = st.multiselect("Veri:", list(VERI_KONFIGURASYONU.keys()), default=["📌 Toplam Aktifler"],
                                     key="sb_veriler")
    st.markdown("---")
    st.markdown("### 🚀 İŞLEM MERKEZİ")
    btn = st.button("ANALİZİ BAŞLAT", key="sb_btn_baslat")

st.title("🏦 BDDK Analiz Botu")

if 'df_sonuc' not in st.session_state:
    st.session_state['df_sonuc'] = None

if btn:
    if not secilen_taraflar or not secilen_veriler:
        st.warning("Lütfen en az bir Taraf ve bir Veri kalemi seçin.")
    else:
        status_txt = st.empty()
        status_txt.info("🌐 BDDK'ya bağlanılıyor, lütfen bekleyiniz...")
        my_bar = st.progress(0)
        df = scrape_bddk_data(bas_yil, bas_ay, bit_yil, bit_ay, secilen_taraflar, secilen_veriler, status_txt, my_bar)
        my_bar.empty()
        status_txt.empty()

        if not df.empty:
            st.session_state['df_sonuc'] = df
            st.success("✅ Veriler Başarıyla Çekildi!")
            st.balloons()
            time.sleep(1)
            st.rerun()
        else:
            st.error("Veri bulunamadı.")

# --- DASHBOARD ---
if st.session_state['df_sonuc'] is not None:
    df = st.session_state['df_sonuc']
    df = df.drop_duplicates(subset=["Dönem", "Taraf", "Kalem"])
    df = df.sort_values("TarihObj")

    # 4 SEKMELİ ŞOV ALANI
    tab1, tab2, tab3, tab4 = st.tabs([
        "📉 Trend Analizi",
        "🧪 Senaryo",
        "📑 Veri Tablosu & Excel",
        "🧠 Akıllı Analiz Botu 2.0"
    ])

    # 1. SEKME: TREND (KLASİK)
    with tab1:
        kalem_sec = st.selectbox("Grafik Kalemi:", df["Kalem"].unique(), key="trend_select")
        df_chart = df[df["Kalem"] == kalem_sec].copy().sort_values("TarihObj")
        fig = px.line(df_chart, x="Dönem", y="Değer", color="Taraf", title=f"📅 {kalem_sec} Gelişimi", markers=True,
                      color_discrete_sequence=px.colors.qualitative.Bold)
        fig.update_xaxes(categoryorder='array', categoryarray=df_chart["Dönem"].unique())
        fig.update_yaxes(tickformat=",")
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True, key="trend_chart")


    # 2. SEKME: SENARYO
    with tab2:
        st.markdown("#### 🧪 What-If Analizi")
        c_sim1, c_sim2 = st.columns([1, 2])
        with c_sim1:
            taraf_sim = st.selectbox("Taraf:", df["Taraf"].unique(), key="sim_taraf")
            kalem_sim = st.selectbox("Kalem:", df["Kalem"].unique(), key="sim_kalem")
            artis_orani = st.slider("Değişim (%)", -50, 50, 10, 5, key="sim_slider")
        with c_sim2:
            base_row = df[
                (df["Taraf"] == taraf_sim) & (df["Kalem"] == kalem_sim) & (df["TarihObj"] == df["TarihObj"].max())]
            if not base_row.empty:
                mevcut = base_row.iloc[0]["Değer"]
                yeni = mevcut * (1 + artis_orani / 100)
                fark = yeni - mevcut

                # Görsel Kartlar
                c_k1, c_k2, c_k3 = st.columns(3)
                c_k1.metric("Mevcut", f"{mevcut:,.0f}")
                c_k2.metric("Senaryo", f"{yeni:,.0f}", f"{fark:,.0f}")

                # Basit Bar
                sim_df = pd.DataFrame({"Durum": ["Mevcut", "Senaryo"], "Değer": [mevcut, yeni]})
                fig_sim = px.bar(sim_df, x="Durum", y="Değer", color="Durum", text_auto='.2s',
                                 color_discrete_map={"Mevcut": "gray", "Senaryo": "orange"})
                fig_sim.update_layout(height=250, showlegend=False)
                st.plotly_chart(fig_sim, use_container_width=True)

    # 3. SEKME: TABLO & EXCEL (GÜNCELLENDİ)
    with tab3:
        st.markdown("#### 📑 Ham Veri ve Excel İndirme")
        
        # Ekrana basılan tablo (Formatlı)
        df_display = df.sort_values(["TarihObj", "Kalem", "Taraf"])[["Dönem", "Kalem", "Taraf", "Değer"]]
        df_display_fmt = df_display.copy()
        df_display_fmt["Değer"] = df_display_fmt["Değer"].apply(lambda x: "{:,.0f}".format(x).replace(",", "."))
        st.dataframe(df_display_fmt, use_container_width=True)

        buffer = io.BytesIO()
        # xlsxwriter motorunu kullanarak formatlama yapacağız
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            # Excel'de binlik ayracı (nokta) formatı: #,##0
            num_format = workbook.add_format({'num_format': '#,##0'})
            
            for kalem in df["Kalem"].unique():
                # İlgili kalemi filtrele
                sub = df[df["Kalem"] == kalem].copy()
                
                # --- PIVOT İŞLEMİ (YAN YANA YAZDIRMA) ---
                # Index: TarihObj, Dönem | Kolonlar: Taraf | Değerler: Değer
                sub_pivot = sub.pivot_table(index=["TarihObj", "Dönem"], columns="Taraf", values="Değer")
                
                # İndeksi sıfırla ve TarihObj'ye göre sıralayıp onu at (Excel'de görünmesin diye)
                sub_pivot = sub_pivot.sort_values("TarihObj").reset_index()
                sub_pivot = sub_pivot.drop(columns=["TarihObj"])
                
                # Kolon isimlerini temizle (Pivot sonrası 'Taraf' ismi kalabilir)
                sub_pivot.columns.name = None
                
                # Sheet adı oluştur (Excel max 31 karakter kabul eder)
                sheet_name = kalem[:30].replace("/", "-")
                
                # Excel'e yaz (Index'i yazma)
                sub_pivot.to_excel(writer, index=False, sheet_name=sheet_name)
                
                # --- FORMATLAMA KISMI ---
                worksheet = writer.sheets[sheet_name]
                
                # Sütunları döngüye alıp genişlet ve formatla
                for idx, col in enumerate(sub_pivot.columns):
                    # Genişlik ayarla (20 birim)
                    # "Dönem" sütunu (idx=0) hariç diğerlerine sayı formatı uygula
                    if idx > 0: 
                        worksheet.set_column(idx, idx, 20, num_format)
                    else:
                        worksheet.set_column(idx, idx, 15)

        st.download_button("💾 Excel İndir (Yan Yana & Formatlı)", buffer.getvalue(), "bddk_analiz_yan_yana.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_btn")

    # 4. SEKME: AKILLI ANALİZ BOTU 2.0 (ŞOV KISMI)
    with tab4:
        st.markdown("#### 🧠 Akıllı Analiz Botu 2.0")
        st.info("Verileri istatistiksel olarak inceler, riskleri ve fırsatları matematiksel olarak bulur.")

        bot_kalem = st.selectbox("Analiz Edilecek Veri:", df["Kalem"].unique(), key="bot_select")
        bot_taraf = st.selectbox("Odaklanılacak Taraf:", df["Taraf"].unique(), key="bot_taraf_select")

        if st.button("Analizi Çalıştır", key="run_bot"):
            with st.spinner("Bot verileri tarıyor, istatistikleri hesaplıyor..."):
                time.sleep(1)  # Şov efekti

                # Veri Hazırlığı
                df_bot = df[(df["Kalem"] == bot_kalem) & (df["Taraf"] == bot_taraf)].sort_values("TarihObj")

                if not df_bot.empty:
                    son_deger = df_bot.iloc[-1]["Değer"]
                    ilk_deger = df_bot.iloc[0]["Değer"]
                    ortalama = df_bot["Değer"].mean()
                    std_sapma = df_bot["Değer"].std()

                    # 1. BÜYÜME KARTI
                    toplam_buyume = ((son_deger - ilk_deger) / ilk_deger) * 100
                    trend_icon = "🚀" if toplam_buyume > 0 else "📉"

                    st.markdown(f"""
                    <div class="bot-card">
                        <div class="bot-title">📊 Genel Trend Analizi</div>
                        <div class="bot-value">{trend_icon} %{toplam_buyume:.1f} Değişim</div>
                        <p>Seçilen dönem aralığında <b>{bot_taraf}</b> tarafında <b>{bot_kalem}</b> verisi {ilk_deger:,.0f} seviyesinden {son_deger:,.0f} seviyesine gelmiştir.</p>
                    </div>
                    """, unsafe_allow_html=True)

                    c_bot1, c_bot2 = st.columns(2)

                    # 2. RİSK / VOLATİLİTE ANALİZİ (Z-Score)
                    with c_bot1:
                        st.markdown("##### ⚠️ Risk ve Stabilite")
                        # Varyasyon katsayısı (CV) = Std Sapma / Ortalama
                        cv = (std_sapma / ortalama) * 100 if ortalama != 0 else 0

                        risk_renk = "green"
                        risk_yorum = "Düşük (Stabil)"
                        if cv > 20:
                            risk_renk = "red"
                            risk_yorum = "Yüksek (Dalgalı)"
                        elif cv > 10:
                            risk_renk = "orange"
                            risk_yorum = "Orta (Normal)"

                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=cv,
                            title={'text': "Volatilite (Risk) Skoru"},
                            gauge={'axis': {'range': [0, 50]},
                                   'bar': {'color': risk_renk},
                                   'steps': [
                                       {'range': [0, 10], 'color': "#e6fffa"},
                                       {'range': [10, 20], 'color': "#fffaf0"},
                                       {'range': [20, 50], 'color': "#fff5f5"}],
                                   'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75,
                                                 'value': 40}}))
                        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        st.caption(f"Veri hareketliliği (CV): %{cv:.1f} - Durum: **{risk_yorum}**")

                    # 3. GELECEK TAHMİNİ (Basit Projeksiyon)
                    with c_bot2:
                        st.markdown("##### 🔮 Gelecek Ay Tahmini")
                        # Ortalama aylık büyüme hızını bul
                        df_bot["degisim"] = df_bot["Değer"].pct_change()
                        avg_growth = df_bot["degisim"].mean()

                        gelecek_tahmin = son_deger * (1 + avg_growth)
                        fark_tahmin = gelecek_tahmin - son_deger

                        st.metric(label="Önümüzdeki Ay Beklentisi",
                                  value=f"{gelecek_tahmin:,.0f}",
                                  delta=f"{fark_tahmin:,.0f} (Tahmini Artış)")

                        st.markdown(f"""
                        <div style="background-color:#f0f2f6; padding:10px; border-radius:5px; font-size:12px;">
                        ℹ️ <b>Not:</b> Bu tahmin, geçmiş dönemlerin ortalama büyüme hızı (%{avg_growth * 100:.2f}) baz alınarak hesaplanmıştır. Kesinlik içermez.
                        </div>
                        """, unsafe_allow_html=True)

                    # 4. ANOMALİ KONTROLÜ
                    z_score = (son_deger - ortalama) / std_sapma if std_sapma != 0 else 0
                    if abs(z_score) > 2:
                        st.warning(
                            f"🚨 **DİKKAT:** Son ay verisi istatistiksel olarak normalden çok sapmış (Z-Skor: {z_score:.2f}). Olağandışı bir hareket var!")
                    else:
                        st.success(
                            f"✅ **DURUM NORMAL:** Son veri istatistiksel standartlar içinde (Z-Skor: {z_score:.2f}). Anormal bir sıçrama yok.")
