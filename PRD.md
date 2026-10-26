# Product Requirements Document: Graph-Based Movie Recommender

## 1. Project overview

### Product name

**MovieGraph**

### Purpose

MovieGraph helps users discover movies through their ratings, shared genres, and similarities with other users. It explains recommendations using evidence from the graph and allows users to ask questions in natural language.

### Example

A user asks:

> “Recommend science-fiction movies I might like and explain why.”

MovieGraph returns a ranked list with reasons grounded in actual ratings and graph connections, such as shared genres or movies liked by similar users.

### Project level

**Level 2 — Graph engineering**, with graph algorithms and an ML workflow included to address the grading rubric.

---

## 2. Goals and success criteria

The project is successful when:

- A user can receive personalized movie recommendations through an API.
- Each recommendation includes evidence from the graph.
- A user can explore similar movies and trending movies.
- A user can ask a natural-language question and receive a response based on a validated, read-only graph query.
- The application runs through Docker Compose and can be demonstrated by the team.
- The team can explain and defend its graph model, queries, AI guardrails, and engineering choices.

### Measurable completion targets

| Area | Target |
|---|---|
| API | At least four endpoints, including at least three advanced graph queries |
| Graph | At least three node labels, three relationship types, two constraints, and appropriate indexes |
| Graph algorithms | An in-memory GDS projection and at least two algorithms |
| Machine learning | A documented link-prediction or node-classification workflow |
| Testing | At least 60% test coverage, with unit, API, Cypher, and connectivity tests |
| Code quality | Pylint score of at least 9.5/10 |
| Infrastructure | At least three Docker Compose services and one image published to a public registry |
| Collaboration | At least one substantial merged pull request per member and meaningful code review |
| Demonstration | Successful natural-language request and rejected invalid or unsafe generated query |

---

## 3. Users

### Primary user: movie viewer

Wants to find movies that match their preferences and understand why they were recommended.

### Secondary user: project evaluator

Wants to inspect the graph, test API endpoints, review the AI component, and understand the team’s technical decisions.

---

## 4. Data

### Primary source

Use **MovieLens `ml-latest-small`** for initial development. It contains movies, genres, user ratings, and tags.

A larger MovieLens dataset may be used for performance experiments if time and infrastructure permit.

### Data preparation requirements

The ingestion process must:

- Import movies, users, ratings, genres, and selected tags.
- Handle missing or malformed values.
- Avoid creating duplicates when run more than once.
- Record the data source and document any filtering decisions.
- Create the required constraints and indexes.

MovieLens users are dataset records, so the initial product will use an existing user ID rather than require account creation.

---

## 5. Proposed graph model

```text
(:User)-[:RATED {rating, timestamp}]->(:Movie)
(:Movie)-[:IN_GENRE]->(:Genre)
(:User)-[:TAGGED {timestamp}]->(:Tag)
(:Movie)-[:HAS_TAG]->(:Tag)
```

### Main entities

- **User:** An anonymized MovieLens user.
- **Movie:** A movie with an ID, title, and other available metadata.
- **Genre:** A category such as Comedy or Science Fiction.
- **Tag:** A user-supplied descriptive term.

### Modeling decisions to validate

- Represent genres as nodes so queries can traverse shared genres across movies.
- Store ratings as relationship properties because the rating describes a user’s relationship with a movie.
- Evaluate how to represent tags and their authorship. The final model must preserve enough information to avoid incorrectly implying that every user who used a tag applied it to every movie with that tag.

The final schema may change after inspecting the dataset. The README must compare it with a basic AI-generated schema and explain the team’s decisions.

---

## 6. Functional requirements

### 6.1 Personalized recommendations

**Endpoint:** `GET /api/users/{user_id}/recommendations`

The system must:

- Recommend movies the user has not already rated.
- Rank candidates using a documented approach based on graph information.
- Return the movie ID, title, score, and a short evidence-based explanation.
- Support a result limit.

**Example explanation:**

> “Recommended because users with similar ratings liked this movie, and it shares genres with movies you rated highly.”

### 6.2 Similar movies

**Endpoint:** `GET /api/movies/{movie_id}/similar`

