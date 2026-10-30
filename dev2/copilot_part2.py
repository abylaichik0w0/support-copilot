"""Точка стыка для разработчика 1: пункты правил + черновик ответа.

    from copilot_part2 import PartTwo
    p2 = PartTwo()
    out = p2.run(kind, messages, lang, rule_refs_raw)
    # out = {"draft_reply": {"lang","text","cited"}, "rule_candidates": [(id, prob)], "reasons": [...]}
"""
from rule_predictor import RulePredictor
from rule_search import RuleSearcher
from drafts import generate_draft


class PartTwo:
    def __init__(self, min_prob: float = 0.5):
        self.rp = RulePredictor(min_prob=min_prob)
        self.store = self.rp.store
        self.search = RuleSearcher(self.store)

    def run(self, kind, messages, lang="ru", rule_refs_raw=""):
        reasons = []
        cands = self.rp.predict(kind, messages, rule_refs_raw, top_k=2)
        if not cands and kind == "complaint":
            # запасной вариант: лексический поиск по тексту правил, порог выше, чтобы не цитировать наугад
            text = " ".join(m.get("text", "") for m in messages if m.get("role") in ("player", "reported_player"))
            cands = [(r, s) for r, s in self.search.search(text, top_k=1, min_score=0.3)]
            if cands:
                reasons.append("пункт найден лексическим поиском, уверенность низкая")
        rid = cands[0][0] if cands else None
        if kind == "complaint" and not rid:
            reasons.append("пункт правил не определён, ответ без цитаты")
        draft = generate_draft(self.store, lang, rid)
        draft["cited"] = self.store.sanitize_cited(draft["cited"])  # финальный фильтр
        return {"draft_reply": draft, "rule_candidates": cands, "reasons": reasons}
