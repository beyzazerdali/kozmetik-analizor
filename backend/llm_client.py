"""
LLM istemcisi - hem Foundry Local (yerel) hem Gemini API (bulut) ile
çalışabilir. Hangisinin kullanılacağı backend/llm_config.py'deki
LLM_PROVIDER değişkeniyle seçilir.

ÖNEMLİ TASARIM KARARI: "Ne yapılmalı" (ÖNERİLEN KULLANIM SIRASI) HİÇBİR
ZAMAN LLM'e bırakılmaz, her zaman kod tarafında (ingredient_parser.py'deki
"recommendation" alanlarından) deterministik üretilir. Bir sağlık/cilt bakımı
sisteminde yanlış yönde bir tavsiye (örn. "ayırın" yerine "birlikte kullanın")
kabul edilemez bir hata payıdır, bu yüzden bu kısım hangi LLM kullanılırsa
kullanılsın hep aynı, güvenilir koddan gelir.

RİSK DEĞERLENDİRMESİ (neden riskli olduğunun açıklaması) için ise:
  - Gemini gibi güçlü bir bulut modeli kullanılıyorsa, gerçekten LLM'e
    yazdırılır (birden fazla bulguyu doğru şekilde sentezleyebiliyor).
  - Foundry Local gibi küçük bir yerel model kullanılıyorsa, bu model
    bulguları birbirine karıştırabildiği için (test ettik, gerçekten oldu)
    güvenli tarafta kalıp deterministik/koddan üretilen açıklamaya düşülür.
"""

from openai import OpenAI

from llm_config import LLM_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL, GEMINI_BASE_URL

try:
    from foundry_config import FOUNDRY_BASE_URL, CHAT_MODEL_ID as FOUNDRY_MODEL
except ImportError:
    FOUNDRY_BASE_URL = None
    FOUNDRY_MODEL = None

DISCLAIMER = "UYARI: Bu analiz genel bilgi amaçlıdır, gerçek bir dermatoloğun muayenesinin yerini tutmaz."

SYSTEM_PROMPT_RISK = """Sen uzman bir dermatologsun. Sana bir kullanıcının günlük \
cilt bakım rutinindeki BİRDEN FAZLA ürünün içerik listesi ve bu içeriklerde \
tespit edilen aktif bileşenler arasındaki bilinen çakışmalar (pH çakışmaları \
ve bilinen dermatolojik uyumsuzluklar) verilecek.

Görevin SADECE şunu yazmak: verilen HER BİR çakışma bulgusunun NEDEN risk \
oluşturduğunu (veya düşük riskli/güvenli olduğunu) açıkla. Her bulguyu \
kendi bağlamında ele al - bir bulgunun gerekçesini başka bir bulguya \
karıştırıp uygulama. Hangi ürünün ne zaman kullanılması gerektiğine dair \
bir KULLANIM ÖNERİSİ YAZMA - bu ayrıca ve kesin olarak sağlanacak.

Sadece "RİSK DEĞERLENDİRMESİ:" ile başlayan TEK bir paragraf yaz, başka \
hiçbir başlık ekleme. En fazla 2-3 cümle, her bulgu için ayrı ayrı ve net."""

SYSTEM_PROMPT_RECOMMENDATION = """Sen uzman bir dermatologsun. Sana bir \
kullanıcının rutinindeki ürünler arasında tespit edilen çakışma bulguları \
verilecek. Görevin: bu bulgulara göre SOMUT bir kullanım sırası önerisi \
yazmak.

KESİN KURAL: Eğer bir bulgu pH çakışması İSE veya "orta"/"yüksek" risk \
seviyesindeyse, bu ürünlerin AYRI kullanılmasını (sabah/akşam ayırarak veya \
farklı günlerde) önermelisin - bunun tersini (aynı anda/birlikte kullanın) \
ASLA söyleme, bu tehlikeli bir hata olur. Sadece "düşük" risk seviyeli \
bulgular için genelde birlikte kullanılabileceğini söyleyebilirsin.

ÖNEMLİ NET'LİK KURALI: Aynı ürün çifti için HEM düşük riskli HEM de gerçek \
riskli (pH çakışması veya orta/yüksek) bir bulgu varsa, ayırma tavsiyesinin \
HANGİ bulguya dayandığını açıkça belirt (örn. "X ve Y arasındaki pH \
çakışması nedeniyle ayırın; Z ve W arasındaki düşük riskli etkileşim ise \
tek başına bir ayırma gerektirmezdi ama zaten var olan risk nedeniyle aynı \
kurala tabi"). Okuyanın "düşük risk, birlikte kullanılabilir" ile "ayırın" \
ifadelerini çelişkili sanmaması için bu bağlantıyı mutlaka kur.

Sadece "ÖNERİLEN KULLANIM SIRASI:" ile başlayan TEK bir paragraf yaz, başka \
hiçbir başlık ekleme. En fazla 3-4 cümle."""


