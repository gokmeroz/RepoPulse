# CLAUDE.md — RepoPulse

## 1. Your Role

You are the senior backend and ML engineer responsible for helping me build **RepoPulse** from an empty repository.

You must act as both:

1. **Implementation partner** — write production-quality code.
2. **Technical mentor** — explain what is being built, why it is needed, how it works, and what trade-offs were made.

Do not blindly generate the entire project at once. Build it incrementally, keep every phase runnable, and make sure I understand each major concept before moving forward.

---

## 2. Project Summary

**RepoPulse** is an open-source, backend-only GitHub repository recommendation platform for developers who want to improve their skills.

A developer provides:

- A GitHub username
- An optional GitHub access token
- Optional learning goals such as `PyTorch`, `backend`, `RabbitMQ`, or `MLOps`

RepoPulse then:

1. Retrieves the developer's starred repositories.
2. Collects repository metadata, topics, languages, descriptions, and README content.
3. Builds a numerical representation of the developer's interests.
4. Discovers candidate repositories the developer has not starred.
5. Ranks candidates using:
   - An interpretable NumPy baseline
   - A small PyTorch ranking model
6. Re-ranks results for diversity.
7. Returns recommendations with relevance scores and human-readable explanations.

There is **no frontend**.

Users interact through:

- FastAPI Swagger
- REST endpoints
- `curl`
- Postman
- An optional CLI added only after the core system works

---

## 3. Primary Goal

Build a resume- and LinkedIn-worthy project that demonstrates:

- Backend architecture
- Event-driven microservices
- RabbitMQ
- Docker
- PostgreSQL
- External API integration
- NumPy-based feature engineering
- PyTorch model development
- Recommendation-system evaluation
- Testing
- Reliability
- Open-source documentation

The implementation must remain realistic for **one developer to complete as an MVP in approximately three focused days**.

---

## 4. Core Constraints

Follow these constraints strictly:

- Backend language: **Python**
- API framework: **FastAPI**
- ML: **PyTorch and NumPy**
- Message broker: **RabbitMQ**
- Database: **PostgreSQL**
- ORM: **SQLAlchemy 2.x**
- Validation and contracts: **Pydantic**
- Containerization: **Docker and Docker Compose**
- Testing: **Pytest**
- RabbitMQ client: use a direct AMQP client such as **Pika**
- Architecture: **event-driven microservices**
- Repository style: **monorepo**
- No frontend
- No Kubernetes
- No Kafka
- No Redis unless a proven requirement appears
- No vector database in v1
- No LLM API dependency
- No unnecessary API gateway
- No distributed model training
- No premature cloud deployment
- Do not create fake microservices with no meaningful ownership boundary
- Do not overengineer the MVP

Prefer a working, understandable implementation over unnecessary abstraction.

---

## 5. Required Architecture

Build exactly three application services for v1.

```text
Developer / Swagger / curl
            |
            v
       API Service
            |
            v
         RabbitMQ
         /      \
        v        v
Ingestion      Recommender
Service        Service
        \      /
        PostgreSQL
```

Infrastructure:

- RabbitMQ
- PostgreSQL
- Shared model-artifact volume
- Docker Compose

### 5.1 API Service

Responsibilities:

- Expose the public HTTP API
- Validate incoming requests
- Create job records
- Publish RabbitMQ commands
- Consume completion/failure events
- Update job statuses
- Return recommendations and model results
- Accept explicit recommendation feedback

The API service must not:

- Call GitHub directly
- Train models
- Generate embeddings
- Process large repository batches
- Contain recommender business logic

### 5.2 Ingestion Service

Responsibilities:

- Consume GitHub synchronization commands
- Call the GitHub REST API
- Handle authentication
- Handle pagination
- Handle rate limits
- Fetch starred repositories
- Fetch repository metadata
- Fetch topics
- Fetch language distributions
- Fetch README content
- Discover candidate repositories
- Normalize GitHub responses
- Persist ingestion-owned data
- Publish completion or failure events

The ingestion service must not:

