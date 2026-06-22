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

# These three variables make the prompt concrete. Students can edit them and see
# how a better-specified research scenario produces a more useful AI response.
research_question = "How do VLOPs report election-related moderation decisions?"
# access_route tells the AI what kind of data infrastructure we are using. A DSA
# Transparency Database extract has different constraints than scraping or an
# authenticated platform API.
access_route = "DSA Transparency Database extract"
# known_docs anchors the prompt in official documentation. The model should use
# this as a reference point, not invent undocumented endpoints or fields.
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

# The f before the triple-quoted string makes this an f-string: Python replaces
# {research_question}, {access_route}, and {known_docs} with the values above.
# We print the prompt instead of sending it automatically so students can inspect
# and edit it before using any AI tool.
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

# This prompt describes evidence rather than just asking "fix my scraper." The
# evidence distinguishes a static-fetch problem from a selector typo: requests
# saw only a JavaScript shell, while the browser saw rendered result cards.
print(scraper_prompt)


# %% 4. Human review checklist

review_checklist = [
    # Endpoint and field hallucination are common because models often infer
    # plausible API shapes from examples instead of checking actual docs.
    "Did the AI invent a non-existent API endpoint or field?",
    # Permission claims should come from law, policy, or institutional review,
    # not from model output.
    "Did it imply permission that must be checked elsewhere?",
    # This line keeps the workflow on compliance and observation, not evasion.
    "Did it suggest bypassing access controls, CAPTCHAs, or anti-bot systems?",
    # AI tools may transmit prompts to external services, so sensitive data must
    # be handled according to the project data-management plan.
    "Did it ask to paste personal or sensitive data into the model?",
    # Network calls, filesystem writes, and credential handling should be checked
    # before any generated code is run.
    "Did it generate code with network calls that need review before execution?",
    # A useful AI response should include ways to test and document the workflow,
    # not just code that appears to work once.
    "Did it include validation checks and provenance notes?",
]

for item in review_checklist:
    print("-", item)


# %% 5. Provenance note template

provenance_note = {
    # Record the tool or model name because outputs can differ across tools and
    # versions.
    "ai_tool_used": "[tool/model name]",
    # Date matters because AI systems and platform documentation change.
    "date": "[YYYY-MM-DD]",
    # The task should be specific: query planning, selector repair, code drafting,
    # documentation, etc.
    "task": "Generated candidate code/query plan/documentation text.",
    # Human review states which parts were verified before use.
    "human_review": "All endpoints, fields, permissions, and code paths checked before execution.",
    # False here means no personal or sensitive data was shared with the AI tool.
    "sensitive_data_shared": False,
    # final_status reminds students that AI output is draft assistance, not an
    # authoritative method or source.
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
