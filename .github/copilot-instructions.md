<!-- Short, focused instructions to help AI coding agents be productive in this repo -->

# Copilot instructions — Timeline Backend

Keep this short and opinionated. The repository is a small FastAPI + Celery scheduler that persists workflow state to Firebase and uses RabbitMQ (broker) + Redis (result backend).

Key files to read first

- `src/main.py` — FastAPI routes. Entrypoint for HTTP API (use `uvicorn src.main:app`).
- `src/tasks.py` — Celery app and `schedule_task` implementation. Handles execution + rescheduling.
- `src/schema.py` — Pydantic model `WorkflowSchema` used by routes and tasks.
- `src/services/firebase_client.py` — Firebase Admin init and helpers (ensure initialized before using `auth`).
- `src/services/auth.py` — FastAPI dependency that verifies Firebase ID tokens.
- `src/utils.py` — scheduling helper `calculate_next_run`.

Architecture & dataflow (short)

- Client POSTs workflow JSON -> `POST /schedule-workflow` in `src/main.py`.
- `main` converts Pydantic model to JSON-serializable dict using `model_dump(mode="json")` and enqueues a Celery task via `schedule_task.delay(payload)`.
- Celery worker (`src/tasks.py`) validates payload into `WorkflowSchema`, runs the job logic (currently a string result), writes updated state and reschedules itself via `apply_async(..., eta=next_run_time)`.
- Firestore (via `src/services/firebase_client.py`) is used for persistence of workflow state and run history (ensure service account credentials are provided via env).
- Redis holds Celery task results. RabbitMQ is the broker.

Important runtime config & commands

- Run FastAPI (project root):
  - `uvicorn src.main:app --reload`
  - Or: `export PYTHONPATH="$PWD" && uvicorn src.main:app --reload`
- Start Celery worker (project root):
  - `celery -A src.tasks.celery_app worker --loglevel=info`
  - Broker URL in `src/tasks.py`: `amqp://timeline:timeline@localhost:5672/timelinehost` (RabbitMQ vhost/user must match)
  - Result backend: `redis://localhost:6379/0`
- Health & debug endpoints:
  - `GET /health/redis` — checks Redis ping used by Celery backend
  - `GET /tasks/{task_id}` — returns Celery AsyncResult(status/result)

Data & serialization conventions

- Use Pydantic v2 APIs: `model_dump(mode="json")` to create JSON-safe payloads that are passed to Celery. Prefer storing Python datetimes when saving to Firestore so Firestore stores native timestamps.
- `WorkflowSchema` fields: `name, query, start_time_utc (datetime), interval_seconds (int), active (bool), next_run_at_utc, last_result, last_run_at_utc`.

Project-specific patterns and gotchas

- schedule_task reschedules itself with `apply_async((payload,), eta=next_run_time)`. To stop a workflow you must:
  - Mark `active=False` in Firestore (or update the workflow doc the worker reads before scheduling the next run), OR
  - Revoke the scheduled task id from the broker if you stored `next_task_id`.
- Celery IPC: tasks return a Python value (string on success in current code). Results are stored in Redis under `celery-task-meta-<task_id>` and read via `AsyncResult`.
- Firebase initialization must happen before using `firebase_admin.auth.verify_id_token`. Prefer idempotent init in `src/services/firebase_client.py` and import from there in `src/services/auth.py`.

Secrets & env

- Firebase credentials: set either `GOOGLE_APPLICATION_CREDENTIALS=/abs/or/project/path/firebase-service-account.json` or `FIREBASE_SERVICE_ACCOUNT_JSON` (path or full JSON string). Code expects env to point to a valid service account file.
- RabbitMQ and Redis are currently hardcoded to localhost in `src/tasks.py`; use env refactors before deploying.

Testing & debugging tips

- If you see `ModuleNotFoundError: No module named 'src'` run from project root and import by module path: `uvicorn src.main:app` or set `PYTHONPATH` to project root.
- To remove Celery results from Redis without installing `redis-cli` (or for scripted cleanup) use a Python snippet that calls `scan_iter('celery-task-meta-*')` and deletes keys.

When editing code for agents

- Keep changes minimal and follow current patterns: pydantic v2 (`model_validate`/`model_dump`), Celery `apply_async` rescheduling, Firestore persistence.
- Avoid changing how tasks are scheduled in a single PR without preserving a migration path (clients rely on `task_id` semantics).

Files of interest for edits

- `src/main.py` — routes + examples
- `src/tasks.py` — scheduling behavior and side-effects (first place to check when tasks misbehave)
- `src/services/firebase_client.py` — ensure idempotent init and robust path resolution
- `src/services/auth.py` — authentication dependency used by protected routes

If something is unclear

- Ask to show the exact file you plan to edit and the goal (e.g., "persist next_task_id to Firestore"), then make a small patch and run the worker locally.

---

Please review — tell me any missing local commands or conventions and I'll iterate.
