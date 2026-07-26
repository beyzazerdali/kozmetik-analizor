"""
SQLite tabanlı ürün deposu + basit (brute-force cosine similarity) vektör arama.

Not: Küçük/orta ölçekli kataloglar (birkaç bin ürün) için brute-force cosine
similarity yeterince hızlıdır ve ekstra bir uzantı (sqlite-vec vb.) kurulum
derdi olmadan çalışır. Katalog büyürse `sqlite-vec` gibi bir uzantıya
geçebilirsin; kod bunun için de kolayca uyarlanabilir şekilde yazıldı.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

import numpy as np

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "kozmetik.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            url TEXT UNIQUE,
            source_site TEXT,
            ingredients_text TEXT,
            embedding TEXT,        -- JSON-encoded float list
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def upsert_product(product_name: str, url: str, source_site: str,
                    ingredients_text: str, embedding: Optional[list[float]] = None) -> int:
    conn = get_connection()
    embedding_json = json.dumps(embedding) if embedding is not None else None
    cur = conn.execute("""
        INSERT INTO products (product_name, url, source_site, ingredients_text, embedding)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            product_name=excluded.product_name,
            source_site=excluded.source_site,
            ingredients_text=excluded.ingredients_text,
            embedding=COALESCE(excluded.embedding, products.embedding)
    """, (product_name, url, source_site, ingredients_text, embedding_json))
    conn.commit()
    product_id = cur.lastrowid
    if product_id == 0:
        # ON CONFLICT durumunda lastrowid güncellenmeyebilir, id'yi ayrıca çek
        row = conn.execute("SELECT id FROM products WHERE url = ?", (url,)).fetchone()
        product_id = row["id"] if row else None
    conn.close()
    return product_id


def get_all_products() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT id, product_name, url, source_site, ingredients_text FROM products").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product(product_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def search_similar(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """En yakın top_k ürünü embedding benzerliğine göre döner."""
    conn = get_connection()
    rows = conn.execute("SELECT id, product_name, url, embedding FROM products WHERE embedding IS NOT NULL").fetchall()
    conn.close()

    scored = []
    for r in rows:
        emb = json.loads(r["embedding"])
        score = cosine_similarity(query_embedding, emb)
        scored.append({"id": r["id"], "product_name": r["product_name"], "url": r["url"], "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
