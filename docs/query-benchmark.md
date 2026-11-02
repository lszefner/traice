# Query profiling experiment

On 2 November 2026, we ran a local, warm-cache comparison on Neo4j 5.26.32 against the development graph (257 `Article` nodes at measurement time). The experiment selected `2024-10-17`, a date with one matching article, and ran the same parameterized query before and after creating a temporary range index:

```cypher
MATCH (a:Article) WHERE a.published_at = $date
RETURN count(a) AS articles
```

| Measurement | Before | Temporary index |
| --- | ---: | ---: |
| PROFILE operator | NodeByLabelScan + Filter | NodeIndexSeek |
| Total database accesses (DB hits) | 515 | 2 |
| Matching articles | 1 | 1 |
| Median round-trip, 30 runs | 1.404 ms | 1.084 ms |
| Range of round-trips | 0.906–7.645 ms | 0.761–5.745 ms |

These are single-machine, warm-cache measurements including Python driver and network overhead, not a load test or production performance guarantee. The query is an isolated equality-filter experiment, not a currently exposed API endpoint; the experiment does not justify adding a permanent index by itself. Dataset size, selected date, concurrent workload, caches and planner statistics affect results. The temporary index was removed after the run, and a check found no `traice_bench_` indexes remaining.

To reproduce, start Neo4j, import the snapshot, install requirements, then run from the repository root:

```sh
set -a; source .env; set +a
.venv/bin/python scripts/benchmark_query.py
```

The script refuses to run if an `Article.published_at` index already exists, picks a least-frequent non-null date, warms each case five times, records 30 client-side samples, and prints both full PROFILE trees. It creates a uniquely named temporary index, waits for it to come online, and drops only that index in a `finally` block. A forced process termination or connection loss may interrupt cleanup; inspect `SHOW INDEXES` and remove only the experiment's `traice_bench_…` index if necessary. Run on a disposable development database, not a production instance. The measured graph had previously been imported more than once; Neo4j merges nodes by ID but a changing snapshot can leave older nodes, so its 257 articles need not equal the current snapshot size.

For an opt-in real Cypher test of the article-to-paper path and edge provenance after import, run `make test-integration` with `.env` loaded into the shell. It does not modify graph data.
