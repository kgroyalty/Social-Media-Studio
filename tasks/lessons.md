# Promura Social — Lessons Learned

Per workflow rule 3 (Self-Improvement Loop): every correction or non-obvious decision goes here. Future-Claude reviews this at session start to avoid repeating mistakes.

Format:
```
## YYYY-MM-DD — Short title
**Trigger:** what happened
**Lesson:** what to do next time
**Why:** the underlying principle
```

---

## 2026-05-17 — docker-compose.prod.yml is a supplement, not a standalone file

**Trigger:** Initial deploy spec said `docker compose -f docker-compose.prod.yml up --build -d`. That command fails because the prod compose file has services without `build:` or `image:` directives — they inherit from docker-compose.yml.

**Lesson:** Always run `docker compose -f docker-compose.yml -f docker-compose.prod.yml ...` for the production VPS. The default file-resolution behavior auto-loads docker-compose.override.yml (the dev overlay), which is wrong for prod. Explicit `-f` flags REPLACE the default resolution.

**Why:** Docker compose's file resolution is layered: base + override.yml for dev (auto), or explicit -f for prod. Mixing them produces incorrect environments.

---

## 2026-05-17 — Django production.py forced HTTPS without an env toggle

**Trigger:** Django production.py had `SECURE_SSL_REDIRECT = True`, `SECURE_HSTS_SECONDS = 31536000`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True` hardcoded. Deploying to plain HTTP (no TLS proxy yet) created an infinite redirect loop.

**Lesson:** Always gate HTTPS-only Django settings behind an env toggle. Default to False for IP-based deploys; flip to True only when a TLS-terminating reverse proxy is in front.

**Why:** Production code should be deployable in multiple postures (bare IP, behind nginx, behind Cloudflare, behind Caddy). Hardcoding HTTPS-required settings prevents staging or IP-based deploys.

---

## 2026-05-17 — CSRF_TRUSTED_ORIGINS must be explicitly read from env in Django 4.x+

**Trigger:** Setting `CSRF_TRUSTED_ORIGINS` in .env did nothing because the settings file never called `env.list("CSRF_TRUSTED_ORIGINS", default=[])`. Every POST request would have returned 403.

**Lesson:** When the project uses django-environ, an env var only takes effect if the settings file explicitly reads it. Spec docs saying "set X in .env" must be paired with a code change that consumes X. Verify both ends of the contract.

**Why:** Django settings are Python — they don't auto-import from env. The bridge between env and settings is the explicit `env(...)` call.

---

## 2026-05-18 — Dev compose worker race-conditions migrations on fresh DB

**Trigger:** First `docker compose up` after fresh build crashed `promura-social-worker-1` with `relation "background_task" does not exist`. Root cause: in dev mode, `worker` and `app` both depend only on `postgres: service_healthy` and start in parallel; if worker queries `Task` model before app has applied migrations, it crashes.

**Lesson:** In `docker-compose.override.yml`, override worker's `command` to migrate-then-process: `sh -c "python manage.py migrate --noinput && python manage.py process_tasks"`. `migrate` is idempotent so this stays safe. Prod compose already has a dedicated `migrate` one-shot service; dev keeps it inline.

**Why:** `depends_on: condition: service_healthy` only waits for postgres readiness, NOT for schema migrations. Any container that uses the ORM at startup is exposed to this race on a fresh DB.

---

## 2026-05-18 — Orphan docker network blocks compose up

**Trigger:** After an interrupted/half-failed `docker compose up`, retrying produced `Network promura-social_default Error: network with name promura-social_default already exists` and containers app + worker never reached Created state.

**Lesson:** When compose up fails partway through, run `docker compose down --remove-orphans` followed by `docker network prune -f` before retrying. Failing to clean orphan networks silently breaks subsequent `up`s with confusing error messages.

**Why:** Docker compose creates a default network per project. If the up process is killed mid-execution, the network can persist but the containers don't, leaving compose unable to reuse OR recreate the network cleanly.

---

## 2026-05-17 — Audit before deploy, every time

**Trigger:** Pre-deploy audit caught 4 blockers that would have produced a broken production environment: forced HTTPS, missing CSRF reader, non-standalone prod compose, port 8000 collision with Coolify.

**Lesson:** Always run a senior-developer-style audit pass on a forked codebase before deploying. Check: env-var consumption, security toggle assumptions, compose file topology, port conflicts on the target host, license/branding completeness.

**Why:** Fork-and-deploy projects accumulate assumptions from upstream that don't match your environment. Catching them in audit costs minutes; catching them in production costs hours and reputation.
