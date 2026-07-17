# Hosting And Public Beta

## Document metadata

- **Purpose:** Operating assumptions for hosting MealRoulette beyond personal use.
- **Authority:** Strategy document. Deployment runbooks remain under [operations/](../operations/).
- **Status:** Planning assumptions — not a service commitment.
- **Update when:** Before public beta, before changing hosting provider, or when active household scale changes materially.

---

## Cost Snapshot

**Research date:** 2026-07-17  
**Currency:** EUR unless noted  
**Purpose:** order-of-magnitude planning only  
**Refresh when:** before public beta, before choosing a provider, or every 3-6 months during beta.

Provider prices and infrastructure plans change frequently. Treat estimates as rough planning ranges.

## Durable Conclusions

- Roulette CPU is unlikely to be the main infrastructure cost.
- The first real risks are inefficient database queries, PostgreSQL connections, background jobs, images, LLM calls, email abuse, and support time.
- Start public beta with capped usage and predictable fixed infrastructure costs.
- Avoid unlimited free hosted access.
- Do not adopt managed cloud complexity or auto-scaling before retention proves demand.

## Expected Hosting Ranges

| Scale | Active households/month | Infrastructure estimate |
| --- | ---: | ---: |
| Personal/private | 1-20 | EUR 5-15/month |
| Early public beta | 100-1,000 | EUR 10-40/month |
| Small real service | 1,000-10,000 | EUR 40-150/month |
| Growing service | 10,000-50,000 | EUR 150-600/month |
| Large usage | 50,000+ | architecture-dependent |

Active households matter more than registered households.

## Recommended Early Beta Architecture

Start with one self-managed VPS:

```text
Caddy or Nginx
Frontend static assets
FastAPI API
APScheduler worker
PostgreSQL
Nightly database backup to separate object storage
```

Suggested size:

```text
2 shared vCPU
4 GB RAM
60-80 GB SSD
```

Expected total:

```text
EUR 12-30/month, excluding managed AI usage and owner time
```

Use Docker Compose initially. Do not introduce Kubernetes or microservices for the first public beta.

## Why Not A Raspberry Pi For Public Hosting

A Raspberry Pi can host private testing, and roulette CPU is not a blocker.

Do not use it for a public hosted service because of:

- residential internet reliability;
- power outages;
- dynamic IP and routing;
- security exposure;
- backup/recovery responsibility;
- operational coupling to the owner's home network.

## Managed Platform Tradeoff

Managed app platforms reduce operations work but cost more because API, worker, database, backups, and monitoring are provisioned separately.

Planning range:

```text
EUR/USD 35-120/month for a minimal managed setup
```

This may become worthwhile after public beta proves retention and support burden.

## Roulette Load Assumption

A weekly generation might evaluate:

```text
14 meal slots
× 500-10,000 candidates per slot
= tens of thousands of lightweight scoring operations
```

Even:

```text
10,000 households × 1 weekly generation
= about 1,429 generations/day
= about 1 generation/minute on average
```

should be manageable on modest infrastructure if candidate loading and SQL query counts are controlled.

Avoid synchronized spikes by adding scheduling jitter or queueing generation jobs.

## Resource Thresholds

Consider separating PostgreSQL, adding workers, or moving to managed services when:

- sustained CPU exceeds 70%;
- sustained RAM exceeds 80%;
- database size exceeds 20-30 GB;
- p95 API latency exceeds 500 ms;
- roulette p95 exceeds 3 seconds;
- backup duration becomes operationally problematic;
- support incidents show self-managed operations are taking too much time.

## Image Storage

Text recipes are cheap to store. Images can dominate storage.

Example:

```text
1,000,000 images × 500 KB = about 500 GB
```

Early constraints:

- restrict upload size;
- resize uploads;
- store optimized WebP/AVIF;
- avoid multiple large derivatives;
- consider external image URLs or object storage before public image uploads.

## Public Beta Stages

### Stage 1 — Private Alpha

Invite 5-10 households.

Prefer:

- non-engineers;
- different household structures;
- at least one family that does not enjoy configuring software.

Measure:

- whether they can create enough recipes;
- whether they understand dish vs recipe;
- whether they use roulette more than once;
- whether shopping lists are useful;
- whether they return after four weeks;
- whether AI entry reduces onboarding friction.

### Stage 2 — Capped Public Beta

Limit access to 100-500 households.

Use:

- invite codes or waiting list;
- hard AI credit limits;
- rate limits;
- image limits;
- email limits;
- automatic backups;
- monthly infrastructure budget alert;
- beta/no-guarantee wording.

### Stage 3 — Decide From Evidence

After several months, evaluate:

- weekly active households;
- four-week retention;
- recipes created per household;
- plans generated per week;
- shopping lists opened;
- cost per active household;
- support incidents per household;
- percentage using AI entry;
- willingness to pay.

Then decide whether MealRoulette is a personal open-source project, community-hosted service, paid hosted product, free core plus paid AI, or not worth operating publicly.

## Operating Rule

Build for hundreds or a few thousand households first, not millions.

Prefer predictable degradation:

```text
queue jobs -> slow response -> reject excess requests
```

over unpredictable spend.