Return movies related to a selected movie using a documented similarity measure, such as shared genres, tags, or user-rating patterns.

### 6.3 Trending movies

**Endpoint:** `GET /api/movies/trending`

Return ranked movies using a documented calculation based on the available ratings and timestamps. Explain any limitations of calling older dataset activity “trending.”

### 6.4 Recommendation explanations

**Endpoint:** `GET /api/users/{user_id}/recommendations/{movie_id}/explanation`

Return the graph evidence behind a recommendation, such as:

- Relevant shared genres.
- Movies the user rated highly.
- Similar users and their ratings, where applicable.
- The graph paths or structured evidence used.

An AI-generated explanation must not introduce evidence absent from the returned graph data.

### 6.5 Community discovery

**Endpoint:** `GET /api/users/{user_id}/discover`

Use a documented graph community or similarity approach to find movies that may interest the user.

### 6.6 Natural-language questions

**Endpoint:** `POST /api/ask`

The user submits a question such as:

> “Which comedies are popular among users who liked Toy Story?”

The system must:

1. Receive the question.
2. Generate a Cypher query using the documented graph schema.
3. Validate the query before execution.
4. Execute only an allowed, read-only query.
5. Return a structured answer and relevant query or evidence.
6. Return a clear error if the query is rejected or cannot be answered.

Guardrails must restrict write operations, unsafe procedures, unbounded results, and access outside the permitted graph schema. The team must demonstrate both a successful question and a rejected unsafe or invalid query.

---

## 7. Graph algorithms and machine learning

### Graph algorithms

Use Neo4j Graph Data Science to create an in-memory projection and apply at least two appropriate algorithms. Candidate choices include:

- **Similarity:** Find users or movies with similar graph neighborhoods.
- **Community detection:** Group related users or movies for discovery.

The team must explain why each algorithm fits the problem and what its output means.

### ML workflow

Implement one documented workflow, such as **link prediction** to estimate which user–movie connections may form in the future.

The workflow should:

- Clearly define the prediction target and evaluation metric.
- Separate training and evaluation data appropriately, preferably using rating timestamps where suitable.
- Avoid leaking information from the evaluation set into training.
- Compare results with a simple baseline.
- Document limitations and distinguish predictions from observed ratings.

---

## 8. Technical architecture

### Required services

Docker Compose will run at least:

1. **Neo4j:** Graph database and GDS.
2. **FastAPI:** API, recommendation logic, and AI integration.
3. **Nginx:** Reverse proxy in front of the API.

An LLM may be accessed through a provider or run locally with Ollama. Credentials must be stored in `.env`, never committed, and documented through `.env.example`.

### Other technical requirements

- Python 3.11+, Neo4j Python driver, Pydantic, and pytest.
- Swagger/OpenAPI documentation available at `/docs`.
- Meaningful HTTP errors and input validation.
- Parameterized queries, pagination or limits where appropriate, and performance measurements.
- GitHub Actions for linting and tests.
- A Makefile with the commands required by the specification.

---

## 9. Parallel team organization

The project is designed for **five workstreams**. Each person owns a workstream, but everyone reviews and understands the integrated system. With fewer than five people, combine adjacent workstreams.

| Owner | Workstream | Main responsibilities |
|---|---|---|
| 1 | **Graph and data** | Dataset exploration, schema, constraints, indexes, import scripts, graph documentation |
| 2 | **Recommendations and GDS** | Similarity, community detection, recommendation logic, GDS projection, ML experiment |
| 3 | **API and integration** | FastAPI structure, Pydantic contracts, endpoints, error handling, integration of services |
| 4 | **AI and guardrails** | Natural-language-to-Cypher, query validation, structured responses, AI evaluation |
| 5 | **Infrastructure and quality** | Docker Compose, Nginx, Makefile, CI, test infrastructure, deployment image |

### Shared responsibilities

- **Team lead:** Coordinates the backlog, integration, review assignments, and balanced contributions.
- **Every member:** Creates at least one substantial pull request, reviews teammates’ work, documents their decisions, and prepares to explain their contribution.
- **Documentation and demo:** Owned jointly; each workstream supplies its own setup, design decisions, and demo material.

