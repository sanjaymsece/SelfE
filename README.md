# SelfE — AI Social Media Manager Backend

Django/DRF backend for an AI-assisted social media manager. It provides five
workspace-scoped capabilities:

1. **AI analytics** — deterministic metrics calculated from stored daily post
   insights, with a Gemini explanation of the supplied numbers.
2. **Personalized content studio** — ideas, captions/hashtags, and short-form
   video scripts generated from saved user preferences and simulated analytics.
3. **Posting-time recommendations** — ranked weekday/hour slots calculated from
   simulated historical post performance.
4. **Reel script generation** — schema-validated production plans with hook,
   scenes, dialogue, camera angles, lighting, backgrounds, music, caption, and CTA.
5. **Comment intelligence** — batch comment classification and contextual reply
   suggestions, scoped to the active workspace.

> **Simulation notice:** all social accounts, posts, insights, and comments are
> simulated. This project has no Meta/Instagram connection and does not publish
> content. It does not use real Instagram credentials or data.

## Stack

- Python 3.14.6
- Django 6.1.2
- Django REST Framework 3.18.3
- djangorestframework-simplejwt 5.5.1
- drf-spectacular 0.30.0
- PostgreSQL (tested with PostgreSQL 18)
- `google-genai` 2.32.0, Pydantic 2.14.1
- `httpx` 0.28.1

## Quick start

```powershell
cd C:\Users\Sanjay M\Desktop\SelfE
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Create the PostgreSQL database (adjust credentials in `.env` if needed):

```powershell
psql -U postgres -c "CREATE DATABASE selfe_db;"
```

Then run migrations and seed the simulated demo tenants:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo_data
.\.venv\Scripts\python.exe manage.py runserver
```

- **Web Application**: `http://127.0.0.1:8000/` (Integrated React + TypeScript SPA)
- **API root**: `http://127.0.0.1:8000/api/v1/`
- **Swagger UI**: `http://127.0.0.1:8000/api/v1/docs/`
- **ReDoc**: `http://127.0.0.1:8000/api/v1/redoc/`
- **OpenAPI schema**: `http://127.0.0.1:8000/api/v1/schema/`

### Frontend Development Server (Optional for live HMR)

```powershell
cd frontend
npm install
npm run dev
# Vite runs at http://localhost:3000
```

## Demo data

`seed_demo_data` is idempotent and creates two complete simulated tenants:

| User | Workspace | Timezone |
| --- | --- | --- |
| `maya@example.com` | Green Fork Kitchen (plant-based cooking) | America/New_York |
| `arjun@example.com` | Momentum Fitness (strength coaching) | Asia/Kolkata |

The demo password comes from `DEMO_PASSWORD` (default `DemoPass123!`). Each
tenant has two simulated social accounts, 16 posts, daily insights, and 14
comments. Re-running the command does not duplicate records. Re-running it with a
different `--reference-date` replaces each post's insight window instead of
leaving stale rows behind.

```powershell
# Optional deterministic reference date
.\.venv\Scripts\python.exe manage.py seed_demo_data --reference-date 2026-06-30
```

## Configuration

`.env` is loaded automatically. `.env.example` documents all supported settings.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | required when `DEBUG=False` | Django signing key |
| `DJANGO_DEBUG` | `False` | Development mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Comma-separated CSRF origins |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | `selfe_db` / `postgres` / empty / `127.0.0.1` / `5432` | PostgreSQL connection |
| `DB_CONN_MAX_AGE` | `60` | Persistent DB connection seconds |
| `JWT_SIGNING_KEY` | `DJANGO_SECRET_KEY` | Optional separate JWT signing key |
| `GEMINI_API_KEY` | empty | Google AI Studio key. Empty means AI endpoints fail closed with `503`. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Single configured free-tier model. There is no automatic paid/model fallback. |
| `GEMINI_TIMEOUT_SECONDS` | `30` | Provider HTTP timeout |
| `GEMINI_MAX_ATTEMPTS` | `2` | Retries for transient provider failures (1–3) |
| `GEMINI_MAX_OUTPUT_TOKENS` | `2048` | Provider output cap |
| `GEMINI_TEMPERATURE` | `0.5` | Default generation temperature |
| `AI_THROTTLE_RATE` | `30/hour` | Per-user AI endpoint throttle |
| `DEMO_PASSWORD` | `DemoPass123!` | Demo seed password; development only |

Never commit `.env`. The committed example contains no real credentials.

## Authentication and workspace isolation

JWT endpoints:

- `POST /api/v1/auth/register/` creates a user, first workspace, owner membership,
  and saved preferences in one transaction.