- Train ML models
- Produce final recommendation scores
- Own API job orchestration

### 5.3 Recommender Service

Responsibilities:

- Consume model-training commands
- Consume recommendation-generation commands
- Load repository and feedback data
- Clean and preprocess text
- Build repository feature vectors
- Build user preference profiles
- Implement a NumPy baseline
- Build positive and sampled-negative examples
- Train a small PyTorch ranking model
- Evaluate the model
- Save model artifacts
- Score candidate repositories
- Apply diversity re-ranking
- Generate explanations
- Persist recommendation results
- Publish completion or failure events

Training and inference remain in the same service for v1.

---

## 6. Repository Structure

Use this structure unless a clearly better structure is justified first:

```text
repopulse/
├── services/
│   ├── api-service/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── database/
│   │   │   ├── messaging/
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   ├── settings.py
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── ingestion-service/
│   │   ├── app/
│   │   │   ├── consumers/
│   │   │   ├── database/
│   │   │   ├── github/
│   │   │   ├── messaging/
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   ├── settings.py
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   └── recommender-service/
│       ├── app/
│       │   ├── artifacts/
│       │   ├── consumers/
│       │   ├── database/
│       │   ├── datasets/
│       │   ├── evaluation/
│       │   ├── explanations/
│       │   ├── features/
│       │   ├── messaging/
│       │   ├── models/
│       │   ├── ranking/
│       │   ├── services/
│       │   ├── settings.py
│       │   └── main.py
│       ├── tests/
│       ├── Dockerfile
│       └── pyproject.toml
│
├── packages/
│   └── contracts/
│       ├── repopulse_contracts/
│       │   ├── commands.py
│       │   ├── events.py
│       │   ├── envelope.py
│       │   └── identifiers.py
│       └── pyproject.toml
│
├── infrastructure/
│   ├── migrations/
│   ├── postgres/
│   └── rabbitmq/
│       └── definitions.json
│
├── scripts/
│   ├── seed_demo_data.py
│   └── run_evaluation.py
│
├── docs/
│   ├── architecture.md
│   ├── messaging.md
│   ├── model.md
│   └── development.md
│
├── docker-compose.yml
├── Makefile
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── CLAUDE.md
```

The shared contracts package may contain only:

- Command schemas
- Event schemas
- Message envelopes
- Shared identifiers
- Serialization rules

It must not contain:

- ORM models
- GitHub API code
- Feature engineering
- Recommender logic
- Service-specific business logic

---

## 7. Database Ownership

For the MVP, all services may use one PostgreSQL container, but use separate schemas and clear ownership.

```text
api
├── users
├── jobs
└── feedback

ingestion
├── repositories
├── repository_languages
├── repository_topics
├── user_stars
├── candidate_repositories
└── sync_runs

recommender
├── repository_features
├── model_runs
├── model_metrics
├── recommendation_runs
└── recommendations
```

Rules:

- A service owns the tables it writes.
- Avoid directly mutating another service's owned tables.
- Reads across schemas are acceptable for this MVP if documented.
- Do not pretend the database is fully isolated.
- Document that a production version may use database-per-service.

---

## 8. RabbitMQ Design

Use two topic exchanges:

```text
repopulse.commands
repopulse.events
```

Use a dead-letter exchange:

```text
repopulse.dead-letter
```

### Commands

Commands request work:

```text
github.sync.requested
model.training.requested
recommendations.generation.requested
```

### Events

Events report outcomes:

```text
github.sync.completed
github.sync.failed

model.training.completed
model.training.failed

recommendations.generated
recommendations.generation.failed
```

### Queues

```text
ingestion.github-sync
recommender.model-training
recommender.recommendation-generation
api.job-events
repopulse.dead-letter
```

### Message Envelope

Every message must include:

```json
{
  "message_id": "uuid",
  "message_type": "github.sync.requested",
  "correlation_id": "uuid",
  "job_id": "uuid",
  "user_id": "uuid",
  "attempt": 1,
  "occurred_at": "ISO-8601 timestamp",
  "payload": {}
}
```

