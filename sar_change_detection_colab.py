# %% [markdown]
# # 🛰️ SAR Tabanlı Yüzey Değişimi İzleme Prototipi (NASA Space Apps 2026)
# **Görev (Challenge):** Radar / Yangın Haritaları (NISAR, MODIS/VIIRS)
#
# Bu betik **3 farklı çalışma modunu** tek dosyada destekler:
# 1. **Otomatik NASA ASF İndirme Modu (`USE_ASF_AUTO_DOWNLOAD = True`):** Bilgisayarınıza dosya indirmeden, doğrudan Google Colab sunucusu üzerinden NASA Earthdata Token'ınız ve `asf_search` ile koordinat/tarih vererek aynı Burst ID'ye sahip **Önce** ve **Sonra** `_VV.tif` dosyalarını otomatik çeker.
# 2. **Manuel `.tif` Yükleme Modu:** İndirdiğiniz `sentinel1_before.tif` ve `sentinel1_after.tif` dosyalarını Colab sol paneline sürüklediğinizde otomatik okur.
# 3. **Anında Simülasyon / Demo Modu (Varsayılan):** Henüz `.tif` dosyanız yoksa bile sıfır hatayla çalışır, gerçekçi SAR benek gürültüsü üretir ve `change_detection_panel.png` çıktısını verir.

# %% [code]
# ADIM 0: Google Colab'da çalışıyorsanız aşağıdaki satırın başındaki '#' işaretini kaldırıp çalıştırın:
# !pip install -q asf_search rasterio scipy matplotlib numpy

import os
import glob
import shutil
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter

try:
    import rasterio
    from rasterio.windows import Window
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    print("Bilgi: 'rasterio' kurulu değil. Colab'da üstteki '!pip install ...' satırını çalıştırın.")

try:
    import asf_search as asf
    HAS_ASF = True
except ImportError:
    HAS_ASF = False


# %% [code]
# ==============================================================================
# 1. PARAMETRELER VE NASA ASF OTOMATİK İNDİRME AYARLARI
# ==============================================================================
# Doğrudan Colab içinde NASA ASF'den otomatik veri çekmek için True yapın:
USE_ASF_AUTO_DOWNLOAD = False

# urs.earthdata.nasa.gov -> "Generate Token" menüsünden aldığınız Token'ı buraya yapıştırın:
EARTHDATA_TOKEN = "BURAYA_EARTHDATA_TOKEN_YAPISTIRIN"

# Aranacak Bölge Koordinatı (Örnek: Atatürk Barajı kıyısı / Tuz Gölü / Meriç Nehri) ve Tarih Aralığı
TARGET_LON = 38.45          # Boylam (Longitude - Örn: Atatürk Barajı kıyısı)
TARGET_LAT = 37.55          # Enlem (Latitude)
START_DATE = "2024-05-01"   # Başlangıç Tarihi (YYYY-AA-GG)
END_DATE   = "2024-09-30"   # Bitiş Tarihi (YYYY-AA-GG)

BEFORE_TIF_PATH = "sentinel1_before.tif"   # Önceki tarihli SAR görüntüsü (.tif)
AFTER_TIF_PATH  = "sentinel1_after.tif"    # Sonraki tarihli SAR görüntüsü (.tif)

# 5 km x 5 km'lik küçük ilgi alanı (AOI) penceresi (Piksel koordinatları)
AOI_COL_OFF = 500    # Başlangıç X pikseli
AOI_ROW_OFF = 500    # Başlangıç Y pikseli
AOI_WIDTH   = 500    # Pencere genişliği (piksel)
AOI_HEIGHT  = 500    # Pencere yüksekliği (piksel)

PIXEL_SIZE_METERS = 10.0  # Piksel başına metre (Alan hesabı için)
FILTER_SIZE       = 5     # Benek gürültüsü filtre penceresi (5x5)
THRESHOLD_DB      = 3.0   # Değişim eşiği (±3.0 dB = güçte 2 kat değişim)
OUTPUT_IMAGE_PATH = "change_detection_panel.png"


