import json
import os
import urllib.request

API_KEY = os.getenv("LLM_API_KEY", "")
API_URL = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
MODEL_NAME = os.getenv("LLM_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """Ты — ассистент службы поддержки игры Grand Mobile.
Твоя задача — классифицировать обращение игрока и подготовить черновик ответа на языке игрока.

Правила безопасности:
1. Никогда не обещай разбан, возврат средств или прямое наказание игрока.
2. Ссылайся ТОЛЬКО на пункты правил, переданные в контексте.
3. Отвечай строго в формате JSON:
{
  "category": "категория обращения",
  "priority": "p0 | p1 | p2 | p3",
  "text": "текст черновика ответа на языке обращения",
  "cited": ["пункт правила из контекста, например 2.1"]
}
"""


def generate_llm_draft(user_text: str, lang: str, matched_rules: list[dict]) -> dict:
    if not API_KEY:
        cited_ids = [r["id"] for r in matched_rules]
        fallback_text = "Сәлеметсіз бе! Сіздің өтінішіңіз қабылданды." if lang == "kk" else "Здравствуйте! Ваше обращение принято на рассмотрение."
        return {
            "category": "complaint.insult",
            "priority": "p2",
            "text": fallback_text,
            "cited": cited_ids
        }

    rules_context = "\n".join([r["content"] for r in matched_rules])
    user_prompt = f"Язык: {lang}\nТекст жалобы: {user_text}\nКонтекст правил:\n{rules_context}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }

    try:
        req = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            }
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception:
        return {
            "category": "other",
            "priority": "p2",
            "text": "Здравствуйте! Ваше обращение принято администрацией.",
            "cited": []
        }