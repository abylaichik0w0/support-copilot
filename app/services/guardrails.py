def check_human_needed(category: str, text: str, has_punishment: bool = False) -> tuple[bool, list[str]]:
    reasons = []
    text_lower = text.lower()
    
    # 1. Финансовые операции и донат (всегда человеку)
    if "pay" in category or any(w in text_lower for w in ["донат", "оплат", "деньги", "списали", "покупк"]):
        reasons.append("вопросы платежей и финансовых операций требуют проверки администратором")
        
    # 2. Апелляции блокировок (всегда человеку)
    if "unban" in category or any(w in text_lower for w in ["разбан", "снимите бан", "забанили по ошибке", "жалоба на админ"]):
        reasons.append("апелляции блокировок рассматриваются только старшей администрацией")
        
    # 3. Подозрение на взлом аккаунта (всегда человеку)
    if "hack" in category or any(w in text_lower for w in ["взлом", "угнали аккаунт", "украли акк", "сменили пароль"]):
        reasons.append("подозрение на компрометацию учетной записи")
        
    # 4. Решение о наказании нарушителя (бот не может самостоятельно наказывать)
    if has_punishment:
        reasons.append("решение о наказании подтверждает администратор")
        
    needs_human = len(reasons) > 0
    return needs_human, reasons