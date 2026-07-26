"""
Kozmetik ürün sayfalarından (Trendyol, Gratis) ürün adı ve içerik (INCI)
listesini çekip data/products.xlsx dosyasına yazan Playwright betiği.

Kullanım:
    python scrape_products.py --urls urls.txt --site trendyol
    python scrape_products.py --urls urls.txt --site gratis --headless false

urls.txt içeriği: her satırda bir ürün URL'si.

ETİK/YASAL NOT:
- Hedef sitenin robots.txt ve kullanım şartlarına uy.
- İstekler arasına bekleme (delay) koy, siteyi yükleme altına sokma.
- Bu betik yalnızca kişisel/eğitim amaçlı kullanım içindir.
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from selectors_config import SITE_CONFIGS, INGREDIENTS_KEYWORDS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_XLSX = DATA_DIR / "products.xlsx"


def extract_ingredients_text(page, config: dict) -> str:
    """İçindekiler/İçerik bölümünü bulmaya çalışır. Önce sekmeye tıklamayı
    dener, sonra sayfa metninde "Ingredients:" gibi net bir ifadeyi arar
    (bu en güvenilir yöntem), en son belirlenen CSS seçicisini dener."""

    # 1) Sekme varsa tıkla
    try:
        tab = page.locator(config["ingredients_tab_selector"]).first
        if tab.count() > 0:
            tab.click(timeout=3000)
            page.wait_for_timeout(500)
    except (PWTimeout, Exception):
        pass

    # 2) EN GÜVENİLİR yöntem: sayfa metninde "Ingredients:" gibi net bir
    #    etiketi ara (birçok Türk kozmetik sitesi INCI listesini İngilizce
    #    "Ingredients:" etiketiyle yazıyor). Bulursa, bir sonraki bilinen
    #    durak kelimesine (Sku, Barcode, Yorumlar vb.) kadar keser.
    STOP_WORDS = ["\nSku:", "\nBarcode:", "\nYorumlar", "\nUyarılar", "\nKullanım\n", "\n\n\n"]
    try:
        full_text = page.locator("body").inner_text()
        for label in ["Ingredients:", "INGREDIENTS:", "İçindekiler:"]:
            idx = full_text.find(label)
            if idx != -1:
                snippet = full_text[idx + len(label):idx + len(label) + 1500]
                cut_at = len(snippet)
                for stop in STOP_WORDS:
                    stop_idx = snippet.find(stop)
                    if stop_idx != -1:
                        cut_at = min(cut_at, stop_idx)
                result = snippet[:cut_at].strip()
                if result:
                    return result
    except Exception:
        pass

    # 3) Belirlenen CSS içerik seçicisini dene (site bazlı, tahmine dayalı
    #    olabilir - bazen yanlış bölümü de yakalayabilir, bu yüzden ikinci
    #    öncelikte)
    try:
        content_el = page.locator(config["ingredients_content_selector"]).first
        if content_el.count() > 0:
            text = content_el.inner_text(timeout=3000).strip()
            if text:
                return text
    except (PWTimeout, Exception):
        pass

    # 4) Son çare: daha genel anahtar kelimelerle ara (eski davranış)
    try:
        full_text = page.locator("body").inner_text()
        lower = full_text.lower()
        for kw in INGREDIENTS_KEYWORDS:
            idx = lower.find(kw)
            if idx != -1:
                return full_text[idx: idx + 800].strip()
    except Exception:
        pass

    return ""


def scrape_one(page, url: str, config: dict) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_selector(config["base_wait_selector"], timeout=10000)
    except PWTimeout:
        pass

    name = ""
    try:
        name_el = page.locator(config["product_name_selector"]).first
        if name_el.count() > 0:
            name = name_el.inner_text(timeout=3000).strip()
    except Exception:
        pass

    ingredients = extract_ingredients_text(page, config)

    return {
        "url": url,
        "product_name": name or "(bulunamadı)",
        "ingredients_text": ingredients or "(bulunamadı - manuel kontrol gerekiyor)",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--urls", required=True, help="Her satırda bir URL içeren dosya")
    parser.add_argument("--site", required=True, choices=list(SITE_CONFIGS.keys()))
    parser.add_argument("--headless", default="true", choices=["true", "false"])
    parser.add_argument("--delay", type=float, default=2.0, help="İstekler arası bekleme (sn)")
    args = parser.parse_args()

    urls_path = Path(args.urls)
    if not urls_path.exists():
        print(f"HATA: {urls_path} bulunamadı.")
        sys.exit(1)

    raw_lines = urls_path.read_text(encoding="utf-8").splitlines()
    urls = []
    for line in raw_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue  # boş satır veya yorum satırı, atla
        if not line.startswith("http://") and not line.startswith("https://"):
            line = "https://" + line  # şema eksikse otomatik ekle
        urls.append(line)

    if not urls:
        print("HATA: URL listesi boş (tüm satırlar yorum veya boş).")
        sys.exit(1)

    config = SITE_CONFIGS[args.site]
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=(args.headless == "true"))
        page = browser.new_page()

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Çekiliyor: {url}")
            try:
                row = scrape_one(page, url, config)
                row["source_site"] = args.site
                results.append(row)
                print(f"   -> {row['product_name']}")
            except Exception as e:
                print(f"   HATA: {e}")
                results.append({
                    "url": url,
                    "product_name": "(hata)",
                    "ingredients_text": str(e),
                    "source_site": args.site,
                })

            if args.headless == "false":
                input("   [İncelemek için tarayıcıyı kullan, devam etmek için Enter'a bas]")
            else:
                time.sleep(args.delay)

        browser.close()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results)

    if OUTPUT_XLSX.exists():
        existing = pd.read_excel(OUTPUT_XLSX)
        df = pd.concat([existing, df], ignore_index=True).drop_duplicates(subset=["url"], keep="last")

    df.to_excel(OUTPUT_XLSX, index=False)
    print(f"\nTamamlandı. {len(df)} ürün -> {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()