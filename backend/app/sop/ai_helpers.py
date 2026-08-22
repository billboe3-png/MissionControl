"""
Mission Control SOP AI Helpers
"""
from app.ai.prompts import SYSTEM_PROMPT, render


async def ai_review_sop(entity) -> dict:
    text = "\n".join(str(value) for value in entity.__dict__.values() if isinstance(value, str) and value)
    prompt = render("sop_review", {"sop_title": entity.title, "sop_content": text})
    from app.ai.ai_provider import get_ai_provider
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
    prompt = render("sop_ai_query", {"query": question, "sop_context": context})
    from app.ai.ai_provider import get_ai_provider
    result = await get_ai_provider().complete(prompt, SYSTEM_PROMPT)
    answer = result.get("text", "No approved SOP is currently available.")
    return {
        "answer": answer,
        "sources": [item.title for item in approved[:5]],
        "confidence_score": 0.8 if approved else 0.2,
    }
