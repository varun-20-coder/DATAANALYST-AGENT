"""
ai_agent.py
------------
Wraps the Google Gemini API to provide:
  - Natural language question answering about the uploaded dataset
  - Natural language -> SQL generation
  - Automated business insights & recommendations
  - Executive summary generation

Uses the current, actively-maintained `google-genai` SDK (the old
`google-generativeai` package is deprecated and its models, such as
gemini-1.5-flash, have been sunset). A short list of model names is
tried in order so the app keeps working even as Google rotates which
specific model string is "current".

If no API key is configured, a lightweight offline notice is returned
so the app remains functional in offline/demo mode.
"""

import re
from google import genai

# Tried in order; the first one that succeeds for the user's account/region wins.
CANDIDATE_MODELS = [
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def _get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def _call_gemini(prompt: str, api_key: str) -> str:
    """Low-level helper to call Gemini and return plain text, with error handling.

    Tries each candidate model in turn and returns the first successful
    response. If all fail, returns a readable error message instead of
    raising, so the Streamlit UI never crashes.
    """
    if not api_key:
        return offline_notice()

    client = _get_client(api_key)
    last_error = None

    for model_name in CANDIDATE_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            text = (response.text or "").strip()
            if text:
                return text
        except Exception as e:
            last_error = e
            continue

    return (
        f"⚠️ AI request failed on all candidate models ({', '.join(CANDIDATE_MODELS)}). "
        f"Last error: {last_error}\n\n"
        "This usually means your API key is invalid, the free tier quota was hit, "
        "or Google has rotated the available model names again. You can check "
        "which models your key supports at https://aistudio.google.com/app/apikey."
    )


def ask_question(df_schema: str, question: str, api_key: str) -> str:
    """Answer a natural-language question about the dataset."""
    prompt = f"""You are an expert data analyst. A user uploaded a dataset with this schema
and sample data:

{df_schema}

Answer the user's question clearly and concisely, using only information that
can reasonably be inferred from the schema/sample shown. If precise computation
is needed and you cannot compute it exactly from the sample alone, explain what
calculation would answer it and give your best estimate reasoning.

User question: "{question}"

Answer:"""
    return _call_gemini(prompt, api_key)


def generate_sql_from_nl(question: str, table_name: str, schema_string: str, api_key: str) -> str:
    """Convert a natural language question into a single valid SQLite SQL query."""
    prompt = f"""You are a SQL expert. Convert the user's question into a single valid
SQLite SQL query against a table named "{table_name}" with this schema:

{schema_string}

Rules:
- Return ONLY the SQL query, no explanation, no markdown fences, no semicolon-terminated commentary.
- Use only the table name "{table_name}".
- If the question cannot be answered with SQL, return: SELECT 'UNSUPPORTED' as message;

User question: "{question}"

SQL query:"""
    raw = _call_gemini(prompt, api_key)
    # Clean up common formatting artifacts (markdown fences, stray semicolons/backticks)
    cleaned = re.sub(r"```sql|```", "", raw).strip()
    cleaned = cleaned.rstrip(";").strip()
    return cleaned


def generate_insights(df_schema: str, stats_summary: str, api_key: str) -> str:
    """Generate business insights and recommendations based on dataset summary stats."""
    prompt = f"""You are a senior business intelligence analyst. Given the following dataset
schema and summary statistics, write a concise business analysis with two sections:

1. **Key Insights** (3-5 bullet points) — notable patterns, trends, or anomalies.
2. **Recommended Actions** (3-5 bullet points) — concrete, actionable business recommendations.

Dataset schema:
{df_schema}

Summary statistics:
{stats_summary}

Keep the tone professional and the output well-formatted in Markdown."""
    return _call_gemini(prompt, api_key)


def generate_executive_summary(df_schema: str, insights_text: str, api_key: str) -> str:
    """Generate a short executive summary suitable for the top of a PDF report."""
    prompt = f"""Write a 4-6 sentence executive summary for a business report, based on the
following dataset overview and previously generated insights. Write in plain, confident
business language suitable for leadership stakeholders (no bullet points, no markdown).

Dataset overview:
{df_schema}

Insights already generated:
{insights_text}

Executive summary:"""
    return _call_gemini(prompt, api_key)


# ---------------------------------------------------------------------------
# Offline fallback (used if the user has no API key configured yet)
# ---------------------------------------------------------------------------

def offline_notice() -> str:
    return (
        "ℹ️ No Gemini API key configured. Add your free API key in the sidebar "
        "to enable AI-powered Q&A, SQL generation, and insights. "
        "Get a free key at https://aistudio.google.com/app/apikey"
    )