# %% [code]
# ==============================================================================
# 2. NASA ASF VERTEX OTOMATİK VERİ ARAMA VE İNDİRME FONKSİYONU (asf_search)
# ==============================================================================
def download_opera_rtc_pair_from_asf(lon, lat, start_date, end_date, token):
    """
    ASF Vertex üzerinden verilen koordinat ve tarih aralığındaki OPERA-S1 RTC
    ürünlerini arar, aynı Burst ID'ye (birebir aynı piksel hizasına) sahip en eski
    ve en yeni iki görüntünün '_VV.tif' bantlarını doğrudan Colab'a indirir.
    """
    if not HAS_ASF:
        raise RuntimeError("Lütfen önce '!pip install asf_search' komutunu çalıştırın.")

    wkt_point = f"POINT({lon} {lat})"
    print(f"NASA ASF üzerinde OPERA-S1 RTC aranıyor: {wkt_point} ({start_date} -> {end_date})...")

    results = asf.geo_search(
        intersectsWith=wkt_point,
        dataset=asf.DATASET.OPERA_S1,
        processingLevel=asf.PRODUCT_TYPE.RTC,
        start=f"{start_date}T00:00:00Z",
        end=f"{end_date}T23:59:59Z",
    )

    if len(results) < 2:
        raise ValueError("Bu tarih aralığında yeterli OPERA-S1 RTC görüntüsü bulunamadı. Tarih aralığını genişletin.")

    # Aynı Burst ID'ye sahip görüntüleri grupla (üst üste tam oturması için)
    burst_groups = {}
    for item in results:
        props = item.properties
        burst_id = props.get("operaBurstID") or props.get("burstId") or props.get("pathNumber", "default")
        burst_groups.setdefault(burst_id, []).append(item)

    # En çok görüntü içeren Burst grubunu seç ve tarihe göre sırala
    best_burst, group = max(burst_groups.items(), key=lambda kv: len(kv[1]))
    group_sorted = sorted(group, key=lambda x: x.properties.get("startTime", ""))

    before_item = group_sorted[0]
    after_item  = group_sorted[-1]
    print(f"Eşleşen Burst ID: {best_burst}")
    print(f"  -> Önceki Görüntü : {before_item.properties.get('sceneName')} ({before_item.properties.get('startTime')})")
    print(f"  -> Sonraki Görüntü: {after_item.properties.get('sceneName')} ({after_item.properties.get('startTime')})")

    session = asf.ASFSession().auth_with_token(token)
    os.makedirs("asf_downloads", exist_ok=True)

    # Ürünlerin içindeki _VV.tif URL'lerini bul ve indir
    for item, target_name in [(before_item, BEFORE_TIF_PATH), (after_item, AFTER_TIF_PATH)]:
        urls = [u for u in item.properties.get("additionalUrls", []) + [item.properties.get("url", "")] if u.endswith("_VV.tif") or u.endswith(".tif")]
        if not urls:
            item.download(path="asf_downloads", session=session)
            tifs = sorted(glob.glob("asf_downloads/**/*.tif*", recursive=True))
            if tifs:
                shutil.copy(tifs[-1], target_name)
        else:
            tif_url = urls[0]
            print(f"İndiriliyor: {tif_url} -> {target_name}")
            asf.download_url(url=tif_url, path="asf_downloads", filename=target_name, session=session)
            shutil.move(os.path.join("asf_downloads", target_name), target_name)

    print("Her iki .tif dosyası başarıyla Colab ortamına indirildi!")


# %% [code]
# ==============================================================================
# 3. GÖRÜNTÜ İŞLEME FONKSİYONLARI (Okuma, 5x5 Filtreleme, dB Log-Oran)
# ==============================================================================
def read_sar_aoi(path, col_off=0, row_off=0, width=500, height=500):
    """GeoTIFF (.tif) dosyasından sadece seçilen 500x500 piksellik küçük AOI penceresini okur."""
    with rasterio.open(path) as src:
        c_off = min(col_off, max(0, src.width - width))
        r_off = min(row_off, max(0, src.height - height))
        w = min(width, src.width - c_off)
        h = min(height, src.height - r_off)
        window = Window(c_off, r_off, w, h)
        band = src.read(1, window=window).astype(np.float32)
        res_m = abs(src.transform.a) if src.transform and src.transform.a > 0 else PIXEL_SIZE_METERS

    band[band <= 0] = np.nan
    return band, res_m


