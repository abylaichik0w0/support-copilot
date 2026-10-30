from app.models.schemas import TriageRequest, TriageResponse, ExtractedInfo, DraftReply
from app.core.preprocessor import fix_encoding, detect_language, extract_entities
from app.services.guardrails import check_human_needed
from app.rag.engine import rag_engine
from app.services.llm import generate_llm_draft


def run_triage(req: TriageRequest) -> TriageResponse:
    # 1. Исправление кодировки cp1251
    for m in req.messages:
        m.text = fix_encoding(m.text)
        
    full_text = " ".join([m.text for m in req.messages])
    
    # 2. Определение языка и извлечение сущностей
    lang = detect_language(full_text)
    extracted = extract_entities(req.messages)
    
    # 3. RAG-поиск по rules.json
    matched_rules = rag_engine.search(full_text, top_k=2)
    
    # 4. Вызов LLM
    llm_res = generate_llm_draft(full_text, lang, matched_rules)
    category = llm_res.get("category", "other")
    priority = llm_res.get("priority", "p2")
    
    # 5. Защита от галлюцинаций (проверка по белому списку правил)
    raw_cited = llm_res.get("cited", []) + extracted.get("rule_refs", [])
    valid_cited = rag_engine.sanitize_citations(list(set(raw_cited)))
    
    # 6. Guardrails (проверка на необходимость передачи человеку)
    is_complaint = (req.kind == "complaint")
    needs_human, reasons = check_human_needed(category, full_text, has_punishment=is_complaint)
    
    return TriageResponse(
        lang=lang,
        category=category,
        priority=priority,
        is_spam_or_duplicate=False,
        extracted=ExtractedInfo(**extracted),
        draft_reply=DraftReply(
            lang=lang,
            text=llm_res.get("text", "Здравствуйте! Обращение принято."),
            cited=valid_cited
        ),
        needs_human=needs_human,
        confidence=0.88,
        reasons=reasons
    )