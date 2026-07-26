# Akıllı Kozmetik ve Cilt Bakım Rutini Analizörü

Kullanıcının cilt bakım rutinindeki birden fazla ürünü (veritabanından seçerek
veya içindekiler listesini elle yapıştırarak) karşılaştıran, aktif bileşenler
arasındaki bilinen pH çakışmalarını ve dermatolojik uyumsuzlukları tespit eden,
ve sonucu bir yapay zeka (Google Gemini API veya yerel Foundry Local) ile
anlaşılır bir dille yorumlayan uçtan uca bir sistem.

## Özellikler

- **N ürünlü rutin analizi**: 2'den fazla ürünü aynı anda karşılaştırabilirsin
- **İki veri girişi yolu**: veritabanındaki (scraping ile toplanmış) ürünlerden
  seç, veya kutundaki ürünün içindekiler listesini elle yapıştır
- **19 bilinen aktif bileşen** (AHA/BHA asitleri, Retinol, C Vitamini,
  Niacinamide, Benzoyl Peroxide, Azelaic Acid, Bakuchiol vb.) ve aralarındaki
  **10 bilinen çakışma kuralı**
- **pH çakışma tespiti**: asitlerin tipik formülasyon pH aralıklarına göre
  çakışıp çakışmadığını hesaplar
- **Gerçek web scraping**: Playwright ile Rossmann/Trendyol/Gratis gibi
  sitelerden ürün içerik listelerini otomatik toplar
- **Güvenlik kontrollü LLM analizi**: "ne yapılmalı" (kullanım sırası önerisi)
  kısmı LLM'e bırakılmaz; bir güvenlik ağı, AI'nin önerisini kontrol edip
  yanlış yönde bir tavsiye ("ayırın" yerine "birlikte kullanın" gibi) asla
  kullanıcıya ulaşmaz

## Teknoloji Yığını

- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Backend**: Python, Flask
- **Veritabanı**: SQLite
- **Yapay Zeka**: Google Gemini API (varsayılan, ücretsiz katman) veya
  Foundry Local (yerel/offline alternatif, Phi-3.5-mini)
- **Veri toplama**: Python + Playwright (web scraping)

## Klasör Yapısı

```
kozmetik-analizor/
├── scraper/
│   ├── scrape_products.py         # Playwright scraper
│   ├── selectors_config.py        # Site bazlı CSS seçicileri
│   ├── urls.txt                   # Taranacak ürün linkleri
│   └── requirements.txt
├── data/
│   ├── active_ingredients_reference.json  # Bilinen aktif bileşenler + çakışma kuralları
│   └── products.xlsx              # Scraper çıktısı (git'e dahil değil)
├── backend/
│   ├── app.py                     # Flask API
│   ├── database.py                # SQLite katmanı
│   ├── ingredient_parser.py       # İçerik metninden bileşen tespiti + çakışma hesabı
│   ├── llm_client.py              # Gemini/Foundry Local istemcisi + güvenlik kontrolü
│   ├── llm_config.example.py      # LLM ayarları şablonu (kopyala → llm_config.py yap)
│   ├── foundry_config.example.py  # Foundry Local ayarları şablonu (opsiyonel)
│   ├── seed_test_data.py          # Veritabanını örnek ürünlerle doldurur
│   └── requirements.txt
└── frontend/
    ├── templates/index.html
    └── static/{css,js}
```

## Kurulum Adımları

### 1) LLM sağlayıcısını yapılandır

```bash
cd backend
cp llm_config.example.py llm_config.py
```

`llm_config.py`'yi aç, `GEMINI_API_KEY`'i doldur. Ücretsiz anahtar için:
https://aistudio.google.com/apikey (kredi kartı gerekmiyor).

`llm_config.py` `.gitignore`'da olduğu için bu dosya asla repo'ya
yüklenmez — API anahtarın güvende kalır.

