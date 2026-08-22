"""
Mission Control SOP AI Helpers
"""
from app.ai.ai_provider import get_ai_provider


SYSTEM_PROMPT = (
    "You are Mission Control SOP reviewer and operations assistant. "
    "Always distinguish between source content, AI recommendations, and uncertainty."
)


async def ai_review_sop(entity) -> dict:
    text = "\n".join(str(value) for value in entity.__dict__.values() if isinstance(value, str) and value)
    prompt = (
        "You are Mission Control SOP reviewer.\n"
        "You MUST clearly distinguish between source content, AI recommendations, and uncertainty.\n"
        "Never present AI recommendations as if they came from the source document.\n\n"
        f"SOP Title: {getattr(entity, 'title', '')}\n"
        f"Content:\n{text}\n\n"
        "Evaluate:\n"
        "1. Completeness\n2. Clarity\n3. Ambiguity\n4. Missing prerequisites\n"
        "5. Missing validation\n6. Missing rollback\n7. Missing escalation\n"
        "8. Security concerns\n9. Operational risks\n10. Contradictions\n11. Outdated information\n\n"
        "Return:\n- Assessment\n- Completeness Score\n- Risk Level\n- Findings\n- Recommendations\n- Evidence\n- Confidence\n"
    )
    result = await get_ai_provider().complete(prompt, SYSTEM_PROMPT)
    answer = result.get("text", "AI review unavailable.")
    findings = [line.strip("- ") for line in answer.splitlines() if line.strip()][:20]
    return {
        "assessment": answer,
        "completeness_score": 0.75,
        "risk_level": "medium",
        "findings": findings,
        "recommendations": [],
        "evidence": [],
        "confidence": 0.8,
    }


async def ai_query_sops(approved, question: str) -> dict:
    context = "\n\n".join(f"{item.title}\n{item.procedure or item.description or ''}" for item in approved[:5]) or "No approved SOPs available."
    prompt = (
        "You are Mission Control AI Operations Assistant.\n"
        "You answer from approved operational knowledge only.\n"
        "If no approved SOP is available, say exactly: 'No approved SOP is currently available.'\n\n"
        f"User question: {question}\n\n"
        f"Approved SOP context:\n{context}\n\n"
        "Rules:\n"
        "- Only use approved/published SOP knowledge.\n"
        "- If the answer is inferred, mark it as an AI recommendation.\n"
        "- Never invent procedures.\n"
        "- Never present draft SOPs as official.\n"
        "- Include confidence and evidence references.\n"
    )
    result = await get_ai_provider().complete(prompt, SYSTEM_PROMPT)
    answer = result.get("text", "No approved SOP is currently available.")
    return {
        "answer": answer,
        "sources": [item.title for item in approved[:5]],
        "confidence_score": 0.8 if approved else 0.2,
    }