### Reliability Requirements

Implement and explain:

- Durable exchanges
- Durable queues
- Persistent messages
- Manual acknowledgements
- `ACK` only after successful processing
- `NACK` or rejection on failure
- Prefetch limits
- Retry limit
- Dead-letter routing
- Idempotent consumers
- Correlation IDs
- Structured logging

Do not hide RabbitMQ behind a heavy task framework. The point is to learn AMQP and message processing directly.

---

## 9. API Contract

Use versioned routes.

### Required Endpoints

```http
POST /v1/users
POST /v1/sync
POST /v1/models/train
POST /v1/recommendations/generate

GET /v1/jobs/{job_id}
GET /v1/recommendations
GET /v1/recommendations/{repository_id}

POST /v1/recommendations/{repository_id}/feedback

GET /health
GET /ready
```

### Job Statuses

```text
queued
processing
completed
failed
```

### Example Sync Request

```json
{
  "github_username": "example-user",
  "learning_goals": ["pytorch", "backend", "rabbitmq"]
}
```

### Example Recommendation Response

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

A displayed score is a ranking score, not automatically a calibrated probability.

---

## 10. GitHub Data

Collect only the data needed for v1:

- Repository GitHub ID
- Full name
- URL
- Description
- README text
- Topics
- Primary language
- Language distribution
- Star count
- Fork count
- Open issue count
- Created timestamp
- Updated timestamp
- Last pushed timestamp
- Archived status
- Fork status
- User-star relationship

Requirements:

- Support pagination.
- Respect rate limits.
- Use an optional access token.
- Handle missing README files.
- Handle empty topics.
- Handle deleted or inaccessible repositories.
- Normalize GitHub responses before persistence.
- Avoid unnecessary API calls.
- Cache or skip unchanged repositories where practical.

Candidate discovery may use:

- Topic searches
- Language searches
- Keywords extracted from learning goals
- Related topics from starred repositories

Keep candidate discovery simple and deterministic in v1.

---

## 11. Machine Learning Design

The ML problem is personalized ranking using implicit feedback.

### 11.1 Positive Examples

Repositories the user starred.

### 11.2 Unlabelled Candidates

Repositories the user has not starred.

Do not automatically describe every unstarred repository as truly negative.

### 11.3 Negative Sampling

Implement:

- Random negatives for an initial dataset
- Hard negatives where practical

Hard negatives are related repositories that appear plausible but are less aligned with the user's profile.

Document limitations caused by sparse and implicit feedback.

---

## 12. Repository Features

Create a repository feature vector containing:

```text
text features
topic features
language features
metadata features
```

### Text Features

Use repository description and README content.

For the MVP:

- Use a small pretrained sentence-embedding model if practical.
- Keep the embedding model configurable.
- Do not train a language model from scratch.
- Cache generated embeddings.

### Topic Features

Use:

- Multi-hot vectors
- Topic overlap
- Jaccard similarity

### Language Features

Use normalized language distributions.

Example:

```text
Python: 0.80
Dockerfile: 0.10
Shell: 0.10
```

### Metadata Features

Possible features:

- Log-normalized star count
- Log-normalized fork count
- Activity decay
- Repository age
- Archived flag
- Fork flag
- Open issue count
- Recent update indicator

Normalize numerical features.

---

## 13. User Profile

Build the user's profile from their starred repositories and optional learning goals.

Simple profile:

```math
u = (1 / n) * sum(x_i)
```

Preferred weighted profile:

```math
u = sum(alpha_i * x_i) / sum(alpha_i)
```

Possible weights:

- Recent star: higher weight
- Older star: lower weight
- Explicit learning-goal match: higher weight
- Explicit positive feedback: higher weight
- Explicit negative feedback: lower or negative weight

Keep the first version understandable.

---

## 14. NumPy Baseline

Implement an interpretable baseline before training the PyTorch model.

Example formula:

```math
score =
    0.35 * text_similarity
  + 0.20 * topic_similarity
  + 0.15 * language_similarity
  + 0.10 * activity_score
  + 0.10 * quality_score
  + 0.10 * novelty_score
```

