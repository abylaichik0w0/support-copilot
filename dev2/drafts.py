"""Детерминированные черновики-заглушки. Ничего не обещаем: наказание, бан,
возврат решает администратор, поэтому только «обращение принято / передано»."""
from rules_store import RulesStore

T = {
    "ru": {
        "rule": "Здравствуйте! Ваше обращение получено. Оно относится к пункту {rid} правил ({title}). Администратор рассмотрит его и примет решение.",
        "plain": "Здравствуйте! Ваше обращение получено и передано администратору.",
    },
    "kk": {
        "rule": "Сәлеметсіз бе! Өтінішіңіз қабылданды. Ол ережелердің {rid} тармағына ({title}) қатысты. Әкімші қарап, шешім қабылдайды.",
        "plain": "Сәлеметсіз бе! Өтінішіңіз қабылданып, әкімшіге жіберілді.",
    },
    "uz": {
        "rule": "Assalomu alaykum! Murojaatingiz qabul qilindi. U qoidalarning {rid}-bandiga ({title}) tegishli. Administrator ko'rib chiqib, qaror qabul qiladi.",
        "plain": "Assalomu alaykum! Murojaatingiz qabul qilindi va administratorga yuborildi.",
    },
    "en": {
        "rule": "Hello! Your request has been received. It relates to rule {rid} ({title}). An administrator will review it and make a decision.",
        "plain": "Hello! Your request has been received and passed to an administrator.",
    },
}


def generate_draft(store: RulesStore, lang: str, rule_id: str | None) -> dict:
    lang = lang if lang in T else "ru"
    rule = store.get(rule_id) if rule_id else None
    # второй рубеж защиты: цитируем только то, что есть в белом списке
    if rule and rule_id in store.valid_ids:
        title = rule.title or rule.text[:60]
        return {"lang": lang, "text": T[lang]["rule"].format(rid=rule_id, title=title), "cited": [rule_id]}
    return {"lang": lang, "text": T[lang]["plain"], "cited": []}
