"""Поиск по правилам: TF-IDF на символьных n-граммах (CPU, миллисекунды, устойчив к опечаткам)."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from rules_store import RulesStore


class RuleSearcher:
    def __init__(self, store: RulesStore):
        self.store = store
        self.ids = list(store.rules)
        docs = [store.rules[i].corpus().lower() for i in self.ids]
        self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, max_features=300000)
        self.matrix = self.vec.fit_transform(docs)

    def search(self, query: str, top_k: int = 2, min_score: float = 0.12):
        """[(rule_id, score)] по убыванию; ниже порога пусто (лучше без цитаты, чем с выдуманной)."""
        q = self.vec.transform([(query or "").lower()])
        scores = linear_kernel(q, self.matrix).ravel()
        order = scores.argsort()[::-1][:top_k]
        return [(self.ids[i], float(scores[i])) for i in order if scores[i] >= min_score]
