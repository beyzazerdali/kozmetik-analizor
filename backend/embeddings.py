"""
Foundry Local'ın embedding endpoint'ine bağlanan istemci.

Not: `foundry model list` çıktısında şu an embedding görevli bir model
görünmüyorsa, EMBEDDING_MODEL_ID boş kalır ve bu modül anlamlı bir hata
fırlatır. Embedding olmadan da sistemin geri kalanı (asit tespiti, pH
çakışma analizi, LLM yorumu) tam çalışır — embedding sadece "benzer ürün
arama" (/api/search) özelliği için gerekli.
"""

from openai import OpenAI

from foundry_config import FOUNDRY_BASE_URL, EMBEDDING_MODEL_ID

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        base_url = FOUNDRY_BASE_URL.rstrip("/") + "/v1"
        _client = OpenAI(base_url=base_url, api_key="not-needed")
    return _client


def get_embedding(text: str) -> list[float]:
    if not EMBEDDING_MODEL_ID:
        raise RuntimeError(
            "Henüz bir embedding modeli ayarlanmadı. "
            "foundry_config.py içindeki EMBEDDING_MODEL_ID'yi doldur "
            "(önce Foundry Local kataloğunda embedding görevli bir model bulman gerekiyor)."
        )
    client = _get_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL_ID, input=text)
    return response.data[0].embedding


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    return [get_embedding(t) for t in texts]
