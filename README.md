# MovieGraph

MovieGraph is a graph-based movie discovery project using MovieLens ratings. It will recommend unrated movies with graph-backed evidence, explore similar and popular movies, and answer natural-language questions through restricted read-only graph queries. See [PRD.md](PRD.md) for the complete requirements.

## Fast demo plan

1. Agree on graph schema, endpoint examples, environment variables, and a small shared fixture. Preserve tag, user, movie, and timestamp together so tag authorship is accurate.
2. Bring up Neo4j with GDS, FastAPI, and Nginx in Compose. Import the fixture, then MovieLens `ml-latest-small`, repeatably.
3. Deliver a vertical slice: select an existing user ID, request recommendations in Swagger, and show structured graph evidence. Add similar and historical trending queries.
4. Add the natural-language path with constrained query generation and a validated, read-only execution boundary. Demonstrate both an allowed query and a rejected unsafe query.
5. Run two GDS algorithms and a leakage-conscious link-prediction experiment with a baseline. Finish quality targets, documentation, image publication, and a clean-start rehearsal.

The first demo is a milestone, not completion of the grading requirements. Swagger can serve as the initial interface.

## Parallel workstreams

| Workstream | Ownership | First integration result |
| --- | --- | --- |
| Graph and data | Schema, constraints, fixtures, idempotent import | Queryable shared fixture |
| Recommendations and GDS | Ranking, evidence, algorithms, ML evaluation | Recommendation query against fixture |
| API and integration | Contracts, FastAPI, endpoints, error handling | Swagger endpoint connected to graph |
| AI and guardrails | Query generation, validation, read-only execution, evaluation | Allowed and rejected query examples |
| Infrastructure and quality | Compose, CI, testing, image publication | Healthy reproducible stack |

Agree on interfaces before parallel coding; use short-lived branches and integrate the vertical slice early. Each person should own and review substantive changes, with at least one substantial merged pull request per member and two constructive review comments per pull request as required by the PRD. Agents can assist each workstream; human contributors remain responsible for review and understanding.

## Commit and integration policy

Make small, coherent commits when a meaningful unit is ready. Distribute ownership across real contributors and workstreams; do not manufacture commits or misrepresent authorship to equalize counts. Track contribution and review coverage as work proceeds. Protect `main` through reviews and passing checks when the team configures repository settings.

## Acceptance

The full checklist is in the PRD, including four or more endpoints, three advanced graph queries, two GDS algorithms, a documented ML workflow, at least 60% coverage, Pylint 9.5/10, a public image, and the live demo. Record actual results rather than assuming the targets have passed.
