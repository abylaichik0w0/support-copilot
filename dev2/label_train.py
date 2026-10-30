"""Псевдоразметка train по реальной taxonomy.json (черновик от 2026-10-27).

python label_train.py --in tickets_train.jsonl.gz --out train_labeled.jsonl [--limit 0]

Источники метки (поле label_source):
  violation  - пункт из ответа админа -> категория по taxonomy (самая надёжная)
  verdict    - вердикт invalid_format -> complaint.invalid
  keyword    - ключевые слова в тексте игрока (шумнее, особенно для репортов)
Тикеты, где метку поставить не из чего, пропускаются: лучше меньше, но чище.
Приоритет выставляется по правилам из taxonomy.json; они помечены как черновик
организаторов, поэтому при их изменении правится только PRIORITY_BASE/has_evidence.
"""
import argparse, gzip, json, re
from collections import Counter

from rules_store import RulesStore

# пункт -> категория (из taxonomy.json, поле rules)
REF_TO_CAT = {
    "2.1": "complaint.insult", "2.4": "complaint.insult", "2.6": "complaint.insult",
    "5.2": "complaint.cheat",
    "5.3": "complaint.dm", "5.4": "complaint.dm", "GZ 1.1": "complaint.dm", "GZ 1.2": "complaint.dm",
    "4.1": "complaint.scam", "4.2": "complaint.scam",
    "2.3": "complaint.rmt_ads", "4.4": "complaint.rmt_ads",
    "3.4": "complaint.admin",
    "ЖБ 1.1.2": "complaint.invalid", "ЖБ 1.2.7": "complaint.invalid",
}
PRIORITY_BASE = {
    "complaint.insult": "p2", "complaint.dm": "p2", "complaint.other": "p2",
    "complaint.cheat": "p1", "complaint.scam": "p1", "complaint.rmt_ads": "p1", "complaint.admin": "p2",
    "complaint.invalid": "p3",
    "report.question": "p3", "report.offtopic": "p3", "report.help": "p2", "report.complaint": "p2",
    "report.account": "p0", "report.payment": "p0",
}
KEYWORDS = [  # порядок важен: первое совпадение побеждает
    ("report", r"взлом|угнал|угон.*акк|пропал[аио]? .*(машин|дом|акк|имущ)|не могу зайти|потерял акк", "report.account"),
    ("report", r"донат|оплатил|оплата|списал|платеж|платёж|купил .*(гк|коин)|\bгк\b", "report.payment"),
    ("report", r"дмят|дм\b|убил|оскорб|читер|чит(ы|ит)|аимбот|мошенник|развод|обманул", "report.complaint"),
    ("report", r"застр|текстур|телепорт|улетел|провалил|эвакуатор|\bбаг|выбраться|помогите вытащить|заспавн", "report.help"),
    ("report", r"как |где |что делать|\?|когда |можно ли|почему ", "report.question"),
    ("complaint", r"читер|\bчит(ы|ит)|аимбот|aim|wallhack|спидхак|fly|летает|стреляет через", "complaint.cheat"),
    ("complaint", r"оскорб|мат\b|родител|мамк|расизм|токсик", "complaint.insult"),
    ("complaint", r"\bдм\b|\bdm\b|убил без|убивает без|дмит|дб\b|\bsk\b|тк\b", "complaint.dm"),
    ("complaint", r"обманул|кинул|скам|не отдал|мошенн|вымога", "complaint.scam"),
    ("complaint", r"продаёт|продает|за реал|рекламир|реклама", "complaint.rmt_ads"),
    ("complaint", r"админ.*(мут|бан|выдал)|жалоба на админ", "complaint.admin"),
]
GREETING = re.compile(r"^(привет|ау|помогите|здравствуйте|салам|hello|hi|\+|\.+|\?+)\W*$", re.I)

store = RulesStore("data/rules.json")


def open_any(p):
    return gzip.open(p, "rt", encoding="utf-8") if p.endswith(".gz") else open(p, encoding="utf-8")


def player_text(t):
    return " ".join(m["text"] for m in t["messages"] if m["role"] in ("player", "reported_player")).lower()


def label(t):
    text = player_text(t)
    if t["kind"] == "complaint":
        for r in store.parse_refs(t.get("violation") or ""):
            if r in REF_TO_CAT:
                return REF_TO_CAT[r], "violation"
        if t.get("verdict") == "invalid_format":
            return "complaint.invalid", "verdict"
    else:
        if len(text) <= 12 and GREETING.match(text.strip()):
            return "report.offtopic", "keyword"
    for kind, rx, cat in KEYWORDS:
        if kind == t["kind"] and re.search(rx, text):
            return cat, "keyword"
    return None


def priority(t, cat):
    p = PRIORITY_BASE[cat]
    # taxonomy: «жалобы без доказательств» -> p3 (кроме взлома/платежей и читов/скама/RMT)
    if t["kind"] == "complaint" and cat in ("complaint.insult", "complaint.dm", "complaint.other") \
            and not t.get("images_count"):
        p = "p3"
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    cats, srcs, skipped, n = Counter(), Counter(), 0, 0
    with open_any(a.inp) as f, open(a.out, "w", encoding="utf-8") as o:
        for line in f:
            t = json.loads(line)
            r = label(t)
            if not r:
                skipped += 1
                continue
            t["category"], t["label_source"] = r
            t["priority"] = priority(t, t["category"])
            o.write(json.dumps(t, ensure_ascii=False) + "\n")
            cats[t["category"]] += 1; srcs[r[1]] += 1; n += 1
            if a.limit and n >= a.limit:
                break
    print(f"размечено {n}, пропущено {skipped}")
    print("источники:", dict(srcs))
    for c, k in cats.most_common():
        print(f"  {c:20s} {k}")


if __name__ == "__main__":
    main()
