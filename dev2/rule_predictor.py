"""Предсказание нарушенного пункта правил по тексту жалобы (обучается на train).

Обучение (1-2 минуты, CPU):
    python rule_predictor.py train --train tickets_train_jsonl.gz
Проверка на валидации:
    python rule_predictor.py eval --valid tickets_valid.jsonl
Использование в сервисе:
    from rule_predictor import RulePredictor
    rp = RulePredictor();  rp.predict(kind, messages, rule_refs_raw)  -> [(rule_id, prob)]
"""
import argparse, gzip, json, os
import joblib
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from rules_store import RulesStore

MODEL = os.path.join(os.path.dirname(__file__), "models", "rule_clf.joblib")
RULES = os.path.join(os.path.dirname(__file__), "data", "rules.json")


def features(store: RulesStore, messages, rule_refs_raw: str) -> str:
    txt = " ".join(m.get("text", "") for m in messages if m.get("role") in ("player", "reported_player"))
    refs = " ".join("REF_" + r.replace(" ", "_").replace(".", "_") for r in store.parse_refs(rule_refs_raw or ""))
    return txt.lower() + " " + refs


def _read(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        for l in f:
            yield json.loads(l)


def dataset(store, path):
    X, y = [], []
    for t in _read(path):
        if t["kind"] != "complaint":
            continue
        g = store.parse_refs(t.get("violation") or "")
        if g:
            X.append(features(store, t["messages"], t.get("rule_refs_raw"))); y.append(g[0])
    return X, y


def train(train_path):
    store = RulesStore(RULES)
    X, y = dataset(store, train_path)
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2, max_features=200000)
    clf = LogisticRegression(max_iter=300, C=5).fit(vec.fit_transform(X), y)
    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    joblib.dump((vec, clf), MODEL)
    print(f"обучено на {len(y)} жалобах, классов {len(clf.classes_)}, модель: {MODEL}")


class RulePredictor:
    def __init__(self, min_prob: float = 0.5):
        self.store = RulesStore(RULES)
        self.vec, self.clf = joblib.load(MODEL)
        self.min_prob = min_prob

    def predict(self, kind, messages, rule_refs_raw="", top_k=2):
        """[(rule_id, prob)] только для жалоб и только если уверенность >= min_prob.
        Все id проходят белый список, выдуманного пункта здесь быть не может."""
        if kind != "complaint":
            return []
        p = self.clf.predict_proba(self.vec.transform([features(self.store, messages, rule_refs_raw)]))[0]
        out = []
        for i in p.argsort()[::-1][:top_k]:
            rid = self.clf.classes_[i]
            if p[i] >= self.min_prob and self.store.sanitize_cited([rid]):
                out.append((rid, float(p[i])))
        return out


def evaluate(valid_path):
    rp = RulePredictor(min_prob=0.0)
    n = 0; rows = []
    for t in _read(valid_path):
        if t["kind"] != "complaint":
            continue
        g = rp.store.parse_refs(t.get("violation") or "")
        if not g:
            continue
        pr = rp.predict("complaint", t["messages"], t.get("rule_refs_raw"), top_k=1)
        rows.append((pr[0][1], pr[0][0] == g[0]))
    print(f"жалоб с известным пунктом: {len(rows)}; top-1 без порога: {sum(c for _, c in rows)/len(rows):.1%}")
    for th in (0.3, 0.5, 0.7, 0.9):
        sel = [c for p, c in rows if p >= th]
        print(f"  порог {th}: отвечаем на {len(sel)/len(rows):.0%} жалоб, точность {sum(sel)/max(len(sel),1):.1%}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["train", "eval"])
    ap.add_argument("--train", default="tickets_train_jsonl.gz")
    ap.add_argument("--valid", default="tickets_valid.jsonl")
    a = ap.parse_args()
    train(a.train) if a.cmd == "train" else evaluate(a.valid)
