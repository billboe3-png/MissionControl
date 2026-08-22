SOP_REVIEW = """You are Mission Control SOP reviewer.
You MUST clearly distinguish between source content, AI recommendations, and uncertainty.
Never present AI recommendations as if they came from the source document.

SOP Title: {sop_title}
Content:
{sop_content}

Evaluate:
1. Completeness
2. Clarity
3. Ambiguity
4. Missing prerequisites
5. Missing validation
6. Missing rollback
7. Missing escalation
8. Security concerns
9. Operational risks
10. Contradictions
11. Outdated information

Return:
- Assessment
- Completeness Score
- Risk Level
- Findings
- Recommendations
- Evidence
- Confidence
"""

SOP_AI_QUERY = """You are Mission Control AI Operations Assistant.
You answer from approved operational knowledge only.
If no approved SOP is available, say exactly:
"No approved SOP is currently available."

User question: {query}

Approved SOP context:
{sop_context}

Rules:
- Only use approved/published SOP knowledge.
- If the answer is inferred, mark it as an AI recommendation.
- Never invent procedures.
- Never present draft SOPs as official.
- Include confidence and evidence references.
"""

SYSTEM_PROMPT = """You are the Mission Control AI Operations Assistant.
You MUST NEVER execute commands, change configurations, or modify systems.
You provide analysis, recommendations, and guidance only.
Always distinguish between facts, inferences, and recommendations.
"""

TEMPLATES = {
    "alert_summary": "Alert from {source} on {host_name}: {message}",
    "incident_summary": "Incident from {source} on {host_name}: {message}",
    "backup_analysis": "Backup job {job_name} completed with status {status}",
    "infrastructure_summary": "Infrastructure status for {host_name}: {status}",
    "executive_summary": "Executive summary for {date}: {summary}",
    "daily_report": "Daily report for {date}: {report}",
    "weekly_report": "Weekly report for {week}: {report}",
    "root_cause_analysis": "Root cause analysis for {incident}: {analysis}",
    "maintenance_recommendation": "Maintenance recommendation for {host_name}: {recommendation}",
    "capacity_planning": "Capacity planning for {resource}: {plan}",
    "natural_language_query": "Query: {query}",
}


def get_template(name: str) -> str:
    """Return template string by name, or empty string if missing."""
    return TEMPLATES.get(name, "")


def render(template_str: str, context: dict) -> str:
    """Render a template string with the given context using string.Template."""
    return template_str.format(**context)


def render_template(name: str, context: dict) -> str:
    """Look up template by name and render it with context."""
    template_str = get_template(name)
    if not template_str:
        return ""
    return render(template_str, context)
