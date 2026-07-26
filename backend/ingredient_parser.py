"""
Ürün içerik (INCI) metinlerinden bilinen aktif bileşenleri tespit eder ve
hem pH çakışmalarını (asitler için) hem de bilinen dermatolojik çakışmaları
(Retinol + Vitamin C gibi, pH'tan bağımsız) hesaplar.

Artık sadece 2 değil, N ürünlü bir "rutin" analiz edebilir.
"""

import json
from itertools import combinations
from pathlib import Path

REFERENCE_PATH = Path(__file__).resolve().parent.parent / "data" / "active_ingredients_reference.json"

with open(REFERENCE_PATH, "r", encoding="utf-8") as f:
    _REFERENCE = json.load(f)

ACTIVES = _REFERENCE["actives"]
KNOWN_CONFLICTS = _REFERENCE["known_conflicts"]

# Hızlı bakış için conflict tablosunu (a,b) -> info şeklinde indeksle (iki yönlü)
_CONFLICT_INDEX = {}
for c in KNOWN_CONFLICTS:
    _CONFLICT_INDEX[(c["a"], c["b"])] = c
    _CONFLICT_INDEX[(c["b"], c["a"])] = c


def find_actives_in_text(ingredients_text: str) -> list[dict]:
    """Verilen içerik metninde bilinen aktif bileşenleri arar."""
    if not ingredients_text:
        return []

    text_lower = ingredients_text.lower()
    found = []

    for active in ACTIVES:
        names_to_check = [active["inci_name"].lower()] + [a.lower() for a in active.get("aliases", [])]
        if any(name in text_lower for name in names_to_check):
            found.append(active)

    return found


def check_ph_overlap(acids_a: list[dict], acids_b: list[dict]) -> list[dict]:
    """İki üründeki (sadece asit olan) bileşenler arasında pH aralığı çakışan
    çiftleri bulur. Her çakışma için, YÖNÜ HER ZAMAN AYNI olan sabit bir
    öneri döner (LLM'e bırakılmaz) - çünkü pH çakışması tespit edildiğinde
    doğru yön her zaman "dikkatli/ayırarak kullan"dır, bunun tersini
    (birlikte kullanın) bir dil modelinin uydurmasına izin vermek yanlış
    ve tutarsız sonuçlara yol açabilir."""
    overlaps = []
    only_acids_a = [a for a in acids_a if a.get("is_acid")]
    only_acids_b = [b for b in acids_b if b.get("is_acid")]

    for a in only_acids_a:
        for b in only_acids_b:
            if a["inci_name"] == b["inci_name"]:
                continue
            if a["typical_ph_min"] <= b["typical_ph_max"] and b["typical_ph_min"] <= a["typical_ph_max"]:
                overlaps.append({
                    "type": "ph_overlap",
                    "acid_a": a["inci_name"],
                    "acid_a_range": [a["typical_ph_min"], a["typical_ph_max"]],
                    "acid_b": b["inci_name"],
                    "acid_b_range": [b["typical_ph_min"], b["typical_ph_max"]],
                    "reason": (
                        f"{a['inci_name']} (pH {a['typical_ph_min']}-{a['typical_ph_max']}) ve "
                        f"{b['inci_name']} (pH {b['typical_ph_min']}-{b['typical_ph_max']}) birbirine "
                        "yakın/örtüşen pH aralıklarında en etkili hale gelir; bu da aynı anda "
                        "kullanıldıklarında toplam eksfoliasyon etkisinin ve tahriş riskinin artabileceği anlamına gelir."
                    ),
                    "recommendation": (
                        f"{a['inci_name']} ve {b['inci_name']} benzer pH aralığında en "
                        "etkili oldukları için aynı anda kullanıldıklarında tahriş riski "
                        "artabilir; sabah/akşam ayırarak veya farklı günlerde kullanın."
                    ),
                })
    return overlaps

def check_known_conflicts(actives_a: list[dict], actives_b: list[dict]) -> list[dict]:
    """Bilinen (pH'tan bağımsız) çakışma tablosuna göre iki ürün arasındaki
    riskli ikilileri bulur (örn. Retinol + Vitamin C)."""
    found = []
    seen = set()
    for a in actives_a:
        for b in actives_b:
            if a["inci_name"] == b["inci_name"]:
                continue
            key = (a["inci_name"], b["inci_name"])
            if key in _CONFLICT_INDEX:
                pair_id = tuple(sorted([a["inci_name"], b["inci_name"]]))
                if pair_id in seen:
                    continue
                seen.add(pair_id)
                info = _CONFLICT_INDEX[key]
                found.append({
                    "type": "known_conflict",
                    "ingredient_a": a["inci_name"],
                    "ingredient_b": b["inci_name"],
                    "severity": info["severity"],
                    "reason": info["reason"],
                    "recommendation": info["recommendation"],
                })
    return found


def analyze_routine(products: list[dict]) -> dict:
    """N ürünlü bir rutini analiz eder.

    products: [{"id": ..., "name": ..., "ingredients_text": ...}, ...]

    Döner: {
        "products": [{"id", "name", "actives": [...]}, ...],
        "pairwise_findings": [
            {"product_a": name, "product_b": name, "ph_overlaps": [...], "known_conflicts": [...]}
        ]
    }
    """
    enriched = []
    for p in products:
        actives = find_actives_in_text(p.get("ingredients_text", ""))
        enriched.append({"id": p.get("id"), "name": p.get("name"), "actives": actives})

    pairwise_findings = []
    for prod_a, prod_b in combinations(enriched, 2):
        ph_overlaps = check_ph_overlap(prod_a["actives"], prod_b["actives"])
        known = check_known_conflicts(prod_a["actives"], prod_b["actives"])
        if ph_overlaps or known:
            pairwise_findings.append({
                "product_a": prod_a["name"],
                "product_b": prod_b["name"],
                "ph_overlaps": ph_overlaps,
                "known_conflicts": known,
            })

    return {"products": enriched, "pairwise_findings": pairwise_findings}


if __name__ == "__main__":
    sample = [
        {"id": 1, "name": "Serum A", "ingredients_text": "Aqua, Retinol, Glycerin"},
        {"id": 2, "name": "Serum B", "ingredients_text": "Aqua, Ascorbic Acid, Ferulic Acid"},
        {"id": 3, "name": "Tonik C", "ingredients_text": "Aqua, Salicylic Acid, Niacinamide"},
    ]
    result = analyze_routine(sample)
    print(json.dumps(result, indent=2, ensure_ascii=False))