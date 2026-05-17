import requests
from django.conf import settings

def deepseek_chat(messages, model="deepseek-v4-pro"):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "reasoning_effort": "high"
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
