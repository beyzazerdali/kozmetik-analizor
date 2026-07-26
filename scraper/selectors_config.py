"""
Site bazlı CSS seçicileri (selectors).

ÖNEMLİ: Trendyol ve Gratis gibi siteler zaman zaman HTML yapılarını
değiştirir. Bu seçiciler kırılırsa:
  1. Tarayıcıda ürün sayfasını aç, F12 ile DevTools'u aç.
  2. İçerik/İçindekiler bölümüne sağ tık > "İncele" yap.
  3. Doğru CSS seçicisini (class adı) bul ve aşağıyı güncelle.

Not: Bu seçiciler örnek/başlangıç niteliğindedir, siteye göre test edip
düzeltmen gerekecek.
"""

SITE_CONFIGS = {
    "trendyol": {
        "base_wait_selector": "h1",
        "product_name_selector": "h1.pr-new-br span, h1.product-name",
        # Trendyol'da içerik genelde "Ürün Özellikleri" veya "İçindekiler"
        # sekmesinde/akordeonunda yer alır. Sekmeye tıklamak gerekebilir.
        "ingredients_tab_selector": "text=İçindekiler",
        "ingredients_content_selector": "div.detail-desc-list, div.info-wrapper",
    },
    "gratis": {
        "base_wait_selector": "h1",
        "product_name_selector": "h1.product-name, h1.pdp-title",
        "ingredients_tab_selector": "text=İçindekiler",
        "ingredients_content_selector": "div.pdp-ingredients, div.tab-content",
    },
    "rossmann": {
        "base_wait_selector": "h1",
        "product_name_selector": "h1",
        # Rossmann Türkiye ürün sayfalarında "İçindekiler" genelde ayrı bir
        # sekme/akordeon olarak yer alır. Tam class adını henüz doğrulamadık;
        # aşağıdaki genel seçici bulunamazsa, kod otomatik olarak sayfa
        # metninde "içindekiler" kelimesini arayan fallback'e düşer.
        "ingredients_tab_selector": "text=İçindekiler",
        "ingredients_content_selector": "div.product-attribute, div[class*='ingredient'], div[class*='content']",
    },
}

# Genel eşleşme denemesi için, ingredients metninde arayacağımız anahtar
# kelimeler (bazı sitelerde "İçindekiler" yerine "İçerik", "Formül" vb. olabilir)
INGREDIENTS_KEYWORDS = ["içindekiler", "içerik", "formül", "ingredients"]