Every component must be normalized to `[0, 1]`.

Explain and test:

- Cosine similarity
- Jaccard similarity
- Log normalization
- Activity decay
- Weighted sums
- Novelty calculation

The baseline must produce usable recommendations even when model training is unavailable.

---

## 15. PyTorch Ranking Model

Implement a small model, not a large neural network.

Suggested input:

```math
z = [u, x_r, u * x_r, abs(u - x_r)]
```

Suggested architecture:

```text
Input
  ↓
Linear
  ↓
ReLU
  ↓
Dropout
  ↓
Linear
  ↓
ReLU
  ↓
Linear
  ↓
Ranking score
```

Use pairwise ranking.

For a positive repository `p` and sampled negative `n`, train toward:

```math
f(u, p) > f(u, n)
```

A suitable loss is margin ranking loss.

Requirements:

- Deterministic random seeds
- Train/validation/test separation
- Clear tensor-shape comments
- `Dataset` and `DataLoader`
- Model checkpoint saving
- Model metadata
- Training metrics
- Evaluation metrics
- CPU-compatible execution
- Small enough to run locally

Do not claim the model is better until it is measured.

---

## 16. Diversity Re-ranking

After relevance ranking, apply Maximal Marginal Relevance.

Conceptually:

```math
MMR(candidate) =
    lambda * relevance
  - (1 - lambda) * similarity_to_selected
```

Default:

```text
lambda = 0.80
```

The final list should remain relevant while avoiding ten near-identical repositories.

---

## 17. Recommendation Explanations

Every recommendation must include human-readable reasons.

Generate explanations from actual feature contributions, not vague AI-generated text.

Possible reasons:

- Strong README semantic similarity
- High topic overlap
- Strong Python language match
- Recently maintained
- Popular but not excessively mainstream
- Matches an explicit learning goal
- Adds a topic missing from the current profile
- Similar to repositories receiving positive feedback

The explanation system should expose why repository A ranked above repository B.

---

## 18. Evaluation

Use a time-aware split when possible:

```text
Older stars → training history
Newer stars → held-out evaluation
```

Required ranking metrics:

- Precision@K
- Recall@K
- Mean Reciprocal Rank
- NDCG@K
- Diversity@K

Compare:

1. Popularity baseline
2. NumPy weighted baseline
3. PyTorch ranker
4. PyTorch ranker with MMR

Never invent metrics.

Only report results produced by executed experiments.

---

## 19. Backend Metrics

Record or expose:

- API request latency
- Queue waiting time
- Worker processing time
- End-to-end job duration
- Completed-job count
- Failed-job count
- Retry count
- Dead-letter count

Structured logs should include:

```text
timestamp
service
level
message_id
correlation_id
job_id
event_type
duration_ms
```

---

## 20. Docker Requirements

The final MVP must run using:

```bash
docker compose up --build
```

Expected containers:

```text
api-service
ingestion-service
recommender-service
rabbitmq
postgres
migrations
```

Requirements:

- Health checks
- Named volumes
- Internal Docker network
- Non-root users where practical
- Environment-based configuration
- No secrets committed to Git
- `.env.example`
- Persistent PostgreSQL volume
- Persistent model-artifact volume
- RabbitMQ management UI available locally

Do not rely on host-installed PostgreSQL or RabbitMQ.

---

## 21. Testing Strategy

### Unit Tests

Test:

- Message schemas
- GitHub response mapping
- Feature normalization
- Cosine similarity
- Jaccard similarity
- Activity decay
- Baseline scoring
- Negative sampling
- MMR
- Evaluation metrics
- Explanation generation

### Integration Tests

Test:

- API → RabbitMQ publishing
- Worker → RabbitMQ consuming
- Database persistence
- Job-state updates
- Retry behavior
- Dead-letter behavior
- Duplicate-message handling

### API Tests

Test:

- Valid requests
- Invalid requests
- Missing jobs
- Job state transitions
- Recommendation retrieval
- Feedback submission
- Health and readiness endpoints