_client = None
_model = None


def _get_client_and_model():
    global _client, _model
    if _client is not None:
        return _client, _model

    if LLM_PROVIDER == "gemini":
        if not GEMINI_API_KEY or GEMINI_API_KEY == "BURAYA_KENDI_API_KEYINI_YAPISTIR":
            raise RuntimeError(
                "Gemini API anahtarı ayarlanmamış. backend/llm_config.py "
                "içindeki GEMINI_API_KEY'i doldur (ücretsiz anahtar: "
                "https://aistudio.google.com/apikey)."
            )
        _client = OpenAI(base_url=GEMINI_BASE_URL, api_key=GEMINI_API_KEY)
        _model = GEMINI_MODEL
    elif LLM_PROVIDER == "foundry_local":
        if not FOUNDRY_BASE_URL:
            raise RuntimeError("foundry_config.py bulunamadı veya eksik.")
        base_url = FOUNDRY_BASE_URL.rstrip("/") + "/v1"
        _client = OpenAI(base_url=base_url, api_key="not-needed")
        _model = FOUNDRY_MODEL
    else:
        raise RuntimeError(f"Bilinmeyen LLM_PROVIDER: {LLM_PROVIDER}")

    return _client, _model


def _needs_separation(routine_result: dict) -> bool:
    """Bulgular arasında pH çakışması veya orta/yüksek risk var mı? Varsa,
    önerinin mutlaka bir 'ayırma' ifadesi içermesi gerekir."""
    for f in routine_result["pairwise_findings"]:
        if f["ph_overlaps"]:
            return True
        for c in f["known_conflicts"]:
            if c["severity"] in ("orta", "yüksek"):
                return True
    return False


_CAUTION_KEYWORDS = [
    "ayır", "farklı gün", "sabah", "akşam", "aynı anda kullanma",
    "beklet", "önce", "sonra", "değil aynı", "bir arada kullanma",
]


