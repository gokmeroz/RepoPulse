# RepoPulse — Internal Implementation Roadmap

> This document is the implementation source of truth.
> The README is the public product overview.
> When they conflict, fix whichever is wrong.

---

## Critical Path

The sequence below is not arbitrary. Each version unblocks the next.

```
0.0.0  Plan and README
  └─► 0.1.0  All containers start (proves the monorepo, Docker, and service skeletons work)
        └─► 0.2.0  Messaging works end-to-end (proves RabbitMQ topology before adding GitHub)
              └─► 0.3.0  GitHub data lands in PostgreSQL (proves ingestion before ML needs it)
                    └─► 0.4.0  NumPy baseline works (proves features before adding a model)
                          └─► 0.5.0  PyTorch model trains and is measured honestly
                                └─► 0.6.0  Full pipeline: rank → diversity → explain → feedback
                                      └─► 1.0.0  Reliability, evaluation, docs, release
```

You cannot train without data. You cannot rank without features. You cannot declare the model
better without evaluation. The order enforces these dependencies.

---

## Highest-Risk Assumptions

Listed in descending priority — address earliest.

1. **Docker Compose wiring is correct** (v0.1.0).
   If services cannot reach each other or the database, nothing downstream works.
   Mitigation: validate health checks before writing any business logic.

2. **RabbitMQ manual ACK/NACK is implemented correctly** (v0.2.0).
   Incorrect acknowledgement means silent message loss or infinite redelivery.
   Mitigation: write a demo consumer that deliberately crashes; verify the message reappears.

3. **GitHub API rate limits are respected** (v0.3.0).
   An unauthenticated client gets 60 requests/hour. A user with 500 stars requires ~10 pages
   of starred repos, plus metadata calls. This can exhaust the limit quickly.
   Mitigation: always use a token in development; add rate-limit logging from day one.

4. **Implicit feedback is too sparse for the PyTorch model** (v0.5.0).
   A user with 30 stars gives 30 positive examples. After negative sampling, the dataset
   may be too small to meaningfully train. The NumPy baseline must always work as a fallback.
   Mitigation: build the baseline first and verify it produces useful results before training.

5. **Sentence embeddings are slow or too large** (v0.4.0).
   A pretrained embedding model may be several hundred MB and slow on CPU.
   Mitigation: make the embedding model configurable; start with a small model (e.g. all-MiniLM-L6-v2).

---

## Scope Exclusions (MVP)

These will not be built in v1.0.0:

- Frontend of any kind
- Authentication or authorization layer
- Redis caching
- Vector database
- LLM API calls (no GPT, Claude, Gemini)
- Kubernetes
- Kafka
- Distributed model training
- Collaborative filtering (cross-user signals)
- Real-time streaming recommendations
- Graph-based candidate discovery
- Cloud deployment (AWS, GCP, Azure)
- CLI tool (may be added after core system works)

---

## Version Definitions

---

### Version 0.0.0 — README and Project Plan

**Status:** In progress

**Goal:** Document the vision, architecture, and implementation order before writing a single line of application code.

**Deliverables:**
- `README.md` — public product and architecture overview
- `docs/project-plan.md` — this file

**Files created:**
- `README.md` (rewritten)
- `docs/project-plan.md` (new)

**Dependencies:** None. This is the starting point.

**Acceptance criteria:**
- README clearly explains what RepoPulse does, who it is for, how it works, and what is planned vs. available.
- README is honest: every unimplemented section is marked `[PLANNED]`.
- Project plan documents all versions, dependencies, risks, and learning objectives.
- No application code exists.

**Tests:** None. This version produces only documentation.

**Learning objectives:**
- Understand the product problem and why async processing is necessary.
- Be able to describe what each service owns and what it is forbidden to do.
- Understand why the versions are ordered the way they are.
- Understand the difference between the NumPy baseline and the PyTorch ranker.

**Risks:**
- Over-planning leads to analysis paralysis. Mitigation: the plan exists to clarify order, not to predict every implementation detail.

