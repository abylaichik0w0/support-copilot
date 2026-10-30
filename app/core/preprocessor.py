import re
from langdetect import DetectorFactory, detect

DetectorFactory.seed = 0

# Восстановление букв казахского языка, искаженных cp1251
CP1251_KZ_MAP = {
    'ќ': 'қ', 'ґ': 'ғ', 'ѕ': 'ң', 'є': 'ә',
    'ј': 'ө', 'ў': 'ұ', 'ї': 'ү',
    'Ќ': 'Қ', 'Ґ': 'Ғ', 'Ѕ': 'Ң', 'Є': 'Ә',
    'Ј': 'Ө', 'Ў': 'Ұ', 'Ї': 'Ү'
}


def fix_encoding(text: str) -> str:
    """Заменяет псевдо-символы cp1251 на корректные казахские буквы."""
    return "".join(CP1251_KZ_MAP.get(ch, ch) for ch in text)


def detect_language(text: str) -> str:
    """Определяет язык текста (ru, kk, uz, en, und)."""
    cleaned = re.sub(r'[^a-zA-Zа-яА-ЯёЁәіңғүұқөһӘІҢҒҮҰҚӨҺ\s]', '', text).strip()
    if not cleaned or len(cleaned) < 3:
        return "und"
    
    # Характерные специфические буквы казахского алфавита
    if re.search(r'[әіңғүұқөһӘІҢҒҮҰҚӨҺ]', cleaned):
        return "kk"
    
    try:
        lang = detect(cleaned)
        if lang in ["ru", "kk", "uz", "en"]:
            return lang
        return "und"
    except Exception:
        return "ru"


def extract_entities(messages: list) -> dict:
    """Извлекает никнейм нарушителя, ссылки на пункты правил и флаг наличия доказательств."""
    full_text = " ".join([m.text for m in messages])
    
    # Никнеймы формата Name_Surname или латиница/кириллица с подчеркиванием
    nick_match = re.search(r'\b[A-Za-z0-9]+_[A-Za-z0-9]+\b', full_text)
    nickname = nick_match.group(0) if nick_match else None
    
    # Пункты правил вроде "2.1", "3.4"
    rule_refs = re.findall(r'\b\d+\.\d+\b', full_text)
    
    # Проверка наличия скриншотов / фрапса
    total_attachments = sum(getattr(m, 'attachments', 0) or 0 for m in messages)
    evidence_keywords = bool(re.search(r'(скрин|док-ва|доказ|фрапс|видео|фото|doka)', full_text, re.IGNORECASE))
    has_evidence = total_attachments > 0 or evidence_keywords
    
    return {
        "nickname": nickname,
        "rule_refs": list(set(rule_refs)),
        "has_evidence": has_evidence,
        "server": None
    }