### Interfaces to agree on before implementation

Hold a short integration meeting and commit an initial version of:

1. **Graph schema:** Node labels, relationship types, IDs, and property names.
2. **API contracts:** Endpoint paths and example request/response JSON.
3. **Service boundaries:** Which module owns queries, recommendation logic, and query validation.
4. **Development dataset:** A small shared fixture for local development and tests.
5. **Configuration:** Environment variable names and service addresses.
6. **Definition of done:** Tests, documentation, and review expectations for every pull request.

These contracts let each workstream proceed against stable examples while the full implementation is still being built. Changes to shared contracts should be proposed in a pull request and communicated to affected owners.

### Parallel work sequence

**Phase 1 — Agree on foundations**

- Owner 1 inspects MovieLens and proposes the schema and sample data.
- Owner 3 proposes API contracts and a minimal application skeleton.
- Owner 5 prepares the repository, Compose stack, and CI.
- Owner 2 researches suitable recommendation methods using the sample data.
- Owner 4 designs the AI interface and guardrail rules.

**Integration checkpoint:** The team agrees on schema, contracts, configuration, and test fixture.

**Phase 2 — Build independently**

- Owner 1 implements ingestion and database setup.
- Owner 2 implements recommendation and graph-analysis services against the agreed schema.
- Owner 3 implements endpoints against agreed service interfaces, using temporary fixtures where necessary.
- Owner 4 implements the AI pipeline and validation using a controlled schema and mocked execution.
- Owner 5 builds service health checks, test infrastructure, and CI.

**Integration checkpoint:** Import the shared fixture and connect the first working recommendation endpoint end to end.

**Phase 3 — Integrate and evaluate**

- Connect all API endpoints to the real graph.
- Run and evaluate the graph algorithms and ML workflow.
- Connect the AI component to the validated query executor.
- Test failure cases, measure query performance, and fix integration issues.
- Complete diagrams, README, notebook, and screenshots.

**Integration checkpoint:** Run the complete application from a clean setup and rehearse the live demo.

### Git and review rules

- Keep `main` stable and use short-lived feature branches.
- Open pull requests early so others can see interfaces and dependencies.
- Require a review before merging, with at least two constructive review comments per pull request, as specified.
- Merge small compatible changes frequently; avoid waiting until the end to combine work.
- Assign a clear owner to every integration issue.

---

## 10. Required deliverables

The repository must include:

- Complete application and ingestion code.
- `docker-compose.yml`, Dockerfiles where needed, `.env.example`, and `.gitignore`.
- `Makefile`, `requirements.txt`, and `.pylintrc`.
- Automated tests and GitHub Actions workflows.
- A complete `README.md` with setup, API examples, screenshots, data sources, architecture, graph schema, and modeling rationale.
- A graph-schema diagram and system-architecture diagram.
- The AI-schema comparison appendix.
- `demo.ipynb` with graph exploration and visualizations.
- Evidence of merged pull requests and team contributions.
- Documentation of the AI guardrails and evaluation.
- A link to at least one public container image.

---

## 11. Live demonstration

The team will demonstrate:

1. Starting the services and checking Neo4j connectivity.
2. Exploring the graph and using Swagger.
3. Requesting recommendations and showing their graph-based explanations.
4. Showing the two graph algorithms and the ML evaluation.
5. Asking a successful natural-language question.
6. Rejecting an invalid or unsafe generated query.
7. Running the required Makefile, lint, and test commands.
8. Showing contribution history and merged pull requests.

---

## 12. Scope priorities

### Must have

- Data ingestion and a justified graph schema.
- Four or more functional API endpoints.
- Personalized recommendations with graph-backed explanations.
- Natural-language-to-Cypher with guardrails.
- Docker Compose, tests, CI, documentation, and live demo.
- Two GDS algorithms and an ML workflow for the grading criteria.

### Nice to have, if time permits

- A simple web interface.
- Larger-scale MovieLens experiments.
- Filtering recommendations by genre or release year.
- Comparing several recommendation algorithms.