---

### Version 0.1.0 — Project Foundation

**Goal:**

```
All service containers start
+ infrastructure is healthy
+ each process has a clear entry point and responsibility
```

**Deliverables:**
- Monorepo directory structure (all folders, no business logic yet)
- Shared contracts package (`packages/contracts/`) — skeleton with empty modules
- Root `.gitignore`
- Root `.env.example` with all required variables documented
- Root `Makefile` with targets: `up`, `down`, `logs`, `test`, `shell-api`, `shell-ingestion`, `shell-recommender`
- `docker-compose.yml` with all six containers
- PostgreSQL container with health check
- RabbitMQ container (management image) with health check
- Minimal API service: FastAPI app, `/health`, `/ready`, structured logging
- Minimal ingestion service: Python process, connects to RabbitMQ on start, structured logging
- Minimal recommender service: Python process, connects to RabbitMQ on start, structured logging
- `Dockerfile` per service (multi-stage builds)
- `pyproject.toml` per service
- Initial startup tests (verify health endpoints respond)

**Files created or modified:**
- `docker-compose.yml`
- `Makefile`
- `.gitignore`
- `.env.example`
- `services/api-service/` (full skeleton)
- `services/ingestion-service/` (full skeleton)
- `services/recommender-service/` (full skeleton)
- `packages/contracts/` (skeleton)
- `infrastructure/rabbitmq/definitions.json`

**Dependencies:** v0.0.0 complete.

**Acceptance criteria:**
- `docker compose config` succeeds with no warnings.
- `docker compose up --build` starts all six containers.
- All health checks reach `healthy` state.
- `GET /health` returns 200.
- `GET /ready` returns 200 when RabbitMQ and PostgreSQL are reachable, 503 otherwise.
- Ingestion and recommender services log "Connected to RabbitMQ" on startup.
- `make test` runs and passes basic startup tests.

**Tests:**
- `test_health_endpoint` — assert 200 from `/health`
- `test_ready_endpoint_when_healthy` — assert 200 from `/ready` with services up
- `test_worker_connects_to_rabbitmq` — assert ingestion and recommender log a successful connection

**Learning objectives:**
- Understand the difference between a Docker image and a container.
- Understand how Docker Compose networking lets containers find each other by service name.
- Understand the difference between a health check (liveness) and a readiness check.
- Understand why ingestion and recommender are separate processes, not modules inside the API.
- Understand why services do not import each other's application code.

**Risks:**
- Dependency resolution across Python packages in a monorepo can be tricky.
  Mitigation: install the contracts package as an editable local dependency in each service.
- RabbitMQ takes several seconds to start. Workers must retry their connection, not fail immediately.
  Mitigation: implement a simple retry loop with exponential backoff on startup.

---

### Version 0.2.0 — Messaging and Job Orchestration

**Goal:**

```
HTTP request
→ job record created (status: queued)
→ RabbitMQ command published
→ worker consumes command
→ worker publishes completion event
→ API consumes event
→ job status updated to: completed
```

**Deliverables:**
- Message envelope schema (in contracts package)
- Command schemas: `GitHubSyncRequested`, `ModelTrainingRequested`, `RecommendationsGenerationRequested`
- Event schemas: `GitHubSyncCompleted`, `GitHubSyncFailed`, `ModelTrainingCompleted`, etc.
- Topic exchanges: `repopulse.commands`, `repopulse.events`
- Dead-letter exchange: `repopulse.dead-letter`
- Queues and bindings (see CLAUDE.md §8)
- API: `POST /v1/users` (create user, return user ID)
- API: `POST /v1/sync` (create job record, publish command, return job ID)
- API: `GET /v1/jobs/{job_id}` (return job status)
- API: job-events consumer (updates job status from events)
- Ingestion worker: consumer reads the command, does fake work, publishes `github.sync.completed`
- Recommender worker: same pattern for `model.training.requested`
- Correlation IDs threaded through all messages and logs
- Manual ACK/NACK on all consumers
- Prefetch = 1 on all consumers
- Retry counter in envelope; NACK-without-requeue after max retries

