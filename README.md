# SignalGraph — proposed AI news intelligence project

SignalGraph connects AI news stories to research papers, organizations and topics. It helps a reader explore what is being reported, trace explicit references to research, and see where possible connections remain unverified. This is a project proposal; the application has not yet been implemented.

## The product

A reader can explore the evidence behind an AI story, compare coverage across sources, follow connections between research and reporting, and ask natural-language questions. Each answer should link to its supporting records and distinguish a documented relationship from an inferred suggestion. A news mention is not proof of endorsement, causation or technical accuracy.

## Proposed data and graph

- **News:** a small, dated snapshot of AI-related article metadata from selected publisher feeds, subject to source access and usage terms.
- **Research:** AI-related paper metadata and citation links from [OpenAlex](https://help.openalex.org/data/works/).
- **Graph:** `Article`, `Publisher`, `Paper`, `Organization` and `Topic` nodes; article-to-publisher, article-to-topic, paper-to-topic and paper-to-paper citation relationships. An article-to-paper reference is recorded as explicit only when supported by a source link or a manually verified record. Candidate matches are separate, labeled suggestions with provenance and validation status.

The two-source join is a project risk: coverage, publisher permissions, stable links and match quality must be measured before finalizing the schema. A pinned fixture and dated source snapshot make the demo reproducible.

## Proposed API and demonstration

1. `GET /api/articles/{id}/evidence` — sources, topics and explicitly linked papers.
2. `GET /api/topics/{id}/connections` — bounded paths connecting coverage and research.
3. `GET /api/papers/{id}/coverage` — related articles, separating explicit references from candidates.
4. `GET /api/topics/{id}/trends` — article and paper counts over time, with dataset-window caveats.
5. `POST /api/ask` — natural-language-to-Cypher with validation, read-only access, bounded execution and structured evidence. Demonstrate a successful request and rejection of an unsafe generated query.

At least two endpoints must incorporate pathfinding or graph algorithms, and at least three must demonstrate advanced graph queries. Exact contracts depend on the data spike.

## Delivery sequence

1. Inspect both sources, validate a small joinable dataset, decide a defensible graph schema and establish API contracts and a shared fixture.
2. Bring up Neo4j/GDS, FastAPI and Nginx; import the fixture and demonstrate an evidence endpoint and an early guarded natural-language query.
3. Import a reproducible source snapshot; implement paths, coverage and trends, with source citations and explicit uncertainty.
4. Add a GDS projection and two justified algorithms, plus a time-split link-prediction experiment against a simple baseline. Define the target from observable explicit links and check that there are enough positive examples before committing to it; otherwise choose a feasible classification task.
5. Complete testing, performance measurements, documentation, public image publication and a clean-start demo rehearsal.

## Parallel work and contribution

Parallel streams: data and graph modeling; graph queries, algorithms and ML; API integration; LLM and guardrails; infrastructure and quality. Agree on shared contracts first and integrate a small end-to-end slice early. Use feature branches and substantive, honestly attributed commits. Every team member should have a substantial merged PR, with meaningful reviews and at least two constructive comments per PR. Track both contribution balance and understanding; do not manufacture commits.

## Assignment requirements

The supplied assignment permits a custom project with comparable scope. The full rubric includes at least three Compose services, four endpoints with three advanced queries, pathfinding or graph algorithms in two endpoints, GDS projection and two algorithms, an ML workflow, NL-to-Cypher or an agent, tests with 60% coverage, Pylint at least 9.5, a public container image, diagrams, a notebook and documented modeling decisions. Level 3/3+ requires a genuine LangGraph agent; the initial proposal targets Level 2 while retaining the rubric's GDS and ML requirements. Confirm the project and its level with the instructor.

Repository name `moviegraph` is temporary and still reflects the original idea.
