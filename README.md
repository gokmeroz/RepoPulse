# RepoPulse

> **Status: Under active development — v0.0.0 (planning phase)**
> The architecture and API contract are defined. Application code does not exist yet.
> All sections marked **[PLANNED]** describe intended behaviour, not working features.

Personalized GitHub repository recommendations for developers who want to grow their skills.

---

## What RepoPulse Does

Most developers star repositories and forget them. When they want to learn something new — say, distributed systems, PyTorch, or RabbitMQ — they have to search manually, sift through popularity lists, and guess what is actually relevant to them.

RepoPulse solves this differently. It reads what you already care about — your GitHub stars — and uses that signal to rank repositories you have *not* starred yet. Instead of showing you what is globally popular, it shows you what is personally relevant.

---

## Who It Is For

- Developers who want to grow in a specific direction (e.g. ML, backend, DevOps)
- Developers who learn by reading high-quality open-source code
- Anyone curious about personalized recommendation systems built without a frontend

---

## Core User Journey

```
1. You provide your GitHub username (and an optional token + learning goals)
2. RepoPulse fetches your starred repositories
3. It collects metadata, topics, languages, and README content for each one
4. It builds a numerical profile of your interests
5. It discovers candidate repositories you have not starred
6. It ranks candidates using a NumPy baseline and a small PyTorch model
7. It re-ranks results for topic diversity (no ten near-identical repos)
8. It returns recommendations with relevance scores and plain-English reasons
```

Everything happens asynchronously. You submit a request, get a job ID back immediately, and poll for results.

---

## Example Output [PLANNED]

```json
{
  "model_version": "ranker-v1.0.0",
  "recommendations": [
    {
      "repository_id": 123,
      "full_name": "example/production-pytorch",
      "rank": 1,
      "score": 0.874,
      "score_display": 87.4,
      "reasons": [
        "Strong semantic similarity to your starred ML repositories",
        "Matches your Python and backend interests",
        "Recently maintained",
        "Introduces MLOps concepts not heavily represented in your profile"
      ]
    }
  ]
}
```

`score_display` is a relative ranking score (0–100), not a calibrated probability.

---

## Why Open Source?

RepoPulse exists to be a learning project and a portfolio artefact. The architecture deliberately uses full-size tools — RabbitMQ, PostgreSQL, Docker, PyTorch — at a scale a single developer can understand and explain. If you want to learn event-driven microservices, recommendation systems, or ML evaluation, reading and running this project is the point.

---

## Architecture [PLANNED]

```
Developer / Swagger / curl
            |
            v
       API Service          (FastAPI, port 8000)
            |
            v
         RabbitMQ           (AMQP, management UI port 15672)
         /      \
        v        v
Ingestion      Recommender
Service        Service
        \      /
        PostgreSQL          (port 5432)
```

Three application services, four infrastructure containers, one Docker Compose file.

### API Service

The only service exposed to the outside world.

Responsibilities:
- Accept HTTP requests and validate them
- Create job records in PostgreSQL
- Publish commands to RabbitMQ
- Consume completion/failure events from workers
- Update job statuses
- Return recommendations and accept feedback

What it does **not** do: call GitHub, train models, score repositories.

### Ingestion Service

A background worker. No HTTP port.

Responsibilities:
- Consume GitHub sync commands from RabbitMQ
- Fetch starred repositories, metadata, topics, languages, and READMEs from the GitHub REST API
- Handle pagination and rate limits
- Discover candidate repositories
- Normalize and persist data
- Publish sync-completed or sync-failed events

### Recommender Service

A background worker. No HTTP port.

Responsibilities:
- Consume model-training and recommendation-generation commands
- Build repository feature vectors (text, topic, language, metadata)
- Build a user preference profile from starred repositories and learning goals
- Score candidates using the NumPy baseline
- Train and evaluate the PyTorch ranking model
- Apply MMR diversity re-ranking
- Generate plain-English explanations
- Persist recommendations
- Publish completion or failure events

---

