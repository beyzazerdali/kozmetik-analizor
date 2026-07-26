"""
Bu dosyayı 'llm_config.py' olarak kopyala ve kendi ayarlarını gir.
'llm_config.py' .gitignore'da olduğu için repo'ya hiç yüklenmez - API
anahtarın güvende kalır.

LLM_PROVIDER = "gemini"        -> Google Gemini API (ücretsiz katman, bulut)
LLM_PROVIDER = "foundry_local" -> Foundry Local (yerel, offline, ücretsiz)

Ücretsiz Gemini API anahtarı almak için: https://aistudio.google.com/apikey
"""

LLM_PROVIDER = "gemini"

GEMINI_API_KEY = "BURAYA_KENDI_API_KEYINI_YAPISTIR"
GEMINI_MODEL = "gemini-3.6-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"