"""
AI Prompt Library

Reusable prompt templates for all AI operations.
No prompt duplication. Each template is rendered with context data.

Sprint 3.11.0 - AI Operations Assistant.
"""

from typing import Any

SYSTEM_PROMPT = (
    "You are Mission Control AI Operations Assistant. "
    "You analyze infrastructure data and provide concise, actionable insights. "
    "You NEVER execute changes directly. You only advise, explain, summarize, "
    "recommend, prioritize, and predict. "
    "Always include confidence scores and affected systems in your analysis."
)


def render(template: str, variables: dict[str, Any]) -> str:
    """Render a prompt template with variables."""
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


# ------------------------------------------------------------------ #
# Alert Summary                                                        #
# ------------------------------------------------------------------ #

ALERT_SUMMARY = """Analyze the following alerts and provide a concise summary:

Alerts:
{alert_list}

Provide:
1. Top critical issues
2. Affected systems
3. Likely root causes
4. Recommended immediate actions

Focus on actionable insights. Be concise."""


# ------------------------------------------------------------------ #
# Incident Summary                                                     #
# ------------------------------------------------------------------ #

INCIDENT_SUMMARY = """Explain the following incident:

Source: {source}
Host: {host_name}
Severity: {severity}
Message: {message}
Affected Systems: {affected_systems}

Provide:
1. What happened (plain English)
2. Possible causes (bullet list)
3. Recent related events
4. Recommended actions (numbered list)
5. Confidence level"""


# ------------------------------------------------------------------ #
# Backup Analysis                                                      #
# ------------------------------------------------------------------ #

BACKUP_ANALYSIS = """Analyze the backup infrastructure:

{backup_data}

Provide:
1. Backup health overview
2. Failed jobs and reasons
3. Repository capacity status
4. Risk assessment
5. Recommendations to improve backup reliability"""


# ------------------------------------------------------------------ #
# Infrastructure Summary                                               #
# ------------------------------------------------------------------ #

INFRASTRUCTURE_SUMMARY = """Summarize the current infrastructure state:

{infrastructure_data}

Provide:
1. Overall health score
2. Components needing attention
3. Capacity concerns
4. Trend observations
5. Priority actions"""


# ------------------------------------------------------------------ #
# Executive Summary                                                    #
# ------------------------------------------------------------------ #

EXECUTIVE_SUMMARY = """Generate an executive summary of IT operations:

{operations_data}

Provide a brief (3-5 bullet) executive summary suitable for leadership.
Focus on business impact, risk, and decisions needed."""


# ------------------------------------------------------------------ #
# Daily Report                                                         #
# ------------------------------------------------------------------ #

DAILY_REPORT = """Generate a daily operations report:

{daily_data}

Include:
1. Key events today
2. Issues resolved
3. Ongoing concerns
4. Overnight outlook
5. Recommendations for tomorrow"""


# ------------------------------------------------------------------ #
# Weekly Report                                                        #
# ------------------------------------------------------------------ #

WEEKLY_REPORT = """Generate a weekly operations report:

{weekly_data}

Include:
1. Week highlights
2. Incident trends
3. Capacity changes
4. Recommendations
5. Items for next week"""


# ------------------------------------------------------------------ #
# Root Cause Analysis                                                  #
# ------------------------------------------------------------------ #

ROOT_CAUSE_ANALYSIS = """Perform root cause analysis:

Incident: {incident_description}
Timeline: {timeline}
Affected Systems: {affected_systems}
Related Alerts: {related_alerts}

Provide:
1. Most likely root cause (with confidence %)
2. Contributing factors
3. Evidence supporting the conclusion
4. Suggested verification steps
5. Prevention recommendations"""


# ------------------------------------------------------------------ #
# Maintenance Recommendation                                           #
# ------------------------------------------------------------------ #

MAINTENANCE_RECOMMENDATION = """Analyze infrastructure and recommend maintenance:

{infrastructure_data}

Provide:
1. Systems needing maintenance (priority ordered)
2. Specific maintenance tasks
3. Estimated downtime
4. Risk of postponement
5. Recommended schedule"""


# ------------------------------------------------------------------ #
# Capacity Planning                                                    #
# ------------------------------------------------------------------ #

CAPACITY_PLANNING = """Analyze capacity and predict needs:

{capacity_data}

Provide:
1. Current utilization by component
2. Growth trends
3. Predicted exhaustion dates
4. Scaling recommendations
5. Budget considerations"""


# ------------------------------------------------------------------ #
# Natural Language Query                                               #
# ------------------------------------------------------------------ #

NATURAL_LANGUAGE_QUERY = """You are Mission Control AI Operations Assistant.

User question: {query}

Available infrastructure data:
{context_data}

Answer the question based on the data. Be concise and specific.
Include confidence level and affected systems.
Never recommend executing changes directly."""


# Template registry for dynamic lookup
TEMPLATES = {
    "alert_summary": ALERT_SUMMARY,
    "incident_summary": INCIDENT_SUMMARY,
    "backup_analysis": BACKUP_ANALYSIS,
    "infrastructure_summary": INFRASTRUCTURE_SUMMARY,
    "executive_summary": EXECUTIVE_SUMMARY,
    "daily_report": DAILY_REPORT,
    "weekly_report": WEEKLY_REPORT,
    "root_cause_analysis": ROOT_CAUSE_ANALYSIS,
    "maintenance_recommendation": MAINTENANCE_RECOMMENDATION,
    "capacity_planning": CAPACITY_PLANNING,
    "natural_language_query": NATURAL_LANGUAGE_QUERY,
}


def get_template(name: str) -> str:
    """Get a prompt template by name."""
    return TEMPLATES.get(name, "")


def render_template(name: str, variables: dict[str, Any]) -> str:
    """Get and render a prompt template by name."""
    template = get_template(name)
    if not template:
        return ""
    return render(template, variables)
