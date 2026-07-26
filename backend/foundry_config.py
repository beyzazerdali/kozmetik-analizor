"""
Foundry Local servis adresi.

ÖNEMLİ: `foundry model run <model>` her çalıştırdığında (veya servisi yeniden
başlattığında) port DEĞİŞEBİLİR. Terminaldeki şu satıra bak:

    Service is Started on http://127.0.0.1:60898/, PID ...

O adresi aşağıya yapıştır (sonundaki "/" kalabilir veya kalmayabilir, ikisi de
çalışır). Adres değişirse sadece burayı güncellemen yeterli, başka hiçbir
dosyayı değiştirmene gerek yok.
"""

FOUNDRY_BASE_URL = "http://127.0.0.1:52238"

# `foundry model list` çıktısındaki tam Model ID'ler (alias değil).
CHAT_MODEL_ID = "Phi-3.5-mini-instruct-generic-cpu:2"

# Şimdilik embedding modelin yok (kataloğunda embedding görevli model
# görünmüyordu). Bulana kadar bu None kalsın, embeddings.py bunu kontrol edip
# anlamlı bir hata verecek.
EMBEDDING_MODEL_ID = None