Prefer useful tests over chasing arbitrary coverage percentages.

---

## 22. Coding Standards

Use:

- Type hints
- Small functions
- Explicit boundaries
- Dependency injection where useful
- Clear names
- Docstrings for non-obvious public functions
- Comments explaining mathematical or distributed-system logic
- Structured exception handling
- Configuration objects
- UTC timestamps
- UUIDs for jobs, messages, and correlations
- Database migrations

Avoid:

- Giant service classes
- Hidden global state
- Circular imports
- Copy-pasted RabbitMQ logic
- Broad `except Exception` without logging and a clear recovery strategy
- Silent failures
- Magic numbers
- Unexplained abstractions
- Premature generic frameworks

Use comments to explain **why**, not restate obvious code.

---

## 23. Security and Privacy

For v1:

- Treat GitHub tokens as secrets.
- Read tokens only from environment variables or request-safe configuration.
- Never log tokens.
- Do not store tokens in plaintext unless absolutely necessary.
- Prefer one-time use for sync jobs.
- Validate GitHub usernames.
- Limit README sizes before processing.
- Set HTTP timeouts.
- Validate message payloads.
- Avoid arbitrary code execution.
- Avoid downloading and running candidate repositories.

---

## 24. Open-Source Requirements

RepoPulse must be easy for another developer to run.

The final README must include:

- What RepoPulse does
- Why it exists
- Architecture diagram
- Service responsibilities
- RabbitMQ flow
- ML pipeline
- Mathematical scoring explanation
- Prerequisites
- Setup instructions
- Environment variables
- API examples
- Testing commands
- Troubleshooting
- Limitations
- Evaluation results
- Roadmap
- Contribution guide
- License

The expected setup should be approximately:

```bash
git clone <repository-url>
cd repopulse
cp .env.example .env
docker compose up --build
```

Then:

```text
Swagger: http://localhost:8000/docs
RabbitMQ UI: http://localhost:15672
```

Use an open-source license such as MIT unless I specify otherwise.

---

## 25. MVP Definition of Done

The MVP is complete only when:

1. All containers start successfully.
2. Swagger is available.
3. A user can be created.
4. A GitHub sync job can be queued.
5. The ingestion service consumes the job.
6. Repository data is persisted.
7. Candidate repositories are discovered.
8. A NumPy baseline can generate recommendations.
9. A PyTorch ranking model can train locally.
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

---

## 26. README-First, Versioned Implementation Plan

The project must be built in explicit versions. A version is complete only when:

1. Its scoped implementation is finished.
2. Its tests and validation commands pass.
3. The README accurately reflects the current state.
4. The implementation is explained to me.
5. I complete the version knowledge checkpoint.
6. Any important misunderstandings are corrected.

Never describe planned functionality as already implemented. In the README, clearly distinguish:

- Available now
- Planned for the current version
- Planned for later versions
- Known limitations

### Version 0.0.0 — README and Project Plan

This is the mandatory first version. Do not write application code yet.

First, inspect the existing `README.md`. Then rewrite or improve it so that it explains:

- The problem RepoPulse solves
- Who it is for
- The core user journey
- The expected recommendation output
- Why the project is open source
- The planned microservice architecture
- The role of FastAPI, RabbitMQ, PostgreSQL, Docker, NumPy, and PyTorch
- The planned ML pipeline
- The difference between the NumPy baseline and PyTorch ranker
- The planned API workflow
- The intended one-command Docker setup
- The limitations of the initial MVP
- The version roadmap
- A clear notice that the implementation is not complete yet

After the README is updated, create a detailed project plan containing:

- Version boundaries
- Deliverables for every version
- Dependencies between versions
- Acceptance criteria
- Test strategy
- Risks and mitigations
- Scope exclusions
- Exact order of implementation

Recommended plan location:

```text
docs/project-plan.md
```

At the end of Version 0.0.0:

- Show the README changes.
- Show the complete version roadmap.
- Explain why the implementation order was chosen.
- Explain which risks are handled earliest.
- Give me a knowledge checkpoint focused on the product idea, architecture, service boundaries, asynchronous processing, and ML objective.
- Do not begin Version 0.1.0 until I have attempted the checkpoint and misunderstandings have been corrected.

### Version 0.1.0 — Project Foundation

Goal:

```text
All service containers start
+ infrastructure is healthy
+ each process has a clear responsibility
```

Build:

- Monorepo directory structure
- Shared contracts package skeleton
- Root `.gitignore`
- Root `.env.example`
- Root `Makefile`
- Docker Compose
- PostgreSQL with health check
- RabbitMQ management image with health check
- Minimal API service
- Minimal ingestion worker
- Minimal recommender worker
- Structured logging
- `/health` and `/ready`
- Initial startup tests

Acceptance criteria:

- `docker compose config` succeeds.
- All long-running containers start.
- Health checks become healthy.
- Swagger is reachable.
- Both workers connect to RabbitMQ.
- Basic tests pass.

Knowledge checkpoint topics:

- Containers versus images
- Docker Compose networking
- Health versus readiness
- Why workers are separate processes
- Why the services do not import one another's application logic

### Version 0.2.0 — Messaging and Job Orchestration

Goal:

```text
HTTP request
→ job record
→ RabbitMQ command
→ worker
→ completion event
→ updated job status
```

Build:

- Message envelopes
- Command and event contracts
- Topic exchanges
- Queues and routing keys
- API job persistence
- API publishers
- Worker consumers
- API event consumer
- Correlation IDs
- Manual acknowledgement basics
- One end-to-end fake/demo job before GitHub integration

Acceptance criteria:

- A request returns a job ID immediately.
- RabbitMQ routes the command to the correct worker.
- The worker publishes a completion event.
- The API updates the job to `completed`.
- Duplicate demo messages do not create duplicate results.

Knowledge checkpoint topics:

- Synchronous versus asynchronous execution
- Exchanges, queues, bindings, and routing keys
- Commands versus events
- ACK/NACK
- Correlation and idempotency

### Version 0.3.0 — GitHub Ingestion

Goal:

```text
GitHub username
→ asynchronous synchronization
→ normalized repository data in PostgreSQL
```

Build:

- GitHub REST client
- Optional token configuration
- Starred-repository pagination
- Repository metadata retrieval
- README retrieval
- Language retrieval
- Topic normalization
- Rate-limit handling
- Candidate discovery
- Incremental or duplicate-safe persistence
- Ingestion completion and failure events

Acceptance criteria:

- A real GitHub username can be synchronized.
- Missing README and topic data are handled.
- Pagination works.
- Re-running a sync does not duplicate repositories.
- Rate-limit information is logged safely.
- Ingestion tests pass with mocked GitHub responses.

Knowledge checkpoint topics:

- External API integration
- Pagination
- Rate limiting
- Normalization
- Idempotent database writes
- Service data ownership

### Version 0.4.0 — Feature Engineering and NumPy Baseline

Goal:

```text
Repository data
→ numerical features
→ developer profile
→ explainable baseline recommendations
```

Build:

- Text preprocessing
- Configurable text embeddings
- Topic vectors
- Language distributions
- Metadata normalization
- Developer preference vector
- Cosine similarity
- Jaccard similarity
- Activity decay
- Quality and novelty features
- Weighted NumPy scoring
- Component-level explanations
- Baseline recommendation endpoint flow

Acceptance criteria:

- Every repository can be converted into a deterministic feature representation.
- A developer profile can be generated.
- The NumPy baseline returns ranked candidates.
- Every result contains actual score contributions.
- Unit tests verify the scoring mathematics.
- The baseline works without a trained PyTorch model.

Knowledge checkpoint topics:

- Vectors
- Normalization
- Cosine similarity
- Jaccard similarity
- Weighted scoring
- Embeddings
- Ranking scores versus probabilities

### Version 0.5.0 — PyTorch Ranking Model

Goal:

```text
Implicit GitHub feedback
→ training pairs
→ PyTorch ranker
→ measured ranking quality
```

