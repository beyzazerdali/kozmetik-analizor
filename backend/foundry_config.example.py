"""
Bu dosyayı 'foundry_config.py' olarak kopyala (sadece Foundry Local
kullanacaksan gerekli). 'foundry_config.py' .gitignore'da olduğu için
repo'ya yüklenmez.

`foundry model run <model>` çalıştırdığında terminalde göreceğin
"Service is Started on http://127.0.0.1:PORT" adresini FOUNDRY_BASE_URL'e
yapıştır.
"""

FOUNDRY_BASE_URL = "http://127.0.0.1:PORT_BURAYA"
CHAT_MODEL_ID = "Phi-3.5-mini-instruct-generic-cpu:2"