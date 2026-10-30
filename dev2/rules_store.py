"""Загрузка rules.json и белый список пунктов (защита от галлюцинаций).

Формат rules.json: {"rules": [{"id": 30, "category": "...", "points": [{"ref": "1.1", "text": "..."}]}]}
Номера пунктов повторяются между разделами (1.1 есть почти везде), поэтому
каноническое имя пункта = код раздела + номер: "ЖБ 1.1.2", "GZ 1.2".
Для общих правил (ОП) префикс опускаем: "2.1", как в примере контракта и таксономии.
"""
import json
import re
from dataclasses import dataclass

# id раздела в rules.json -> код, которым ссылаются админы и таксономия
SECTION_CODE = {
    30: "ОП", 31: "ЖБ", 32: "GZ", 33: "ЛД", 34: "ПГО",
    35: "ГВ", 36: "СМ", 40: "ОПГ", 41: "ВБ", 42: "ФВ",
}
# написания кода в тексте игроков/админов -> канонический код
ALIASES = {
    "ОП": "ОП", "OP": "ОП", "ОБЩ": "ОП", "ОБЩИЕ": "ОП",
    "GZ": "GZ", "ГЗ": "GZ",
    "ЖБ": "ЖБ", "ЖАЛОБ": "ЖБ", "JB": "ЖБ",
    "ПГО": "ПГО", "ФВ": "ФВ", "ВБ": "ВБ", "ОПГ": "ОПГ", "ГВ": "ГВ", "СМ": "СМ", "ЛД": "ЛД",
}
# "2.1", "2.1 ОП", "ЖБ 1.1.2", "GZ 1.2", "2.1ОП"
REF_RE = re.compile(
    r"(?:(?P<pre>[A-Za-zА-Яа-я]{2,3})\s*)?(?<![\d.])(?P<num>\d{1,2}(?:\.\d{1,2}){1,2})(?![\d])\s*(?P<suf>[A-Za-zА-Яа-я]{2,3})?"
)
PUN_RE = re.compile(r"\|\s*(Грубое нарушение|Нарушение)\s*:\s*([^|]+)")


def canon(code: str | None, num: str) -> str:
    code = ALIASES.get((code or "").upper(), None) if code else None
    return num if code in (None, "ОП") else f"{code} {num}"


@dataclass
class Rule:
    id: str
    section: str
    section_title: str
    text: str
    punishment: str = ""

    @property
    def title(self) -> str:
        return self.text.split(". ")[0][:90]

    def corpus(self) -> str:
        return f"{self.section_title}. {self.text}"


class RulesStore:
    def __init__(self, path: str):
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
        self.rules: dict[str, Rule] = {}
        for sec in data["rules"]:
            code = SECTION_CODE.get(sec["id"])
            if not code:
                continue  # раздел без пунктов (термины) цитировать нельзя
            for p in sec.get("points", []):
                rid = canon(code, p["ref"])
                text = p["text"].strip()
                pun = "; ".join(f"{k}: {v.strip()}" for k, v in PUN_RE.findall(text))
                if rid in self.rules:  # в GZ часть номеров повторяется: склеиваем
                    self.rules[rid].text += " " + text
                    continue
                self.rules[rid] = Rule(rid, code, sec["category"], text, pun)
        if not self.rules:
            raise ValueError("В rules.json не найдено ни одного пункта")
        self.valid_ids = set(self.rules)

    def get(self, rid: str):
        return self.rules.get(rid)

    def sanitize_cited(self, cited: list[str]) -> list[str]:
        """Только реально существующие пункты, без дублей, порядок сохраняется."""
        out = []
        for r in cited:
            r = re.sub(r"\s+", " ", str(r)).strip()
            if r in self.valid_ids and r not in out:
                out.append(r)
        return out

    def parse_refs(self, text: str) -> list[str]:
        """Достаёт пункты из свободного текста ('2.1 оп', 'ЖБ 1.1.2', '1.2 GZ'),
        возвращает только существующие."""
        found = []
        for m in REF_RE.finditer(text or ""):
            code = m.group("suf") or m.group("pre")
            if code and code.upper() not in ALIASES:
                code = m.group("pre") if m.group("pre") and m.group("pre").upper() in ALIASES else None
            found.append(canon(code, m.group("num")))
        return self.sanitize_cited(found)

    # обратная совместимость с первым наброском
    refs_in_text = parse_refs