- `POST /api/v1/auth/login/` returns access/refresh tokens.
- `POST /api/v1/auth/refresh/` returns a new access token.
- `GET /api/v1/auth/me/` returns the authenticated user, preferences, and memberships.
- `GET|PATCH /api/v1/auth/preferences/` reads or updates niche, goals, language,
  tone, content style, target audience, and keywords.

Send the access token as `Authorization: Bearer <access>`.

Workspace-scoped endpoints resolve the active workspace from the
`X-Workspace-ID` header:

- Required when the user belongs to more than one workspace.
- Optional when the user belongs to exactly one workspace.
- The server always verifies membership; the header is never trusted on its own.
- A foreign workspace header returns `403 workspace_forbidden`.
- Guessed IDs for another tenant's drafts, Reels, reports, or comments return
  `404 not_found` without revealing whether the object exists.

Example:

```http
GET /api/v1/analytics/overview/?date_from=2026-09-01&date_to=2026-10-22
Authorization: Bearer <access>
X-Workspace-ID: 1
```

## Endpoints

### System and authentication

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/v1/health/` | Public health/database check; no secrets |
| GET | `/api/v1/schema/` | OpenAPI 3 schema |
| GET | `/api/v1/docs/` | Swagger UI |
| GET | `/api/v1/redoc/` | ReDoc |
| POST | `/api/v1/auth/register/` | Public |
| POST | `/api/v1/auth/login/` | Public |
| POST | `/api/v1/auth/refresh/` | Public |
| GET | `/api/v1/auth/me/` | Authenticated |
| GET/PATCH | `/api/v1/auth/preferences/` | Authenticated, user-scoped |
| GET/POST | `/api/v1/workspaces/` | List accessible workspaces or create new workspace |
| GET/PATCH/DELETE | `/api/v1/workspaces/{id}/` | Workspace detail, update settings, or delete |

### Simulated social data and analytics

| Method | Path | Notes |
| --- | --- | --- |
| GET/POST | `/api/v1/social-accounts/` | Workspace-scoped; list or connect simulated social accounts |
| GET/DELETE | `/api/v1/social-accounts/{id}/` | Retrieve or disconnect a social account |
| GET | `/api/v1/analytics/overview/` | Calculated totals, prior period, growth, daily series, top posts |
| GET | `/api/v1/analytics/posts/` | Paginated per-post metrics; `date_from`, `date_to`, `platform`, `media_type` |
| GET | `/api/v1/analytics/posting-times/` | Ranked slots; `min_posts`, `limit`, `platform` |
| GET | `/api/v1/analytics/reports/` | Saved AI reports |
| POST | `/api/v1/analytics/reports/generate/` | Explain calculated metrics with Gemini |
| GET | `/api/v1/analytics/reports/{id}/` | Saved report detail |

Default analytics range is the last 90 days. Ranges may not exceed 366 days.
All totals are computed from `PostInsight` rows with database aggregation.

Metric formulas:

- `engagement = likes + comments + shares + saves`
- `engagement_rate = engagement / reach * 100`
- `reach_rate = reach / views * 100`
- `save_rate = saves / reach * 100`
- Growth is null when the preceding equal-length period has no data; it is never
  invented.
- Posting slots group each post once by its local publication weekday/hour in the
  workspace timezone and average per-post engagement rates.

### Content studio

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/v1/content/ideas/generate/` | Saves a schema-validated idea draft |
| POST | `/api/v1/content/captions/generate/` | Saves a caption draft |
| POST | `/api/v1/content/scripts/generate/` | Saves a general short-form video script draft |
| GET/POST | `/api/v1/content/drafts/` | List/create manual drafts; filters `kind`, `status`, `search` |
| GET/PATCH/DELETE | `/api/v1/content/drafts/{id}/` | Workspace-scoped CRUD |

Generation requests accept `topic`, `goal`, `platform`, `tone`, `language`,
`count`, and `extra_instructions`, depending on the endpoint. Empty tone/language
fall back to saved preferences. A failed AI call saves nothing.

### Reel generator

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/v1/reels/generate/` | Validated, saved Reel production plan |
| GET/POST | `/api/v1/reels/` | Paginated list or create a manual plan validated against the reel schema; filters `status`, `platform`, `search` |
| GET/PATCH/DELETE | `/api/v1/reels/{id}/` | Workspace-scoped CRUD; plan itself is immutable |

### Comment intelligence

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/v1/comments/` | Workspace-scoped; filters `sentiment`, `intent`, `post`, `is_question`, `analyzed`, `search` |
| GET/PATCH/DELETE | `/api/v1/comments/{id}/` | Retrieve, update sentiment/intent/flags, or delete comment |
| POST | `/api/v1/comments/analyze/` | Classify up to 50 selected or unanalyzed comments |
| POST | `/api/v1/comments/{id}/suggest-reply/` | Saves contextual reply suggestion history |

