"""Teaching walkthrough: using AI as a supervised coding assistant.

This script does not call an AI system. It generates structured prompts and
review checklists for a live teaching exercise.

Teaching goals:
1. Use AI for bounded support tasks.
2. Separate generated suggestions from verified methods.
3. Identify hallucinated endpoints, unsafe scraping advice, and privacy risks.
4. Document AI assistance as part of provenance.
"""

# %% 1. Define the research scenario

research_question = "How do VLOPs report election-related moderation decisions?"
access_route = "DSA Transparency Database extract"
known_docs = "https://transparency.dsa.ec.europa.eu/"


# %% 2. Prompt for API or data-query planning

api_prompt = f"""
You are helping design a platform-data collection workflow.

Research question:
{research_question}

Access route:
{access_route}

Known official documentation:
{known_docs}

Return:
1. the minimum necessary fields;
2. likely filters or grouping variables;
3. pagination or download considerations;
4. data-quality checks;
5. assumptions that must be verified in the official documentation.

Do not invent endpoints, permissions, or legal claims.
"""

print(api_prompt)


# %% 3. Prompt for scraper debugging

scraper_prompt = """
You are helping debug a research scraper.

Observed problem:
The script finds zero records, but the browser visibly shows ten result cards.

Evidence:
- requests.get(url).text contains a JavaScript app shell.
- Browser inspector shows cards under div.result-card after rendering.

Return:
1. likely cause;
2. a safe debugging plan;
3. validation checks;
4. what raw evidence to save;
5. ethical/legal checks before running at scale.

Do not suggest bypassing access controls or anti-bot systems.
"""

print(scraper_prompt)


# %% 4. Human review checklist

review_checklist = [
    "Did the AI invent a non-existent API endpoint or field?",
    "Did it imply permission that must be checked elsewhere?",
    "Did it suggest bypassing access controls, CAPTCHAs, or anti-bot systems?",
    "Did it ask to paste personal or sensitive data into the model?",
    "Did it generate code with network calls that need review before execution?",
    "Did it include validation checks and provenance notes?",
]

for item in review_checklist:
    print("-", item)


# %% 5. Provenance note template

provenance_note = {
    "ai_tool_used": "[tool/model name]",
    "date": "[YYYY-MM-DD]",
    "task": "Generated candidate code/query plan/documentation text.",
    "human_review": "All endpoints, fields, permissions, and code paths checked before execution.",
    "sensitive_data_shared": False,
    "final_status": "AI output treated as draft assistance, not authoritative method.",
}

print(provenance_note)


# %% 6. Teaching prompts

questions = [
    "Which tasks are appropriate to delegate to AI?",
    "Which tasks require human or legal/institutional judgment?",
    "How would prompt injection matter in a browser-agent workflow?",
    "How should AI-generated code be tested before live collection?",
    "What belongs in the methods section of a paper if AI assisted the workflow?",
]

for question in questions:
    print("-", question)