## Technology Stack [PLANNED]

| Layer | Technology | Why |
|---|---|---|
| HTTP API | FastAPI | Fast, async, auto-generates Swagger |
| Message broker | RabbitMQ (Pika client) | Industry-standard AMQP, teaches queues and exchanges directly |
| Database | PostgreSQL | Relational, durable, schemas per service |
| ORM | SQLAlchemy 2.x | Type-safe, async-capable |
| Validation | Pydantic | Consistent contracts at every boundary |
| ML numerics | NumPy | Interpretable baseline, no training overhead |
| ML model | PyTorch | Industry standard, CPU-compatible, small enough to run locally |
| Containers | Docker + Docker Compose | One-command reproducible environment |
| Tests | Pytest | Standard Python testing |
| Language | Python | Readable, rich ML and async ecosystem |

---

## ML Pipeline [PLANNED]

### Feature Engineering

Every repository is converted into a feature vector with four components:

1. **Text features** — sentence embeddings of the description and README
2. **Topic features** — multi-hot vector over GitHub topics
3. **Language features** — normalized distribution (e.g. Python: 0.80, Dockerfile: 0.10)
4. **Metadata features** — log-normalized stars, forks, issues; activity decay; archived flag

### User Profile

Your preference vector is the weighted average of feature vectors for your starred repositories:

```
u = Σ(αᵢ · xᵢ) / Σαᵢ
```

Weights are higher for recent stars and repositories matching your learning goals.

### NumPy Baseline (interpretable, always available)

Scores each candidate as a weighted sum of similarity components:

```
score =  0.35 × text_similarity
       + 0.20 × topic_similarity
       + 0.15 × language_similarity
       + 0.10 × activity_score
       + 0.10 × quality_score
       + 0.10 × novelty_score
```

Every component is normalized to [0, 1]. No training required. Runs immediately after data ingestion.

### PyTorch Ranker (learned, measured)

A small feed-forward network trained on pairwise comparisons:
- **Positive**: a repository you starred
- **Negative**: a candidate you did not star (random or hard negative)

Training objective: `f(user, starred_repo) > f(user, unstarred_repo)` using margin ranking loss.

Input to the network:

```
z = [u, x_repo, u ⊙ x_repo, |u - x_repo|]
```

Architecture: `Linear → ReLU → Dropout → Linear → ReLU → Linear → score`

The model is only reported as better than the baseline after honest evaluation with held-out data.

### Diversity Re-ranking (Maximal Marginal Relevance)

After relevance ranking, MMR re-ranks the top candidates to avoid redundancy:

```
MMR(candidate) = λ · relevance - (1 - λ) · max_similarity_to_already_selected
```

Default λ = 0.80 (80% relevance, 20% diversity penalty).

---

## API Contract [PLANNED]

All routes are versioned under `/v1`.

```
POST   /v1/users                                  Create a user
POST   /v1/sync                                   Queue a GitHub sync job
POST   /v1/models/train                           Queue a model training job
POST   /v1/recommendations/generate               Queue a recommendation job

GET    /v1/jobs/{job_id}                          Poll job status
GET    /v1/recommendations                        List recommendations
GET    /v1/recommendations/{repository_id}        Get one recommendation

POST   /v1/recommendations/{repository_id}/feedback   Submit feedback

GET    /health                                    Liveness probe
GET    /ready                                     Readiness probe
```

Job statuses: `queued → processing → completed | failed`

### Example Sync Request [PLANNED]

```bash
curl -X POST http://localhost:8000/v1/sync \
  -H "Content-Type: application/json" \
  -d '{
    "github_username": "your-username",
    "learning_goals": ["pytorch", "backend", "rabbitmq"]
  }'
```

```json
{ "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "status": "queued" }
```

---

## RabbitMQ Message Flow [PLANNED]

```
POST /v1/sync
  → API publishes to: repopulse.commands  (routing key: github.sync.requested)
  → Ingestion Service consumes from: ingestion.github-sync queue
  → Ingestion Service publishes to: repopulse.events (routing key: github.sync.completed)
  → API Service consumes from: api.job-events queue
  → API updates job status to: completed
```