## Frontend Integration & CORS

The backend includes `django-cors-headers` and is configured out of the box to accept cross-origin requests from web frontends (including Google AI Studio web previews, local React/Vite/Next.js apps, or any browser origin).

### Quick Frontend Connection Checklist:
1. **Base URL**: Point the frontend API client to `http://127.0.0.1:8000/api/v1` (or your tunneled HTTPS address if running from Google AI Studio cloud).
2. **Auth Header**: Once logged in via `/api/v1/auth/login/`, attach the Bearer token to all requests:
   ```
   Authorization: Bearer <access_token>
   ```
3. **Workspace Header**: Send the active workspace ID:
   ```
   X-Workspace-ID: <workspace_id>
   ```
   (Optional if the account only has 1 workspace; required if switching between multiple workspaces).
4. **Demo Credentials**:
   - `maya@example.com` / `DemoPass123!` (Workspace: Green Fork Kitchen)
   - `arjun@example.com` / `DemoPass123!` (Workspace: Momentum Fitness)

Analysis requires the AI to return every requested comment ID exactly once. A
partial, duplicate, or invalid classification is rejected as
`502 ai_invalid_response`, and no comment is updated. Reply generation accepts
optional `tone`, `language`, and `extra_instructions`.

## AI provider behavior

AI calls go through `ai/service.py` and the official `google-genai` SDK. Output is
validated with Pydantic before it is returned or saved. Prompts and generated text
are never written to `AIUsageLog`; only feature, provider, model, success/failure,
error kind, latency, and token counts are stored.

Failures are explicit and structured; no results are fabricated or substituted
from another model/provider:

| Condition | HTTP status | Error code |
| --- | --- | --- |
| Empty API key or unusable credentials/model | 503 | `ai_not_configured` |
| Provider quota or rate limit (`429`) | 429 | `ai_quota_exceeded` |
| Timeout | 504 | `ai_timeout` |
| Invalid/incomplete structured output | 502 | `ai_invalid_response` |
| Other provider/transport failure | 502 | `ai_provider_error` |

All error responses use the same envelope:

```json
{
  "error": {
    "code": "ai_not_configured",
    "message": "AI generation is not configured on this server."
  }
}
```

Validation errors add an `error.details` object.

The configured model is controlled only by `GEMINI_MODEL`. If Gemini is
unavailable, endpoints fail; there is no automatic fallback to a paid model.

## Tests

Tests do not call Gemini or Instagram. AI success paths use the deterministic
`ai.mock.MockAIClient`; failure paths use mocked provider exceptions.

```powershell
.\.venv\Scripts\python.exe manage.py test --verbosity 2
```

Coverage includes authentication/JWT, registration, preferences, workspace
resolution, cross-tenant isolation, analytics formulas and date validation,
posting-time ranking/timezones, content generation and CRUD, Reel generation and
CRUD, comment filtering/analysis/replies, AI error mapping, seed idempotency, and
anonymous access.

Latest verified result: **93 tests passed**, 0 failures, 0 errors.

Static checks and schema validation:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py spectacular --file schema.yml --validate
```

## Project layout

```text
config/                         Django settings, URLs, JSON 404/500 fallbacks
apps/accounts/                  Custom user, JWT auth, preferences
apps/workspaces/                Workspace/membership models and active-workspace mixin
apps/social_accounts/           Simulated accounts and posts
apps/analytics/                 Metrics selectors, AI report generation, posting times
apps/content_studio/            AI content generation and draft CRUD
apps/reel_generator/            Reel plan generation and CRUD
apps/comment_intelligence/      Comment classification and reply suggestions
apps/common/                    Health, error envelope, pagination, AI usage logs
ai/                             Gemini client, schemas, orchestration, prompts, mock provider
simulation/                     Deterministic two-tenant demo fixture and seed command
tests/                          Test suite and tenant factories
```

## Known limitations and unfinished work

- **Live Gemini success is unverified** in this environment because
  `GEMINI_API_KEY` is empty. Failure behavior and all structured success paths are
  tested with the mock provider. Add a real free-tier key to `.env` to exercise
  the live provider; quota and model availability then depend on the Google
  account.
- No real Instagram/Meta connectivity, OAuth, webhooks, publishing, or scheduling.
  All social data is simulated.
- No frontend, background worker, Celery/Redis, Docker, or production deployment
  configuration beyond Django security settings.
- No competitor analysis or live trend ingestion, by scope.
- AI output is schema-validated but not content-moderated beyond prompt rules and
  structural checks.
- Reply suggestions are stored as history; there is no endpoint to list reply
  history separately (the model is available for a future read endpoint).
- JWT refresh tokens use the default SimpleJWT rotation/blacklist configuration
  from settings; token revocation is not enabled.
