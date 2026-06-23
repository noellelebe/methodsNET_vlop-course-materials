# Day 5: AI-Augmented and Reproducible Workflows

## What This Day Is About

The final day brings the course together. Students learn how AI can assist
platform-data collection without replacing human judgment, and how to turn
collection scripts into reproducible research workflows.

The key message is that modern platform research requires both technical
adaptability and disciplined documentation. AI can help draft code, inspect
HTML, summarize errors, and propose checks. But it can also hallucinate
endpoints, invent permissions, leak sensitive data, and make fragile workflows
look more reliable than they are.

Reproducibility is the counterweight. A well-designed workflow records
parameters, raw data, processed data, logs, code versions, manifests, codebooks,
and limitations.

## 1. Useful Roles for AI

AI tools can be useful when tasks are bounded and outputs can be verified. They
can help explain API documentation, draft query parameters, generate boilerplate
requests code, propose CSS selectors, interpret error messages, write parsing
functions, draft codebooks, and suggest data-quality checks.

For example, a student might ask an AI tool to draft a plan for collecting data
from an API. A good prompt should include the research question, the official
documentation link, the access route, the necessary fields, and a warning not to
invent endpoints or permissions.

AI is most useful as a supervised assistant. It can speed up routine work, but
the researcher must verify every claim against official documentation, inspect
generated code, and test outputs on small examples.

In this course, AI should be presented as a tool for producing drafts and
diagnostics, not as a source of authority. A useful AI interaction has a narrow
task, clear context, and a verification plan. "Write a scraper for TikTok" is
too broad and risky. "Given this small non-sensitive HTML excerpt, suggest two
possible selectors and explain how to test them" is much safer and more
teachable.

Students should also learn that AI output is shaped by the prompt. If the
prompt omits the official documentation, the model may fill gaps with plausible
but false assumptions. If the prompt omits legal constraints, the model may
suggest workflows that are technically possible but inappropriate.

## 2. Dangerous Roles for AI

AI becomes dangerous when it is treated as an authority. It may invent API
parameters, cite non-existent policies, suggest endpoints that are not
documented, or imply that scraping is allowed because content is public. It may
also generate code that silently collects more data than necessary or stores
sensitive data insecurely.

One risk is hallucination. A model may produce plausible but false code or
documentation. Another risk is prompt injection. If an AI tool reads web pages,
those pages may contain text that attempts to influence the model's behavior.
Researchers should treat web content as data, not instructions.

A third risk is privacy leakage. Pasting scraped content, user profiles, private
metadata, or sensitive examples into an AI service may violate a data management
plan or legal obligation.

AI also creates reproducibility problems. The same prompt may produce different
outputs across models, dates, or settings. A generated selector may work on the
page shown in the prompt but fail on other pages. A generated API query may use
an outdated parameter. For this reason, AI-generated code should be treated like
untrusted draft code: read it, test it, document what was accepted, and discard
what cannot be verified.

## 3. AI Provenance

If AI assists a workflow, document it. An AI assistance log should record the
tool or model, date, task, input sensitivity, whether output was used, and how it
was verified.

This does not mean AI use is automatically problematic. It means AI assistance
is part of the research process. If a model generated a parser, suggested a
selector, or drafted a codebook, the methods documentation should say how that
output was checked.

Students should distinguish between AI-generated suggestions and verified
methods. The final workflow belongs to the researcher.

## 4. Reproducible Workflow Structure

A reproducible project separates code, configuration, raw data, processed data,
and reports.

Configuration contains parameters: query terms, dates, page limits, output
directories, and access choices. Parameters should not be hidden deep inside
code if students or collaborators need to reproduce the workflow.

Raw data preserve source-shaped evidence. For APIs, this may mean JSON
responses. For scraping, raw HTML and screenshots. For DSA transparency data,
original extracts or documented downloads.

Processed data are analysis-ready tables. They are convenient but less complete
than raw evidence.

Reports include manifests, provenance files, audit summaries, logs, and
codebooks. These files explain how to interpret the data.

Reproducibility has two audiences. The first is another researcher who wants to
understand or repeat the workflow. The second is the future version of the same
researcher who will return to the project weeks or months later. Good structure
is a kindness to both. A workflow that only runs in the author's memory is not a
reproducible workflow.

## 5. Manifests and Codebooks

A manifest describes a run. It should include creation time, script name,
parameters, input paths, output paths, row counts, software versions if
available, and known limitations.

A codebook describes variables. It should include column names, definitions,
source fields, transformations, missingness meanings, privacy sensitivity, and
analysis cautions.

Together, manifests and codebooks make a dataset interpretable. Without them, a
CSV is just a table with uncertain origins.

## 6. Logging, Scheduling, and Monitoring

Some collection workflows run once. Others run repeatedly. Scheduled scrapers or
API collectors need logs and monitoring. A log should record start time, end
time, parameters, request counts, status codes, errors, retries, and output
paths.

Monitoring means checking whether the workflow still behaves as expected. Does
the scraper still find records? Are fields missing? Did the number of records
drop unexpectedly? Did an API return errors or rate-limit responses?

Breakage is normal. Silent breakage is the danger.

For scheduled collectors, the absence of errors is not enough. A scraper can
run successfully and collect zero records because a selector changed. An API
collector can run successfully while receiving only partial data because a rate
limit was reached. Monitoring should therefore include substantive checks:
record counts, missingness, duplicate rates, date coverage, and examples of
extracted records.

## 7. Combining Sources

Combining API data, scraped data, and transparency data can be powerful, but it
introduces matching risks. Common join keys include URLs, platform IDs, account
IDs, timestamps, text hashes, and canonical links.

Every join should be audited. False matches can create stronger errors than
missing data because they produce confident but wrong relationships. A workflow
should record matching rules, unmatched records, duplicates, and ambiguity.

Students should avoid overclaiming. Combining partial views does not create a
complete view. It creates a more complex partial view.

Source integration should be documented as carefully as collection. If records
are matched by URL, describe canonicalization rules. If records are matched by
timestamp, describe time zones and tolerance windows. If records are matched by
text, describe normalization and collision risks. Every join rule creates false
positive and false negative possibilities.

## 8. Final Workflow Critique

The final exercise asks students to design a small platform-data workflow. The
goal is not maximum data volume. The goal is methodological clarity.

A strong workflow includes a research question, platform, access route,
parameter discovery plan, fields, time window, collection logic, raw/processed
storage structure, provenance plan, data-quality audit, AI-use statement if
applicable, ethical review, and limitations.

The limitations paragraph is not a weakness. It is evidence that the researcher
understands the dataset.

## End-of-Day Questions

- Which parts of a collection workflow can AI safely assist?
- Which claims must be verified outside AI output?
- What belongs in an AI assistance log?
- What does a manifest record?
- What does a codebook record?
- What would make an end-to-end workflow reproducible?
- What can your final dataset not prove?