**Files created or modified:**
- `packages/contracts/repopulse_contracts/commands.py`
- `packages/contracts/repopulse_contracts/events.py`
- `packages/contracts/repopulse_contracts/envelope.py`
- `packages/contracts/repopulse_contracts/identifiers.py`
- `services/api-service/app/api/` (users, sync, jobs routes)
- `services/api-service/app/database/` (job and user ORM models)
- `services/api-service/app/messaging/` (publisher, event consumer)
- `services/api-service/app/repositories/` (job repo, user repo)
- `services/ingestion-service/app/consumers/` (sync consumer — fake impl)
- `services/ingestion-service/app/messaging/` (publisher)
- `services/recommender-service/app/consumers/` (training consumer — fake impl)
- `services/recommender-service/app/messaging/` (publisher)
- `infrastructure/rabbitmq/definitions.json` (exchanges, queues, bindings)

**Dependencies:** v0.1.0 complete (containers start and are healthy).

**Acceptance criteria:**
- `POST /v1/sync` returns `{ "job_id": "...", "status": "queued" }` immediately.
- Polling `GET /v1/jobs/{job_id}` shows `queued → processing → completed`.
- RabbitMQ management UI shows the message flow correctly.
- Duplicate messages with the same `message_id` do not create duplicate job records.
- A worker that crashes after consuming a message (before ACK) redelivers the message.
- After `MAX_RETRIES` failures, the message appears in the dead-letter queue.

**Tests:**
- `test_sync_request_returns_job_id`
- `test_job_transitions_to_completed`
- `test_duplicate_message_is_idempotent`
- `test_failed_message_reaches_dead_letter_after_max_retries`
- `test_correlation_id_is_consistent_across_messages`

**Learning objectives:**
- Understand the difference between synchronous and asynchronous request handling.
- Understand topic exchanges, routing keys, queue bindings.
- Understand the difference between a command and an event.
- Understand ACK, NACK, and why you only ACK after successful processing.
- Understand correlation IDs and idempotency.

**Risks:**
- Manual ACK logic is easy to get wrong (ACKing before work is done; never ACKing on error).
  Mitigation: write a test that verifies message redelivery after a simulated crash.
- The API's event consumer must not block the HTTP server's event loop.
  Mitigation: run the event consumer in a background thread or asyncio task.

---

### Version 0.3.0 — GitHub Ingestion

**Goal:**

```
GitHub username
→ real GitHub API calls
→ normalized repository data in PostgreSQL
```

**Deliverables:**
- GitHub REST client with optional token, timeout, and rate-limit handling
- Starred-repository fetch with pagination (all pages, not just first)
- Repository metadata fetch (description, topics, languages, README, timestamps, flags)
- Candidate discovery: search by topics, languages, and learning goals from the sync command
- Data normalization layer (GitHub JSON → internal domain objects)
- Ingestion ORM models and repositories
- Database migrations for the ingestion schema
- Idempotent upserts (re-running sync does not duplicate rows)
- `sync_runs` table records start time, end time, status, and counts
- Ingestion consumer now does real work instead of fake work
- Ingestion publishes `github.sync.completed` with counts, or `github.sync.failed` with reason

**Files created or modified:**
- `services/ingestion-service/app/github/` (REST client)
- `services/ingestion-service/app/services/` (sync orchestration logic)
- `services/ingestion-service/app/repositories/` (ORM repositories)
- `services/ingestion-service/app/database/` (ORM models, migrations)
- `services/ingestion-service/app/consumers/sync_consumer.py` (real implementation)
- `infrastructure/migrations/` (Alembic or SQL migration files)

**Dependencies:** v0.2.0 complete (messaging works end-to-end).

