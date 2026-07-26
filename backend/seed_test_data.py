"""
Veritabanını çeşitli senaryoları kapsayan örnek ürünlerle doldurur.

Bu ürünlerin çoğu gerçekçi olsun diye elle yazılmıştır (gerçek scraping
değildir). Amaç: sistemin farklı aktif bileşen kombinasyonlarını (asit
çakışmaları, Retinol+Vitamin C, Benzoyl Peroxide vb.) düzgün tespit
ettiğini gösterebilmek.

Gerçek scraping ile çektiğin ürünleri (data/products.xlsx) ayrıca
/api/import-excel endpoint'i üzerinden eklemen önerilir - böylece hem
gerçek hem örnek veri aynı veritabanında bir arada olur.

Çalıştırmak için:
    python seed_test_data.py
"""

import database

database.init_db()

SAMPLE_PRODUCTS = [
    # --- AHA / BHA asitleri ---
    {
        "name": "Glow Recipe Benzeri Glikolik Tonik",
        "url": "https://example.com/urun/glikolik-tonik",
        "site": "ornek-veri",
        "ingredients": "Aqua, Glycolic Acid, Lactic Acid, Glycerin, Panthenol, Aloe Barbadensis Leaf Juice",
    },
    {
        "name": "Salisilik Asit Akne Serumu",
        "url": "https://example.com/urun/salisilik-serum",
        "site": "ornek-veri",
        "ingredients": "Aqua, Salicylic Acid, Niacinamide, Zinc PCA, Panthenol",
    },
    {
        "name": "Mandelik Asit Hassas Cilt Peelingi",
        "url": "https://example.com/urun/mandelik-peeling",
        "site": "ornek-veri",
        "ingredients": "Aqua, Mandelic Acid, Glycerin, Allantoin, Panthenol",
    },
    {
        "name": "Gece Bakım Retinol Serumu",
        "url": "https://example.com/urun/retinol-serum",
        "site": "ornek-veri",
        "ingredients": "Aqua, Retinol, Squalane, Glycerin, Tocopherol",
    },
    {
        "name": "Yoğun Etkili Retinal Krem",
        "url": "https://example.com/urun/retinal-krem",
        "site": "ornek-veri",
        "ingredients": "Aqua, Retinaldehyde, Ceramide NP, Squalane, Panthenol",
    },
    {
        "name": "C Vitamini Aydınlatıcı Serum",
        "url": "https://example.com/urun/c-vitamini-serum",
        "site": "ornek-veri",
        "ingredients": "Aqua, Ascorbic Acid, Ferulic Acid, Tocopherol, Hyaluronic Acid",
    },
    {
        "name": "Taze C Vitamini Ampul",
        "url": "https://example.com/urun/c-vitamini-ampul",
        "site": "ornek-veri",
        "ingredients": "Aqua, Ascorbic Acid, Sodium Hyaluronate, Panthenol",
    },
    {
        "name": "Niasinamid Gözenek Sıkılaştırıcı",
        "url": "https://example.com/urun/niasinamid-serum",
        "site": "ornek-veri",
        "ingredients": "Aqua, Niacinamide, Zinc PCA, Glycerin, Panthenol",
    },
    {
        "name": "Benzoil Peroksit Akne Jeli",
        "url": "https://example.com/urun/benzoil-peroksit-jel",
        "site": "ornek-veri",
        "ingredients": "Aqua, Benzoyl Peroxide, Glycerin, Niacinamide",
    },
    {
        "name": "Azelaik Asit Leke Karşıtı Krem",
        "url": "https://example.com/urun/azelaik-krem",
        "site": "ornek-veri",
        "ingredients": "Aqua, Azelaic Acid, Squalane, Glycerin, Ceramide NP",
    },
    {
        "name": "Bakuchiol Nazik Yenileyici Serum",
        "url": "https://example.com/urun/bakuchiol-serum",
        "site": "ornek-veri",
        "ingredients": "Aqua, Bakuchiol, Squalane, Tocopherol, Panthenol",
    },
    {
        "name": "Yoğun Nemlendirici Hyaluronik Asit Serumu",
        "url": "https://example.com/urun/hyaluronik-serum",
        "site": "ornek-veri",
        "ingredients": "Aqua, Sodium Hyaluronate, Glycerin, Panthenol, Allantoin",
    },
    {
        "name": "Sade Nemlendirici Krem (Aktifsiz)",
        "url": "https://example.com/urun/sade-nemlendirici",
        "site": "ornek-veri",
        "ingredients": "Aqua, Glycerin, Squalane, Ceramide NP, Panthenol, Allantoin",
    },
]

for p in SAMPLE_PRODUCTS:
    database.upsert_product(
        product_name=p["name"],
        url=p["url"],
        source_site=p["site"],
        ingredients_text=p["ingredients"],
        embedding=None,
    )

print(f"{len(SAMPLE_PRODUCTS)} örnek ürün eklendi.")
print()
print("Not: Gerçek scraping ile çektiğin ürünleri de eklemek için:")
print("  1) Flask çalışırken (python app.py)")
print("  2) Yeni bir terminalde: curl -X POST http://localhost:5000/api/import-excel")
print()
for p in database.get_all_products():
    print(f"  [{p['id']}] {p['product_name']} ({p['source_site']})")