def generate_demo_sar_pair(height=500, width=500, seed=42):
    """Dosya yokken gerçekçi SAR benek gürültüsü ve yüzey değişimi içeren demo veri üretir."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:height, 0:width]
    base_reflectivity = 0.12 + 0.04 * np.sin(x / 45.0) * np.cos(y / 45.0)

    river_mask = np.abs(y - (250 + 60 * np.sin(x / 70.0))) < 18
    base_reflectivity[river_mask] = 0.025

    speckle_before = rng.gamma(shape=4.0, scale=0.25, size=(height, width))
    speckle_after  = rng.gamma(shape=4.0, scale=0.25, size=(height, width))
    before = (base_reflectivity * speckle_before).astype(np.float32)

    after_reflectivity = base_reflectivity.copy()
    flood_mask = (np.abs(y - (250 + 60 * np.sin(x / 70.0))) < 52) & (x > 110) & (x < 390)
    after_reflectivity[flood_mask] = 0.022

    urban_mask = ((x - 360)**2 + (y - 120)**2 < 38**2) | ((x > 80) & (x < 155) & (y > 350) & (y < 420))
    after_reflectivity[urban_mask] = 0.42

    after = (after_reflectivity * speckle_after).astype(np.float32)
    return before, after, PIXEL_SIZE_METERS


def lee_or_mean_speckle_filter(band, size=5):
    """NaN değerlerine dayanıklı 5x5 uzamsal benek gürültüsü (speckle) filtresi."""
    valid_mask = np.isfinite(band).astype(np.float32)
    filled = np.where(np.isfinite(band), band, 0.0)
    num = uniform_filter(filled, size=size, mode="nearest")
    den = uniform_filter(valid_mask, size=size, mode="nearest")
    return np.where(den > 0, num / (den + 1e-6), np.nan)


def to_db(band):
    """Doğrusal radar yoğunluğunu desibel (dB) ölçeğine dönüştürür."""
    return 10.0 * np.log10(np.maximum(band, 1e-6))


# %% [code]
# ==============================================================================
# 4. ANA İŞ AKIŞI (Otomatik İndirme / Okuma -> Filtreleme -> Log-Oran -> Eşikleme)
# ==============================================================================
if USE_ASF_AUTO_DOWNLOAD and EARTHDATA_TOKEN != "BURAYA_EARTHDATA_TOKEN_YAPISTIRIN":
    download_opera_rtc_pair_from_asf(
        TARGET_LON, TARGET_LAT, START_DATE, END_DATE, EARTHDATA_TOKEN
    )

if os.path.exists(BEFORE_TIF_PATH) and os.path.exists(AFTER_TIF_PATH) and HAS_RASTERIO:
    print(f"Gerçek SAR dosyaları okunuyor: {BEFORE_TIF_PATH} ve {AFTER_TIF_PATH}")
    before_raw, pixel_res = read_sar_aoi(
        BEFORE_TIF_PATH, AOI_COL_OFF, AOI_ROW_OFF, AOI_WIDTH, AOI_HEIGHT
    )
    after_raw, _ = read_sar_aoi(
        AFTER_TIF_PATH, AOI_COL_OFF, AOI_ROW_OFF, AOI_WIDTH, AOI_HEIGHT
    )
    data_mode_label = "Sentinel-1 OPERA RTC / NISAR GeoTIFF"
else:
    print("Bilgi: .tif dosyaları bulunamadı, demo/test modu (sentetik SAR çifti) çalıştırılıyor...")
    before_raw, after_raw, pixel_res = generate_demo_sar_pair(AOI_HEIGHT, AOI_WIDTH)
    data_mode_label = "Sentinel-1 RTC Simülasyon (5x5 km AOI)"

# Adım 2: Benek Gürültüsü Filtreleme (5x5 pencere)
before_f = lee_or_mean_speckle_filter(before_raw, size=FILTER_SIZE)
after_f  = lee_or_mean_speckle_filter(after_raw, size=FILTER_SIZE)

# Adım 3: Desibel (dB) Dönüşümü ve Log-Oran Hesabı
before_db = to_db(before_f)
after_db  = to_db(after_f)
log_ratio = after_db - before_db

# Adım 4: ±3 dB Eşikleme ve Değişim Haritası
change_map = np.zeros_like(log_ratio, dtype=np.int8)
change_map[log_ratio > THRESHOLD_DB]  = 1   # Pozitif değişim (Parlama: Yeni yapı / pürüzlülük)
change_map[log_ratio < -THRESHOLD_DB] = -1  # Negatif değişim (Kararma: Su baskını / hasat)

# İstatistik ve Alan (km²) Hesabı
total_pixels = np.isfinite(log_ratio).sum()
pos_pixels   = int((change_map == 1).sum())
neg_pixels   = int((change_map == -1).sum())
changed_pixels = pos_pixels + neg_pixels
changed_pct  = (changed_pixels / max(total_pixels, 1)) * 100.0

pixel_area_km2 = (pixel_res * pixel_res) / 1e6
pos_area_km2   = pos_pixels * pixel_area_km2
neg_area_km2   = neg_pixels * pixel_area_km2
total_changed_km2 = changed_pixels * pixel_area_km2

print("-" * 65)
print(f"ANALİZ ÖZETİ ({data_mode_label})")
print(f"Toplam İncelenen Piksel : {total_pixels:,} piksel ({total_pixels * pixel_area_km2:.2f} km²)")
print(f"Pozitif Değişim (>+{THRESHOLD_DB:.1f} dB): {pos_pixels:,} piksel ({pos_area_km2:.2f} km² - Yeni Yapı/Pürüzlülük)")
print(f"Negatif Değişim (<-{THRESHOLD_DB:.1f} dB): {neg_pixels:,} piksel ({neg_area_km2:.2f} km² - Su Baskını/Kaybı)")
print(f"Toplam Değişen Alan     : {changed_pixels:,} piksel ({total_changed_km2:.2f} km² | %{changed_pct:.1f})")
print("-" * 65)


# %% [code]
# ==============================================================================
# 5. GÖRSELLEŞTİRME (2x2 Jüri ve Sunum Paneli)
# ==============================================================================
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 10.5
})

fig, axes = plt.subplots(2, 2, figsize=(13, 10.5))
fig.suptitle(
    f"SAR Tabanlı Yüzey Değişimi Tespiti | Eşik: ±{THRESHOLD_DB:.1f} dB | "
    f"Değişen Alan: {total_changed_km2:.2f} km² (%{changed_pct:.1f})",
    fontsize=14, fontweight="bold", y=0.98
)

im0 = axes[0, 0].imshow(before_db, cmap="gray", vmin=-20, vmax=0)
axes[0, 0].set_title("1. Önceki Tarih (5x5 Filtrelenmiş SAR - dB)", fontweight="bold")
axes[0, 0].set_xlabel("X Pikseli"); axes[0, 0].set_ylabel("Y Pikseli")
plt.colorbar(im0, ax=axes[0, 0], fraction=0.046, pad=0.04, label="Geri Saçılım (dB)")

im1 = axes[0, 1].imshow(after_db, cmap="gray", vmin=-20, vmax=0)
axes[0, 1].set_title("2. Sonraki Tarih (5x5 Filtrelenmiş SAR - dB)", fontweight="bold")
axes[0, 1].set_xlabel("X Pikseli"); axes[0, 1].set_ylabel("Y Pikseli")
plt.colorbar(im1, ax=axes[0, 1], fraction=0.046, pad=0.04, label="Geri Saçılım (dB)")

im2 = axes[1, 0].imshow(log_ratio, cmap="RdBu_r", vmin=-6, vmax=6)
axes[1, 0].set_title("3. Log-Oran Fark Haritası (Sonra dB - Önce dB)", fontweight="bold")
axes[1, 0].set_xlabel("X Pikseli"); axes[1, 0].set_ylabel("Y Pikseli")
plt.colorbar(im2, ax=axes[1, 0], fraction=0.046, pad=0.04, label="Fark (dB)")

im3 = axes[1, 1].imshow(change_map, cmap="coolwarm", vmin=-1, vmax=1)
axes[1, 1].set_title(
    f"4. Değişim Haritası (Mavi: -{neg_area_km2:.2f} km² | Kırmızı: +{pos_area_km2:.2f} km²)",
    fontweight="bold"
)
axes[1, 1].set_xlabel("X Pikseli"); axes[1, 1].set_ylabel("Y Pikseli")
cbar3 = plt.colorbar(im3, ax=axes[1, 1], ticks=[-1, 0, 1], fraction=0.046, pad=0.04)
cbar3.ax.set_yticklabels(["Negatif (<-3 dB)", "Değişim Yok", "Pozitif (>+3 dB)"])

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(OUTPUT_IMAGE_PATH, dpi=220)
print(f"Görsel panel başarıyla kaydedildi: {OUTPUT_IMAGE_PATH}")