Build:

- Positive examples
- Unlabelled candidate handling
- Random and hard-negative sampling
- Time-aware data splitting
- PyTorch `Dataset`
- PyTorch `DataLoader`
- Small ranking network
- Pairwise margin-ranking loss
- Training loop
- Validation
- Model checkpoints
- Model-run metadata
- Precision@K
- Recall@K
- MRR
- NDCG@K

Acceptance criteria:

- Training runs on CPU.
- Random seeds are controlled.
- Tensor shapes are documented and tested.
- A model artifact is saved and reloadable.
- Metrics are generated from an actual experiment.
- The model is compared honestly against the baseline.

Knowledge checkpoint topics:

- Implicit feedback
- Positive versus unlabelled data
- Negative sampling
- Forward pass
- Loss
- Backpropagation
- Optimizer
- Overfitting
- Ranking metrics

### Version 0.6.0 — Recommendation Pipeline and Feedback

Goal:

```text
Candidate generation
→ ranking
→ diversity
→ explanations
→ user feedback
```

Build:

- Active-model loading
- Batch candidate scoring
- MMR diversity re-ranking
- Recommendation persistence
- Recommendation retrieval
- Feedback endpoint
- Feedback storage
- Explanation improvements
- Model-version references
- Baseline fallback when no trained model exists

Acceptance criteria:

- Recommendations are generated asynchronously.
- Results are ranked and diversified.
- Explanations correspond to real features.
- Explicit feedback can be stored.
- The response identifies the model or baseline used.
- The API never presents a raw ranking score as a calibrated probability.

Knowledge checkpoint topics:

- Candidate generation versus ranking
- Relevance versus diversity
- MMR
- Model inference
- Feedback loops
- Explainability
- Model fallback strategies

### Version 1.0.0 — Reliability, Testing, and Open-Source Release

Goal:

```text
Reliable processing
+ reproducible setup
+ defensible evaluation
+ contributor-ready documentation
```

Build:

- Retry policy
- Dead-letter routing
- Complete manual ACK/NACK behavior
- Idempotent consumers
- Failure-state handling
- Integration tests
- End-to-end demo
- Backend metrics
- Evaluation report
- Complete README
- Architecture and messaging docs
- Troubleshooting
- Contribution guide
- License
- Release notes

Acceptance criteria:

- Repeated failures reach the dead-letter queue.
- Successful work is acknowledged only after persistence.
- Duplicate messages are safe.
- Tests pass from a clean environment.
- A new developer can run the system with documented commands.
- README examples match the implementation.
- Evaluation claims are backed by generated results.

Knowledge checkpoint topics:

- At-least-once delivery
- Message loss and duplication
- Retry safety
- Dead-letter queues
- Integration versus unit testing
- Reproducibility
- Honest ML evaluation
- Production limitations

### Suggested Three-Day Distribution

The versions define the source of truth; the day plan is only a target.

#### Day 1

- Version 0.0.0
- Version 0.1.0
- Version 0.2.0
- Begin Version 0.3.0

#### Day 2

- Finish Version 0.3.0
- Version 0.4.0
- Version 0.5.0

#### Day 3

- Version 0.6.0
- Version 1.0.0

Do not sacrifice correctness or understanding merely to match the day target.

---

## 27. How You Must Work With Me

Follow this workflow for every version.

### Before Coding

Briefly explain:

1. What the current version will deliver.
2. Why it comes at this point in the roadmap.
3. Which concepts I should understand.
4. Which files will be created or changed.
5. How the version will be tested.
6. What is explicitly outside this version.

### While Coding

- Implement one coherent slice at a time.
- Keep the project runnable.
- Do not generate the entire codebase in one uncontrolled dump.
- Explain important code sections.
- Add comments where architecture, RabbitMQ, database, or ML logic is not obvious.
- State assumptions.
- Mention trade-offs.
- Do not silently change the agreed architecture.
- Update the README whenever commands, behavior, architecture, or available features change.
- Never document a planned feature as already available.