**Yerel/offline çalıştırmak istersen** (daha düşük kalite ama internet
gerektirmez): `llm_config.py` içinde `LLM_PROVIDER = "foundry_local"` yap,
`cp foundry_config.example.py foundry_config.py` ile o dosyayı da doldur,
ve [Foundry Local](https://github.com/microsoft/Foundry-Local) kurup bir
model çalıştır (`foundry model run Phi-3.5-mini-instruct-generic-cpu:2`).

### 2) Backend'i kur ve çalıştır

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed_test_data.py   # veritabanını örnek ürünlerle doldurur (opsiyonel ama önerilir)
python app.py
```

Flask varsayılan olarak `http://localhost:5000` üzerinde çalışır.

### 3) Scraper'ı çalıştır (opsiyonel, gerçek ürün verisi eklemek için)

```bash
cd scraper
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install chromium
```

`urls.txt` dosyasına taramak istediğin ürün linklerini ekle (her satıra bir
tane), sonra:

```bash
python scrape_products.py --urls urls.txt --site rossmann --headless false
```

`--site` parametresi `trendyol`, `gratis` veya `rossmann` olabilir (her
sitenin HTML yapısı farklı olduğu için `selectors_config.py`'de ayrı ayrı
tanımlı). `--headless false` ile tarayıcı açık kalır, her sayfada Enter'a
basarak incelemene izin verir.

Bu, `data/products.xlsx` dosyasını üretir/günceller. Flask çalışırken, yeni
bir terminalde şunu çalıştırarak bu veriyi veritabanına aktarabilirsin:

```bash
# PowerShell:
Invoke-WebRequest -Uri http://localhost:5000/api/import-excel -Method POST
# Mac/Linux:
curl -X POST http://localhost:5000/api/import-excel
```

## Nasıl Çalışır (Mimari)

1. **Bileşen tespiti** (`ingredient_parser.py`): her ürünün içindekiler
   metninde bilinen 19 aktif bileşenden hangilerinin geçtiğini bulur.
2. **Çakışma hesabı**: her ürün çifti için iki tür çakışma kontrol edilir:
   - **pH çakışması**: iki asidin tipik pH aralıkları örtüşüyor mu?
   - **Bilinen çakışma**: Retinol+C Vitamini gibi, pH'tan bağımsız,
     literatürde bilinen riskli/güvenli ikililer
3. **LLM analizi** (`llm_client.py`):
   - **RİSK DEĞERLENDİRMESİ** (neden riskli/güvenli olduğu): Gemini
     kullanılıyorsa gerçekten LLM tarafından yazılır; Foundry Local gibi
     küçük bir model kullanılıyorsa güvenli, koddan üretilen açıklamaya
     düşülür (küçük modellerin birden fazla bulguyu karıştırma riski
     gözlemlendiği için).
   - **ÖNERİLEN KULLANIM SIRASI** (ne yapılmalı): Gemini kullanıcıya özel
     bir öneri yazar, ama bu öneri bir **güvenlik kontrolünden** geçer -
     gerçek bir risk varken cevapta bir "ayırma" ifadesi yoksa, bu şüpheli
     kabul edilip güvenli/deterministik metne otomatik düşülür. Böylece
     LLM'in yanlış yönde bir tavsiye vermesi kullanıcıya asla ulaşmaz.

## Önemli Yasal/Etik Not

- Scraping yaparken hedef sitenin `robots.txt` ve kullanım koşullarına uy,
  istekler arasına makul bekleme süreleri koy, siteyi aşırı yüklemeyecek
  şekilde çalıştır. Bu proje yalnızca kişisel/eğitim amaçlıdır.
- `active_ingredients_reference.json` içindeki pH değerleri ve çakışma
  bilgileri **genel/yaygın bilinen dermatolojik gözlemlerdir**, belirli bir
  ürünün gerçek formülasyonunun yerine geçmez. Sistem bunu kullanıcıya net
  şekilde belirtir — **bu bir tıbbi tavsiye değildir.**