**Acceptance criteria:**
- `POST /v1/sync` with a real GitHub username results in repositories appearing in the database.
- A user with 50 stars: all 50 starred repos are fetched and stored.
- Missing README, empty topics, and missing language data are handled without crashing.
- Re-running the sync for the same user does not duplicate rows.
- Rate-limit headers are logged but never logged at debug level with the token visible.
- At least 10 candidate repositories are discovered per sync.
- All ingestion tests pass using mocked GitHub HTTP responses.

**Tests:**
- `test_fetch_starred_repositories_paginates_correctly`
- `test_missing_readme_is_handled_gracefully`
- `test_empty_topics_stored_as_empty_list`
- `test_duplicate_repository_is_upserted_not_duplicated`
- `test_rate_limit_warning_is_logged`
- `test_candidate_discovery_returns_at_least_ten_repos`
- `test_sync_run_record_is_created_with_correct_counts`

**Learning objectives:**
- Understand pagination in REST APIs.
- Understand rate limiting and why it matters for background workers.
- Understand data normalization (GitHub's shape → your shape).
- Understand idempotent database writes.
- Understand service data ownership (ingestion schema is ingestion's territory).

**Risks:**
- GitHub API responses change shape or add unexpected nulls.
  Mitigation: use Pydantic models to parse GitHub responses; fail loudly if shape is wrong.
- README content may be very large (hundreds of KB). Storing raw content naively bloats the DB.
  Mitigation: truncate README to a maximum size (e.g. 50 KB) before storing.
- Candidate discovery may find too few or too many repos.
  Mitigation: cap candidates at a configurable limit (e.g. 200); document the heuristic.

---

### Version 0.4.0 — Feature Engineering and NumPy Baseline

**Goal:**

```
Repository data in PostgreSQL
→ numerical feature vectors
→ developer preference profile
→ ranked candidates with explainable scores
```

**Deliverables:**
- Text preprocessing (lowercase, truncate, clean)
- Sentence-embedding pipeline (small pretrained model; cached to disk or DB column)
- Topic multi-hot vectors (with a fixed vocabulary built from ingested data)
- Language distribution vectors (normalized to sum to 1)
- Metadata feature vector (log-normalized stars/forks, activity decay, flags)
- Developer preference profile (weighted average of starred-repo feature vectors)
- Cosine similarity function (with tests)
- Jaccard similarity function (with tests)
- Activity decay function (with tests)
- Novelty score (penalizes repos already well-represented in user profile)
- NumPy weighted scorer (the full formula from CLAUDE.md §14)
- Component-level score breakdown for explanations
- `repository_features` table (stores computed vectors per repository)
- Recommender consumer now scores candidates using the baseline
- Recommendation results written to `recommendations` table
- `GET /v1/recommendations` returns baseline results

**Files created or modified:**
- `services/recommender-service/app/features/` (all feature builders)
- `services/recommender-service/app/ranking/baseline.py`
- `services/recommender-service/app/explanations/` (generates reasons from score breakdown)
- `services/recommender-service/app/database/` (feature and recommendation ORM models)
- `services/recommender-service/app/consumers/recommend_consumer.py` (real baseline impl)
- `services/api-service/app/api/recommendations.py`

**Dependencies:** v0.3.0 complete (repository data is in PostgreSQL).

**Acceptance criteria:**
- Every ingested repository can be converted to a feature vector deterministically.
- Running the feature builder twice on the same repository produces the same vector.
- A preference profile is generated from a user's starred repositories.
- The NumPy baseline returns a ranked list of at least 10 candidates.
- Every result contains a score breakdown (text, topic, language, activity, quality, novelty).
- Explanations are generated from actual score components, not templates.
- The baseline works with zero PyTorch model artifacts present.
- Unit tests verify: cosine similarity, Jaccard similarity, activity decay, weighted score formula.

**Tests:**
- `test_cosine_similarity_of_identical_vectors_is_one`
- `test_cosine_similarity_of_orthogonal_vectors_is_zero`
- `test_jaccard_similarity_known_values`
- `test_activity_decay_recent_repo_scores_higher`
- `test_language_vector_sums_to_one`
- `test_feature_vector_is_deterministic`
- `test_baseline_scorer_ranks_by_score_descending`
- `test_explanation_includes_top_contributing_components`

**Learning objectives:**
- Understand what a vector is and why numerical representations of text/topics/languages are useful.
- Understand normalization and why it matters for combining different scales.
- Understand cosine similarity geometrically (angle between vectors, not magnitude).
- Understand Jaccard similarity (intersection over union for sets).
- Understand the difference between a ranking score and a probability.

**Risks:**
- Embedding models may not be installed or may be slow on first run.
  Mitigation: make the embedding model configurable; provide a TF-IDF fallback that requires no download.
- Topic vocabulary may be very large (thousands of unique GitHub topics).
  Mitigation: keep only the top-N most frequent topics; cap vocabulary size.
- Feature vectors may have mismatched dimensions across repos (different topic vocab sizes).
  Mitigation: build vocabulary once at training time; pad or truncate consistently.

---

### Version 0.5.0 — PyTorch Ranking Model

**Goal:**

```
Starred repositories (implicit positive feedback)
→ training pairs (positive + sampled negative)
→ PyTorch feed-forward ranker trained with margin ranking loss
→ evaluation metrics on held-out data
```

**Deliverables:**
- Positive example builder (starred repos with feature vectors)
- Random negative sampler
- Hard negative sampler (similar-but-less-aligned candidates)
- Time-aware train/validation/test split
- `RankingDataset` (PyTorch Dataset)
- `DataLoader` with controlled batch size and seed
- Feed-forward ranking network (architecture from CLAUDE.md §15)
- Training loop with validation loss per epoch
- Model checkpoint: save best checkpoint, not just final epoch
- Model metadata: saved alongside checkpoint (feature dimensions, vocab version, epoch, seed)
- `model_runs` and `model_metrics` tables
- Precision@K, Recall@K, MRR, NDCG@K evaluation
- Honest comparison: baseline vs. PyTorch ranker on same held-out set
- Model artifacts saved to the shared Docker volume

**Files created or modified:**
- `services/recommender-service/app/datasets/`
- `services/recommender-service/app/models/ranker.py`
- `services/recommender-service/app/models/train.py`
- `services/recommender-service/app/evaluation/`
- `services/recommender-service/app/artifacts/`
- `services/recommender-service/app/consumers/train_consumer.py` (real impl)
- `services/recommender-service/app/database/` (model_runs, model_metrics)
- `scripts/run_evaluation.py`

**Dependencies:** v0.4.0 complete (feature vectors exist in PostgreSQL).

**Acceptance criteria:**
- Training runs to completion on CPU in under 2 minutes for a user with ~50 stars.
- Random seed is set; re-running training produces the same result.
- Model artifact is saved to the shared volume and reloadable.
- Evaluation metrics are computed from a held-out set, not the training set.
- A table comparing baseline vs. model is printed to logs and saved to `model_metrics`.
- The model is only declared better than the baseline if metrics confirm it.

**Tests:**
- `test_dataset_shapes_are_correct` (verify tensor dimensions match feature dim)
- `test_positive_examples_are_all_starred_repos`
- `test_random_negative_is_not_a_starred_repo`
- `test_time_split_keeps_chronological_order`
- `test_model_forward_pass_produces_scalar_score`
- `test_checkpoint_is_reloadable`
- `test_precision_at_k_known_values`
- `test_ndcg_at_k_known_values`

**Learning objectives:**
- Understand implicit feedback and why starred ≠ "truly positive."
- Understand pairwise ranking (train toward f(pos) > f(neg)).
- Understand the forward pass, loss, backpropagation, and optimizer update.
- Understand overfitting and how validation loss detects it.
- Understand ranking metrics (Precision@K, MRR, NDCG@K) and what they measure.

**Risks:**
- Too few stars → too few training pairs → meaningless model.
  Mitigation: require minimum star count; fall back to baseline if training data is insufficient.
- Hard negatives may accidentally include genuinely good repos (false negatives).
  Mitigation: document this limitation explicitly; use random negatives by default.
- Model may overfit to the small dataset.
  Mitigation: use dropout; monitor validation loss; save best checkpoint by validation performance.

---

### Version 0.6.0 — Full Recommendation Pipeline and Feedback

**Goal:**

```
Candidate repositories
→ ranked by PyTorch model (or baseline if no model available)
→ MMR diversity re-ranking
→ plain-English explanations from actual features
→ results persisted and served from the API
→ user feedback stored and available for future profile updates
```

**Deliverables:**
- Active model loader: load the latest checkpoint from the shared volume; fall back to baseline
- Batch candidate scorer (score all candidates in a single forward pass)
- MMR diversity re-ranking (λ = 0.80 default, configurable)
- `recommendation_runs` table
- `recommendations` table (stores rank, score, score_display, reasons, model_version)
- Explanation improvements: expose which features drove the score
- `GET /v1/recommendations` — list recommendations for the current user
- `GET /v1/recommendations/{repository_id}` — detail for one recommendation
- `POST /v1/recommendations/{repository_id}/feedback` — store thumbs-up / thumbs-down
- Feedback stored in `api.feedback` table
- `score_display` is always a relative score (0–100), never presented as a probability
- Response always identifies `model_version` or `"baseline"` as the scoring method

**Files created or modified:**
- `services/recommender-service/app/ranking/mmr.py`
- `services/recommender-service/app/ranking/inference.py`
- `services/recommender-service/app/explanations/` (improved explanation generator)
- `services/recommender-service/app/consumers/recommend_consumer.py` (full implementation)
- `services/api-service/app/api/recommendations.py` (feedback endpoint added)
- `services/api-service/app/database/` (feedback ORM model)

**Dependencies:** v0.5.0 complete (trained model artifact exists on shared volume).

**Acceptance criteria:**
- `POST /v1/recommendations/generate` triggers end-to-end: score → MMR → persist → notify API.
- Results are diverse: no two consecutive results share all topics.
- Each result's `reasons` list contains at least two factual statements (not generic text).
- `POST /v1/recommendations/{id}/feedback` stores feedback and returns 200.
- If no trained model exists, the baseline is used silently; `model_version: "baseline"` is returned.
- Raw scores are never displayed to the user without being converted to `score_display`.

**Tests:**
- `test_mmr_reduces_topic_overlap_between_results`
- `test_model_fallback_to_baseline_when_no_artifact`
- `test_explanations_reference_actual_feature_components`
- `test_feedback_endpoint_stores_record`
- `test_score_display_is_in_range_0_to_100`
- `test_model_version_is_present_in_response`

**Learning objectives:**
- Understand the difference between candidate generation and re-ranking.
- Understand MMR: relevance vs. novelty trade-off.
- Understand model inference (forward pass only, no gradients needed).
- Understand feedback loops and how explicit feedback could improve future recommendations.
- Understand why ranking scores should not be presented as probabilities.

**Risks:**
- MMR with a large candidate pool may be slow (O(n²) similarity comparisons).
  Mitigation: limit candidate pool to top-200 before MMR; document this limit.
- Loaded model may be incompatible with current feature dimensions if vocab changed.
  Mitigation: save feature config alongside model checkpoint; validate on load.

---

### Version 1.0.0 — Reliability, Testing, and Open-Source Release

**Goal:**

```
Reliable processing under failure conditions
+ reproducible environment from scratch
+ honest evaluation results
+ documentation a contributor can follow without help
```

**Deliverables:**
- Retry policy: `attempt` field in envelope; NACK after `MAX_RETRIES` (default: 3)
- Dead-letter routing: failed messages appear in `repopulse.dead-letter` queue with original headers
- Full ACK/NACK review: every consumer ACKs only after successful DB write
- Idempotency review: duplicate `message_id` is detected and skipped
- Failure state: job transitions to `failed` when a dead-letter event is published
- Integration test suite (requires running containers via `docker compose`)
- End-to-end demo script (`scripts/seed_demo_data.py`)
- Backend metrics logged: latency, queue wait, processing time, error counts
- Evaluation report: run `scripts/run_evaluation.py` and commit the output
- Complete README: troubleshooting section, contribution guide, env var table
- `docs/architecture.md` — service diagram with data flows
- `docs/messaging.md` — exchange/queue/routing key reference
- `docs/model.md` — feature engineering and training explained
- `docs/development.md` — local setup, Makefile targets, running tests
- `LICENSE` file (MIT)
- Release notes in `CHANGELOG.md`

**Dependencies:** v0.6.0 complete (full pipeline works).

**Acceptance criteria (MVP Definition of Done):**
All 19 items from CLAUDE.md §25 must pass:
1. All containers start successfully.
2. Swagger is available at http://localhost:8000/docs.
3. A user can be created.
4. A GitHub sync job can be queued.
5. The ingestion service consumes the job.
6. Repository data is persisted.
7. Candidate repositories are discovered.
8. A NumPy baseline generates recommendations.
9. A PyTorch model trains locally.
10. Model metrics are persisted.
11. Recommendations can be generated asynchronously.
12. Recommendations contain explanations.
13. Feedback can be submitted.
14. Failed jobs retry correctly.
15. Repeatedly failing jobs reach the dead-letter queue.
16. Duplicate messages do not duplicate stored results.
17. Core unit and integration tests pass.
18. The README explains setup, architecture, ML, and limitations.
19. A new contributor can start the project through Docker Compose.

**Tests:**
- Full integration test run via `make test-integration`
- `test_dead_letter_after_three_failures`
- `test_duplicate_message_is_idempotent_in_integration`
- `test_full_pipeline_from_sync_to_recommendation`
- `test_job_fails_when_worker_cannot_recover`

**Learning objectives:**
- Understand at-least-once delivery and what it implies for consumers.
- Understand the difference between message loss and message duplication.
- Understand why idempotency is the correct response to at-least-once delivery.
- Understand integration vs. unit tests and what each catches.
- Understand honest ML evaluation (never report results you did not measure).

**Risks:**
- Integration tests are slow and flaky if containers are not stable.
  Mitigation: use `pytest-docker` or wait-for-it logic; do not run integration tests in tight loops.
- Evaluation results may show the model is no better than the baseline.
  Mitigation: report the results honestly; explain why (sparse data, implicit feedback limitations).

---

## Implementation Order — Rationale

**Why containers before messaging?**
You cannot test RabbitMQ consumers without a running broker. Get the environment working
before adding any business logic.

**Why messaging before GitHub?**
Messaging is the backbone of the entire system. Proving the command/event/job-status loop
with fake data means the GitHub integration only needs to worry about GitHub, not about
whether RabbitMQ is wired correctly.

**Why GitHub before ML?**
The ML pipeline needs real repository data. Building features from an empty database is
impossible; building them from fake data gives false confidence.

**Why NumPy baseline before PyTorch?**
The baseline forces you to define the feature representation concretely. If the baseline
cannot produce useful results, the PyTorch model will not either — and you will know earlier.
The baseline also provides a fallback if training data is insufficient.

**Why PyTorch before the full pipeline?**
You need a trained model artifact before you can test loading it, falling back from it,
or comparing it against the baseline.

**Why reliability last?**
Reliability features (retries, dead-letter, idempotency) are easier to add to a working
system than to a half-built one. Adding them first would hide bugs behind retry logic.

---

## Three-Day Target

| Day | Versions | Risk |
|---|---|---|
| 1 | 0.0.0, 0.1.0, 0.2.0, begin 0.3.0 | Docker and RabbitMQ wiring |
| 2 | Finish 0.3.0, 0.4.0, 0.5.0 | GitHub rate limits, embedding model size |
| 3 | 0.6.0, 1.0.0 | Integration test stability |

Do not sacrifice correctness or understanding to hit the day target.
If 0.3.0 takes all of day 2, proceed to 0.4.0 on day 3 and cut 1.0.0 scope accordingly.
