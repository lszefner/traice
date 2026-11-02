# Local stack

Copy `.env.example` to `.env` and set a local Neo4j password of at least eight characters. Run `make docker-run` to start Neo4j 5 with GDS, the API, and Nginx. Access the API through `http://localhost:8080`, and Neo4j Browser at `http://localhost:7474`. The first start downloads GDS and may take several minutes. Persistent named volumes retain database contents and plugins across restarts; `docker compose down` stops the services without deleting them.

For local development, `make install` prepares `.venv`, `make run` starts the API, and `make test` runs tests without requiring Neo4j. Export the Neo4j credentials from `.env` before `make test-integration` when the stack is running (for example, `set -a; source .env; set +a`). `make lint` enforces Pylint 9.5. The API and database health checks are visible via `docker compose ps`.

If the password in `.env` is changed after the database has initialized, updating the environment alone does not change its stored password. Change it through Neo4j instead, or deliberately delete the data volume only when the data is no longer needed.

The natural-language feature expects an Ollama server reachable from the API container and the configured model already pulled. `.env.example` documents the host address and model. The rest of the stack can start without Ollama.
