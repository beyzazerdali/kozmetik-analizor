# Akıllı Kozmetik Analizörü

Trendyol/Gratis gibi sitelerden ürün içerik listelerini (INCI) toplayan, bunları
vektör veritabanında saklayan ve iki ürünün asit pH'larının çakışıp çakışmadığını
yerel bir LLM (Foundry Local ile Phi-3.5) üzerinden analiz eden uçtan uca sistem.

## Klasör Yapısı

```
kozmetik-analizor/
├── scraper/
│   ├── scrape_products.py     # Playwright scraper
│   ├── selectors_config.py    # Site bazlı CSS seçicileri
│   └── requirements.txt
├── data/
│   ├── acid_ph_reference.json # Bilinen asitlerin tipik formülasyon pH aralıkları
│   └── products.xlsx          # Scraper çıktısı (scraper çalıştırılınca oluşur)
├── backend/
│   ├── app.py                 # Flask API
│   ├── database.py            # SQLite + basit vektör arama
│   ├── embeddings.py          # Foundry Local embedding istemcisi
│   ├── llm_client.py          # Foundry Local chat istemcisi (Phi-3.5)
│   ├── ingredient_parser.py   # İçerik metninden asit tespiti
│   └── requirements.txt
└── frontend/
    ├── templates/index.html
    └── static/{css,js}
```

## Kurulum Adımları

### 1) Foundry Local'ı kur ve modelleri indir

```bash
# Foundry Local CLI'ı kurduktan sonra:
foundry model run phi-3.5-mini
foundry model run qwen2.5-embedding  # veya kataloğunda gördüğün embedding modeli adı
```

> Not: Foundry Local model kataloğundaki tam model adları zamanla değişebilir.
> `foundry model list` komutuyla güncel adları kontrol et ve
> `backend/llm_client.py` / `backend/embeddings.py` içindeki `MODEL_ALIAS`
> değerlerini ona göre güncelle.

### 2) Backend'i kur

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Flask varsayılan olarak `http://localhost:5000` üzerinde çalışır.

### 3) Scraper'ı çalıştır (ayrı terminalde)

```bash
cd scraper
pip install -r requirements.txt
playwright install chromium
python scrape_products.py --urls urls.txt --site trendyol
```

Bu, `data/products.xlsx` dosyasını üretir. Ardından backend'de
`/api/import-excel` endpoint'ini çağırarak bu veriyi veritabanına ve
embedding indexine aktarabilirsin.

## Önemli Yasal/Etik Not

- Scraping yaparken hedef sitenin `robots.txt` ve kullanım koşullarına uy,
  istekler arasına makul bekleme süreleri koy, siteyi aşırı yüklemeyecek
  şekilde çalıştır. Bu proje yalnızca kişisel/eğitim amaçlıdır.
- `acid_ph_reference.json` içindeki pH değerleri **tipik formülasyon
  aralıklarıdır**, belirli bir ürünün gerçek pH'ı değildir (gerçek pH,
  markanın formülasyonuna göre değişir). Sistem bunu kullanıcıya
  net şekilde belirtmelidir — bu bir tıbbi tavsiye değildir.
