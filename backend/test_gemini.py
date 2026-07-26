import traceback

try:
    from llm_config import LLM_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL, GEMINI_BASE_URL
    print("LLM_PROVIDER:", LLM_PROVIDER)
    print("GEMINI_API_KEY ayarlı mı:", GEMINI_API_KEY != "BURAYA_KENDI_API_KEYINI_YAPISTIR" and bool(GEMINI_API_KEY))
    print("GEMINI_MODEL:", GEMINI_MODEL)
except Exception:
    print("llm_config.py okunamadı:")
    traceback.print_exc()
    raise SystemExit

from openai import OpenAI

try:
    client = OpenAI(base_url=GEMINI_BASE_URL, api_key=GEMINI_API_KEY)
    response = client.chat.completions.create(
    model=GEMINI_MODEL,
    messages=[{"role": "user", "content": "Merhaba, bir cümleyle kendini tanıt."}],
    max_tokens=1200,
    reasoning_effort="low",
)
    print("\nfinish_reason:", response.choices[0].finish_reason)
    print("BAŞARILI! Gemini cevabı:")
    print(response.choices[0].message.content)
except Exception:
    print("\nGemini çağrısı BAŞARISIZ:")
    traceback.print_exc()