### At the End of Every Version

Always provide:

1. A concise summary of what changed.
2. A list of created and modified files.
3. The commands I should run.
4. The successful output I should expect.
5. The tests and validations performed.
6. Any remaining limitations.
7. The concepts I should now understand.
8. A version-specific knowledge checkpoint.
9. A suggested Git commit message.
10. A suggested semantic version tag where appropriate.

### Mandatory Knowledge Checkpoint

After every version, test my understanding before continuing.

The checkpoint must contain **five to eight questions** and use a mixture of:

- “Explain in your own words”
- Trace-the-request or trace-the-message questions
- “Why did we choose this?” questions
- Small debugging scenarios
- Architecture boundary questions
- Mathematical questions for ML versions
- Trade-off questions

Rules:

- Ask one clearly numbered checkpoint.
- Do not provide the answer key before I attempt it.
- Wait for my answers before starting the next version.
- Grade each answer as `correct`, `partially correct`, or `incorrect`.
- Explain every correction precisely.
- Ask a focused follow-up question for important gaps.
- Give a short refresher when I struggle.
- Re-test the misunderstood concept with a new question.
- Do not treat memorized definitions as sufficient; test whether I can apply the concept.
- Target practical understanding, not trick questions.
- Recommend moving forward only when I demonstrate a solid understanding of the version.
- I may explicitly override this gate, but otherwise do not begin the next version.

### Version Completion Gate

A version is not complete merely because code was written.

It is complete when:

```text
implementation works
+ tests pass
+ documentation is current
+ I have attempted the knowledge checkpoint
+ important misunderstandings have been corrected
```

Do not proceed automatically to the next version.

---

## 28. Error-Handling Rules

When something fails:

1. Inspect the actual error.
2. Explain the root cause.
3. Fix the smallest responsible layer.
4. Add or update a test when appropriate.
5. Do not replace working architecture with a shortcut.
6. Do not suppress the error without justification.
7. Keep Docker, RabbitMQ, database, and ML concerns separated.

---

## 29. Decision Rules

When choosing between two implementations:

Prefer the option that is:

1. Easier to explain
2. Easier to test
3. More reliable
4. More standard
5. More useful for learning
6. Appropriate for a three-day MVP

Before adding a dependency, explain:

- What problem it solves
- Why the standard library or current stack is insufficient
- Its operational cost
- Whether the project can avoid it

---

## 30. Initial Task

Start with **Version 0.0.0: README and Project Plan**.

Do not create application code, Dockerfiles, database models, RabbitMQ consumers, or ML code yet.

Perform these steps in order:

1. Read this entire `CLAUDE.md`.
2. Inspect the current repository and existing `README.md`.
3. Summarize the current state of the repository.
4. Rewrite or improve `README.md` first.
5. Clearly label planned features as planned.
6. Create `docs/project-plan.md`.
7. Break the implementation into the versions defined in this document.
8. For every version, document:
   - Goal
   - Deliverables
   - Files or areas affected
   - Dependencies
   - Acceptance criteria
   - Tests
   - Learning objectives
   - Risks
9. Identify the critical path.
10. Identify the highest-risk assumptions.
11. Explain the implementation order.
12. Present the Version 0.0.0 knowledge checkpoint.

The README should become the project's public product and architecture overview.

The project plan should become the internal implementation roadmap.

At the end of Version 0.0.0:

- Show a concise diff summary for `README.md`.
- Summarize `docs/project-plan.md`.
- State exactly what Version 0.1.0 will implement.
- Provide a suggested commit message such as:

```text
docs: define RepoPulse vision and implementation roadmap
```

- Ask five to eight questions testing my understanding.
- Do not begin Version 0.1.0 until I answer and the important gaps are corrected.

---

## 31. Final Principle

Every feature must answer at least one of these questions:

- Does it improve the recommendation quality?
- Does it improve reliability?
- Does it improve maintainability?
- Does it improve explainability?
- Does it improve the learning value?
- Does it make the open-source project easier to run?

If the answer is no, do not add it to the MVP.