Every message carries a correlation ID so the full lifecycle of a job can be traced in structured logs.

---

## Setup [PLANNED]

Prerequisites: Docker and Docker Compose.

```bash
git clone <repository-url>
cd repopulse
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| API + Swagger | http://localhost:8000/docs |
| RabbitMQ Management UI | http://localhost:15672 |

Default RabbitMQ credentials: `guest` / `guest` (development only).

---

## Database Schema [PLANNED]

One PostgreSQL instance, three schemas, clear ownership per service.

```
api schema
  users, jobs, feedback

ingestion schema
  repositories, repository_languages, repository_topics,
  user_stars, candidate_repositories, sync_runs

recommender schema
  repository_features, model_runs, model_metrics,
  recommendation_runs, recommendations
```

Services write only to their own schema. Cross-schema reads are allowed in the MVP and documented where they occur. A production deployment would use database-per-service.

---

## Testing [PLANNED]

```bash
# Unit tests (no infrastructure required)
pytest services/api-service/tests/unit
pytest services/ingestion-service/tests/unit
pytest services/recommender-service/tests/unit

# Integration tests (requires running containers)
pytest services/api-service/tests/integration
```

Unit tests cover: message schemas, feature normalization, cosine similarity, Jaccard similarity, activity decay, baseline scoring, negative sampling, MMR, evaluation metrics.

Integration tests cover: API → RabbitMQ → worker → event → job-status update.

---

## Version Roadmap

| Version | Status | Goal |
|---|---|---|
| 0.0.0 | **In progress** | README and project plan |
| 0.1.0 | Planned | Project foundation — all containers start |
| 0.2.0 | Planned | Messaging and job orchestration |
| 0.3.0 | Planned | GitHub ingestion |
| 0.4.0 | Planned | Feature engineering and NumPy baseline |
| 0.5.0 | Planned | PyTorch ranking model |
| 0.6.0 | Planned | Full recommendation pipeline and feedback |
| 1.0.0 | Planned | Reliability, evaluation, and open-source release |

---

## Known Limitations (MVP)

- **Implicit feedback only.** Starring is a weak signal. A starred repository is not proof of skill or preference — it might be a bookmark. The model learns from this noise.
- **No real-time updates.** Recommendations are generated on demand, not continuously refreshed.
- **Cold-start problem.** A user with few stars gets low-quality recommendations. Minimum ~20 stars recommended.
- **Candidate discovery is simple.** v1 uses topic and language searches, not graph-based discovery or collaborative filtering.
- **Single-user training.** The PyTorch model is trained per-user, not across all users. Collaborative signals are not used in v1.
- **CPU-only training.** The model is small enough to train on a laptop CPU in under a minute, but not suitable for large-scale deployment without GPU inference.
- **No authentication.** The API has no auth layer in v1. Add a reverse proxy or API gateway before any public exposure.
- **One PostgreSQL container.** Schemas simulate service isolation but the database is physically shared. A production version would use database-per-service.

---

## Evaluation [PLANNED]

Once implemented, model quality will be measured using a time-aware split (older stars → training, newer stars → evaluation):

- Precision@K
- Recall@K
- Mean Reciprocal Rank (MRR)
- NDCG@K
- Diversity@K

Results will compare four approaches: popularity baseline, NumPy weighted baseline, PyTorch ranker, PyTorch ranker with MMR. No results will be reported until experiments are actually run.

---

## Contributing [PLANNED]

Contribution guide will be added in v1.0.0. Until then:

1. Read `CLAUDE.md` to understand the architecture constraints and decision rules.
2. Read `docs/project-plan.md` for the implementation roadmap.
3. Every feature must improve recommendation quality, reliability, maintainability, explainability, learning value, or ease of running the project. If it doesn't, it doesn't belong in the MVP.

---

## License

MIT — see `LICENSE` (to be added in v1.0.0).