def _looks_safe(text: str) -> bool:
    """AI'nin önerisinde en az bir 'ayırma' ifadesi geçiyor mu diye
    kontrol eder. Gerçek bir risk varken bu kontrolden geçemeyen bir
    cevap şüpheli kabul edilip reddedilir (deterministik metne düşülür)."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in _CAUTION_KEYWORDS)


def build_deterministic_risk_assessment(routine_result: dict) -> str:
    """RİSK DEĞERLENDİRMESİ metnini tamamen koddan üretir - güvenli
    fallback (Foundry Local kullanılırken veya Gemini çağrısı başarısız
    olduğunda kullanılır)."""
    findings = routine_result["pairwise_findings"]
    reasons = []
    seen = set()

    for f in findings:
        for o in f["ph_overlaps"]:
            key = ("ph", f["product_a"], f["product_b"], o["acid_a"], o["acid_b"])
            if key not in seen:
                seen.add(key)
                reasons.append(f"{f['product_a']} × {f['product_b']}: {o['reason']}")
        for c in f["known_conflicts"]:
            key = ("kc", f["product_a"], f["product_b"], c["ingredient_a"], c["ingredient_b"])
            if key not in seen:
                seen.add(key)
                reasons.append(f"{f['product_a']} × {f['product_b']} ({c['severity']} risk): {c['reason']}")

    return " ".join(reasons)


def build_deterministic_recommendation(routine_result: dict) -> str:
    """Kullanım sırası önerisini KOD tarafında, LLM'e hiç sormadan üretir.
    Böylece yön (ayır/birleştir) her zaman tutarlı ve doğru olur - hangi
    LLM sağlayıcısı kullanılırsa kullanılsın bu kısım değişmez."""
    findings = routine_result["pairwise_findings"]
    recs = []
    seen = set()

    for f in findings:
        for o in f["ph_overlaps"]:
            key = (f["product_a"], f["product_b"], o["acid_a"], o["acid_b"])
            if key not in seen:
                seen.add(key)
                recs.append(f"{f['product_a']} × {f['product_b']}: {o['recommendation']}")
        for c in f["known_conflicts"]:
            key = (f["product_a"], f["product_b"], c["ingredient_a"], c["ingredient_b"])
            if key not in seen:
                seen.add(key)
                recs.append(f"{f['product_a']} × {f['product_b']}: {c['recommendation']}")

    if not recs:
        return "Bu ürünler, bilinen çakışma tablomuza göre aynı rutinde serbestçe kullanılabilir."

    return " ".join(recs)


def build_routine_prompt(routine_result: dict) -> str:
    lines = ["Rutindeki ürünler ve tespit edilen aktif bileşenler:\n"]
    for p in routine_result["products"]:
        actives_str = ", ".join(a["inci_name"] for a in p["actives"]) or "(bilinen aktif bileşen yok)"
        lines.append(f"- {p['name']}: {actives_str}")

    lines.append("\nTespit edilen çakışmalar:")
    for f in routine_result["pairwise_findings"]:
        for o in f["ph_overlaps"]:
            lines.append(
                f"  - [pH çakışması] {f['product_a']} ({o['acid_a']}, pH {o['acid_a_range'][0]}-{o['acid_a_range'][1]}) "
                f"<-> {f['product_b']} ({o['acid_b']}, pH {o['acid_b_range'][0]}-{o['acid_b_range'][1]})"
            )
        for c in f["known_conflicts"]:
            lines.append(
                f"  - [bilinen çakışma - {c['severity']} risk] {f['product_a']} ({c['ingredient_a']}) "
                f"<-> {f['product_b']} ({c['ingredient_b']}): {c['reason']}"
            )

    lines.append("\nSadece RİSK DEĞERLENDİRMESİ paragrafını yaz, her bulguyu ayrı ele al.")
    return "\n".join(lines)


def get_risk_assessment(routine_result: dict) -> str:
    """Gemini kullanılıyorsa gerçekten LLM'e yazdırır (güçlü model, çoklu
    bulguyu karıştırmıyor); Foundry Local kullanılıyorsa veya çağrı
    başarısız olursa güvenli deterministik metne düşer."""
    deterministic_fallback = build_deterministic_risk_assessment(routine_result)

    if LLM_PROVIDER != "gemini":
        return deterministic_fallback

    try:
        client, model = _get_client_and_model()
        extra_kwargs = {}
        if LLM_PROVIDER == "gemini":
            extra_kwargs["reasoning_effort"] = "low"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_RISK},
                {"role": "user", "content": build_routine_prompt(routine_result)},
            ],
            temperature=0.3,
            max_tokens=1200,
            **extra_kwargs,
        )
        text = response.choices[0].message.content or ""
        text = text.strip()
        if text.upper().startswith("RİSK DEĞERLENDİRMESİ"):
            text = text.split(":", 1)[1].strip() if ":" in text else text
        return text if text else deterministic_fallback
    except Exception:
        return deterministic_fallback


def get_recommendation(routine_result: dict) -> str:
    """Gemini kullanılıyorsa öneriyi gerçekten LLM'e yazdırır, AMA sonucu
    bir güvenlik kontrolünden geçirir: gerçek bir risk varken (pH çakışması
    veya orta/yüksek risk) cevapta bir 'ayırma' ifadesi geçmiyorsa, bu
    şüpheli kabul edilip güvenli deterministik metne düşülür. Böylece AI'nin
    yön hatası (örn. 'ayırın' yerine 'birlikte kullanın' demesi) kullanıcıya
    hiçbir zaman ulaşmaz."""
    deterministic_fallback = build_deterministic_recommendation(routine_result)

    if LLM_PROVIDER != "gemini":
        return deterministic_fallback

    try:
        client, model = _get_client_and_model()
        extra_kwargs = {}
        if LLM_PROVIDER == "gemini":
            extra_kwargs["reasoning_effort"] = "low"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_RECOMMENDATION},
                {"role": "user", "content": build_routine_prompt(routine_result)},
            ],
            temperature=0.3,
            max_tokens=1200,
            **extra_kwargs,
        )
        text = response.choices[0].message.content or ""
        text = text.strip()
        if text.upper().startswith("ÖNERİLEN KULLANIM SIRASI"):
            text = text.split(":", 1)[1].strip() if ":" in text else text

        if not text:
            return deterministic_fallback

        # GÜVENLİK KONTROLÜ: gerçek bir risk varken AI'nin cevabında bir
        # ayırma ifadesi yoksa, bu cevaba güvenme, deterministik metne düş.
        if _needs_separation(routine_result) and not _looks_safe(text):
            return deterministic_fallback

        return text
    except Exception:
        return deterministic_fallback


def analyze_routine(routine_result: dict) -> str:
    findings = routine_result["pairwise_findings"]

    if not findings:
        risk_text = "Rutindeki ürünler arasında bilinen bir pH çakışması veya dermatolojik uyumsuzluk tespit edilmedi."
        recommendation_text = "Bu ürünler, bilinen çakışma tablomuza göre aynı rutinde serbestçe kullanılabilir."
    else:
        risk_text = get_risk_assessment(routine_result)
        recommendation_text = get_recommendation(routine_result)

    return (
        f"RİSK DEĞERLENDİRMESİ: {risk_text}\n\n"
        f"ÖNERİLEN KULLANIM SIRASI: {recommendation_text}\n\n"
        f"{DISCLAIMER}"
    )