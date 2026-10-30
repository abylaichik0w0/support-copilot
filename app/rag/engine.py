import json
import os
import re
from rank_bm25 import BM25Okapi


class RulesRAG:
    def __init__(self, rules_path: str = "data/raw/rules.json"):
        self.valid_rule_ids = set()
        self.corpus_docs = []
        self.doc_ids = []
        self.bm25 = None
        
        if os.path.exists(rules_path):
            self._load_rules(rules_path)

    def _load_rules(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sections = data.get("sections", [])
        for sec in sections:
            for rule in sec.get("rules", []):
                rule_id = str(rule.get("id"))
                self.valid_rule_ids.add(rule_id)
                
                text = f"Пункт {rule_id}: {rule.get('title', '')}. {rule.get('description', '')}. Наказание: {rule.get('punishment', '')}"
                self.corpus_docs.append(text)
                self.doc_ids.append(rule_id)

        tokenized_corpus = [self._tokenize(doc) for doc in self.corpus_docs]
        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)

    def _tokenize(self, text: str):
        return re.findall(r'\w+', text.lower())

    def search(self, query: str, top_k: int = 2) -> list[dict]:
        if not self.bm25:
            return []
        tokens = self._tokenize(query)
        scores = self.bm25.get_scores(tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in ranked_indices:
            if scores[idx] > 0:
                results.append({
                    "id": self.doc_ids[idx],
                    "content": self.corpus_docs[idx]
                })
        return results

    def sanitize_citations(self, cited: list[str]) -> list[str]:
        """Удаляет выдуманные номера правил, защищая от штрафа за галлюцинации."""
        return [r for r in cited if r in self.valid_rule_ids]


rag_engine = RulesRAG()