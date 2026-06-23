# Day 4: DSA Access and Platform Research Tools

## What This Day Is About

Day 4 moves from researcher-initiated collection to regulated and
platform-provided access infrastructures. This includes DSA researcher access,
the DSA Transparency Database, ad repositories, Meta Content Library, TikTok
Research API, and other platform research tools.

The day has two central messages. First, the Digital Services Act creates new
rights and procedures for studying systemic risks, but those procedures require
careful scoping, justification, and data-security planning. Second,
platform-provided data must be audited. Official access does not automatically
mean complete, unbiased, or analysis-ready access.

## 1. The DSA as Research Infrastructure

The Digital Services Act regulates online intermediaries in the European Union.
For researchers, its most important platform-data provisions concern Very Large
Online Platforms and Very Large Online Search Engines. These services have
heightened obligations because of their scale and potential systemic risks.

The DSA matters methodologically because it changes the access landscape. It
does not simply give researchers a download button. It creates structured
mechanisms, eligibility conditions, oversight roles, and procedural pathways.

This is why DSA access should be taught as infrastructure rather than as a
single legal citation. Infrastructure includes forms, portals, authorities,
data catalogues, review timelines, security requirements, access environments,
and dispute points. Each part affects what research can be done. A brilliant
research question may still fail if the requested data are not proportionate, if
the security plan is weak, or if the access modality prevents the planned
analysis.

Researchers must connect their projects to systemic risks. These may include
dissemination of illegal content, effects on fundamental rights, civic discourse
and electoral processes, public health, protection of minors, gender-based
violence, and other societal harms.

The systemic-risk link matters because it narrows the purpose of access.
Article 40 mechanisms are not general curiosity tools. A request should explain
how the data are necessary for studying or detecting systemic risks in the EU.
This requires translating a social-scientific research question into the
language of risk, necessity, proportionality, and public interest.

## 2. Article 40(12) and Article 40(4)

Article 40(12) concerns researcher access to publicly accessible data. It is
important because it recognizes that public-interface data can be relevant for
systemic-risk research, but it does not erase ethical, legal, or data-protection
responsibilities.

Article 40(4) concerns vetted researcher access to non-public data. This is a
more formal access route. Researchers must meet conditions, formulate a specific
request, justify necessity and proportionality, and satisfy data-security and
independence requirements.

The distinction matters. If a research question can be answered with public data
or transparency data, a request for non-public data may be excessive. If the
research question requires recommender-system logs, moderation metadata, or
non-public risk-related data, public data may be insufficient.

## 3. Digital Services Coordinators and the Data Access Portal

Digital Services Coordinators are national authorities involved in DSA
implementation. In researcher access, they help assess and route requests. The
DSA Data Access Portal provides a procedural entry point for applications.

Students should understand that DSA access is not only a technical interface. It
is a governed process. A request may involve a research institution, a national
coordinator, the Commission, the platform provider, and secure access
arrangements.

The timeline matters for research design. DSA access may not fit a project that
requires immediate data. A strong project plan should account for procedural
time, possible negotiation over scope, and secure access modalities.

## 4. Data Catalogues and Access Modalities

Data catalogues describe available data assets, fields, and structures. They can
help researchers formulate specific requests. But catalogues should not be
treated as the entire universe of possible research data. They are aids to
scoping, not necessarily complete maps of platform systems.

Access modalities define how data will be made available. Possibilities include
data exports, APIs, secure processing environments, platform-hosted analysis
tools, or other controlled access systems. Each modality has consequences for
analysis. A secure environment may restrict export. An API may rate limit
queries. A platform-hosted environment may limit methods or software.

Students should ask: what work can actually be done under this access modality?
Can raw data be inspected? Can code be exported? Can results be reproduced? Can
other researchers verify the analysis?

A secure processing environment, for example, may protect sensitive data but
restrict export of row-level records. That changes the analysis workflow. A
researcher may need to bring code to the data rather than data to the code. An
API modality may allow repeated queries but impose rate limits or field
restrictions. A static export may be easier to analyze but harder to update.
Access modality is therefore not an administrative detail; it is part of the
method.

## 5. Drafting a Strong Request

A strong Article 40 request begins with a research question, not a data wish
list. It identifies the platform, service, systemic risk, population, time
window, requested fields, and why each field is necessary.

Each requested field should be justified. "Interesting" is not enough.
Researchers should explain why the field is needed, whether a less intrusive
alternative exists, and how the field will be protected.

The request should include a data-protection and security plan. This means
storage location, access controls, retention period, deletion plan, publication
plan, and treatment of personal or sensitive data.

The request should also include a public-interest and dissemination plan. DSA
researcher access is tied to public-interest research, not private intelligence
gathering.

## 6. Platform Research Tools

Platform research tools such as Meta Content Library or TikTok Research API are
important because they offer structured access to some platform data. They may
be easier to use than scraping and more official than public-interface
collection.

But platform research tools are not complete mirrors of platforms. They may
exclude certain content types, accounts, metrics, time periods, or geographies.
They may strip metadata. They may impose query limits or rate limits. They may
define visibility in ways that do not match user experience.

Researchers should read eligibility rules, data dictionaries, query
documentation, and known limitations before designing analysis.

Platform research tools also raise an epistemic problem. They can appear more
authoritative than scraped data because they are official. But official does not
mean complete. The platform defines the searchable universe, the query language,
the returned metadata, and sometimes the ranking or sampling logic. A researcher
should ask: what public content can I observe that this tool does not return?
What metadata do users see that the tool strips out? Which accounts, languages,
regions, or media types are excluded?

## 7. DSA Transparency Database

The DSA Transparency Database contains statements of reasons submitted by online
platforms about content moderation decisions. The unit of analysis is a
statement of reasons, not all harmful content and not the full moderation
pipeline.

This distinction is crucial. Counting statements by platform or category does
not automatically measure how much harmful content exists or how much moderation
a platform performs. Counts are shaped by reporting practices, enforcement
policies, schema interpretation, automation, and platform behavior.

Important fields may include platform name, category, content type, date fields,
decision visibility, automated detection, and automated decision. Each field
requires interpretation. For example, automated detection and automated decision
are related but not identical. Detection concerns how content was flagged.
Decision concerns how the moderation outcome was produced.

## 8. Data Quality Auditing

Every platform-provided dataset should be audited before substantive analysis.
Audit questions include:

- How many rows are present?
- What is the unit of analysis?
- Are there duplicate IDs?
- Which fields are missing?
- Are categories comparable across platforms?
- Are there time gaps?
- Did rate limits or query limits shape the data?
- Is there a benchmark or public-interface sample for comparison?

Missingness is not only a technical nuisance. Metadata stripping may make a
research question impossible. Scope narrowing may exclude the most relevant
content. Rate limits may bias time windows.

Auditing should happen before substantive modeling or interpretation. A model
cannot repair a dataset whose collection process excluded the core population of
interest. A descriptive table can be misleading if categories are not comparable
across platforms. A large N can create false confidence when the missingness is
systematic.

For DSA and platform-tool data, a useful audit report should include the access
route, unit of analysis, schema version if known, time period, row counts,
missing fields, duplicate identifiers, platform coverage, category coverage,
rate-limit or query-limit notes, and a short interpretation of what the dataset
cannot support.

## End-of-Day Questions

- Which DSA access route fits a given research question?
- What makes a data request necessary and proportionate?
- What is the unit of analysis in the DSA Transparency Database?
- What does a platform research API reveal and hide?
- How would you audit a platform-provided dataset before analysis?
