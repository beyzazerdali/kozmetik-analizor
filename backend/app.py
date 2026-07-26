"""
Flask API - Akıllı Kozmetik ve Cilt Bakım Rutini Analizörü backend'i.

Endpoint'ler:
  GET  /                         -> frontend'i render eder
  GET  /api/products              -> veritabanındaki (scraper ile toplanmış) ürünleri listeler
  POST /api/import-excel          -> scraper çıktısı products.xlsx'i veritabanına aktarır
  POST /api/analyze-routine       -> {items: [...]} alır, N ürünlü rutin analizini
                                      (pH çakışmaları + bilinen çakışmalar + LLM yorumu) döner
"""

from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request

import database
import llm_client
from ingredient_parser import analyze_routine

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static",
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PRODUCTS_XLSX = DATA_DIR / "products.xlsx"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/products", methods=["GET"])
def api_products():
    return jsonify(database.get_all_products())


@app.route("/api/import-excel", methods=["POST"])
def api_import_excel():
    """scraper/scrape_products.py tarafından üretilen products.xlsx'i veritabanına aktarır.
    (Embedding artık zorunlu değil - embedding modelin yoksa da içe aktarma çalışır.)"""
    if not PRODUCTS_XLSX.exists():
        return jsonify({"error": f"{PRODUCTS_XLSX} bulunamadı. Önce scraper'ı çalıştır."}), 400

    df = pd.read_excel(PRODUCTS_XLSX)
    imported = 0
    errors = []

    for _, row in df.iterrows():
        try:
            database.upsert_product(
                product_name=str(row.get("product_name", "")),
                url=str(row.get("url", "")),
                source_site=str(row.get("source_site", "")),
                ingredients_text=str(row.get("ingredients_text", "")),
                embedding=None,
            )
            imported += 1
        except Exception as e:
            errors.append({"url": row.get("url", ""), "error": str(e)})

    return jsonify({"imported": imported, "errors": errors})


@app.route("/api/analyze-routine", methods=["POST"])
def api_analyze_routine():
    """Body: { "items": [
        {"type": "db", "product_id": 3},
        {"type": "manual", "name": "Kutumdaki Serum", "ingredients_text": "Aqua, Retinol, ..."}
    ] }"""
    body = request.get_json(force=True)
    items = body.get("items", [])

    if not items or len(items) < 2:
        return jsonify({"error": "En az 2 ürün gerekli"}), 400

    resolved = []
    for item in items:
        if item.get("type") == "db":
            product = database.get_product(item["product_id"])
            if not product:
                return jsonify({"error": f"Ürün bulunamadı: id={item.get('product_id')}"}), 404
            resolved.append({
                "id": product["id"],
                "name": product["product_name"],
                "ingredients_text": product["ingredients_text"],
            })
        elif item.get("type") == "manual":
            resolved.append({
                "id": None,
                "name": item.get("name") or "Manuel ürün",
                "ingredients_text": item.get("ingredients_text", ""),
            })
        else:
            return jsonify({"error": "Her item için 'type' 'db' veya 'manual' olmalı"}), 400

    routine_result = analyze_routine(resolved)

    try:
        llm_analysis = llm_client.analyze_routine(routine_result)
    except Exception as e:
        llm_analysis = f"(LLM yanıtı alınamadı: {e}. Foundry Local'ın çalıştığından ve foundry_config.py'deki adresin doğru olduğundan emin ol.)"

    return jsonify({
        "products": routine_result["products"],
        "pairwise_findings": routine_result["pairwise_findings"],
        "llm_analysis": llm_analysis,
    })


if __name__ == "__main__":
    database.init_db()
    app.run(debug=True, port=5000)
