# Zentivra Database Schema

## Conventions

### Naming

- Table names are `snake_case` and plural (e.g. `run_triggers`, `digest_snapshots`).
- Column names are `snake_case`.
- Every table-specific UUID column is named `<singular_table>_id` (e.g. `source_id` in the `sources` table).

### Common Columns (applied to every table)


| Column       | Type          | Constraints                         |
| ------------ | ------------- | ----------------------------------- |
| `id`         | INTEGER       | PK, auto-increment                  |
| `<table>_id` | VARCHAR(36)   | UUID v4, UNIQUE, NOT NULL           |
| ...          | ...           | *(table-specific columns below)*    |
| `is_enabled` | BOOLEAN       | NOT NULL, DEFAULT TRUE              |
| `created_at` | DATETIME (tz) | NOT NULL, DEFAULT utcnow            |
| `created_by` | VARCHAR(36)   | NULLABLE (stores `user_id` UUID)    |
| `updated_at` | DATETIME (tz) | NOT NULL, DEFAULT utcnow, on-update |
| `updated_by` | VARCHAR(36)   | NULLABLE (stores `user_id` UUID)    |


---

## USERS

Stores registered user accounts. Session/auth state is tracked in `user_sessions`.


| Column          | Type         | Constraints      |
| --------------- | ------------ | ---------------- |
| `username`      | VARCHAR(100) | UNIQUE, NOT NULL |
| `password_hash` | VARCHAR(255) | NOT NULL         |
| `display_name`  | VARCHAR(150) | NOT NULL         |


---

## USERSESSIONS

Tracks individual login sessions per user. Supports concurrent multi-device logins. Active sessions are also cached in Valkey (`session:{auth_token}` → JSON) with TTL-based auto-expiry.


| Column       | Type          | Constraints                                        |
| ------------ | ------------- | -------------------------------------------------- |
| `user_id`    | INTEGER       | NOT NULL, FK → `users.id`, INDEXED                 |
| `auth_token` | VARCHAR(36)   | UNIQUE, NOT NULL — the session bearer token        |
| `login_at`   | DATETIME (tz) | NOT NULL                                           |
| `logout_at`  | DATETIME (tz) | NULLABLE — NULL while session is active            |
| `expires_at` | DATETIME (tz) | NOT NULL — TTL-based, defaults to 2 hours          |
| `ip_address` | VARCHAR(45)   | NULLABLE — client IP for device tracking           |
| `user_agent` | VARCHAR(500)  | NULLABLE — browser/device info                     |
| `is_active`  | BOOLEAN       | NOT NULL, DEFAULT TRUE — FALSE after logout/expiry |


---

## SOURCES

Configurable data sources assigned to an agent type. Each row is a URL/feed an agent crawls.


| Column         | Type         | Constraints                                                      |
| -------------- | ------------ | ---------------------------------------------------------------- |
| `user_id`      | INTEGER      | NOT NULL, FK → `users.id`, INDEXED                               |
| `source_name`  | VARCHAR(100) | NOT NULL — slug identifier (e.g. `open_ai`)                      |
| `display_name` | VARCHAR(255) | NOT NULL — human-readable (e.g. "Open AI")                       |
| `agent_type`   | VARCHAR(20)  | NOT NULL — competitor / model_provider / research / hf_benchmark |
| `url`          | TEXT         | NOT NULL                                                         |


---

## RUNS

A run **configuration** — defines what the pipeline should do when triggered.


| Column               | Type         | Constraints                                    |
| -------------------- | ------------ | ---------------------------------------------- |
| `user_id`            | INTEGER      | NOT NULL, FK → `users.id`, INDEXED             |
| `run_name`           | VARCHAR(255) | NOT NULL                                       |
| `description`        | TEXT         | NULLABLE                                       |
| `enable_pdf_gen`     | BOOLEAN      | NOT NULL, DEFAULT TRUE                         |
| `enable_email_alert` | BOOLEAN      | NOT NULL, DEFAULT FALSE                        |
| `sources`            | JSON         | NOT NULL — list of source UUIDs (`source_id`s) |
| `crawl_frequency`    | VARCHAR(50)  | NULLABLE — cron expression or human label      |
| `crawl_depth`        | INTEGER      | NOT NULL, DEFAULT 1                            |
| `keywords`           | JSON         | NULLABLE — list of keyword strings             |


---

## RUNTRIGGERS

Each row is a single execution of a run configuration. Tracks execution status and timing.


| Column           | Type        | Constraints                                                 |
| ---------------- | ----------- | ----------------------------------------------------------- |
| `run_id`         | INTEGER     | NOT NULL, FK → `runs.id`                                    |
| `trigger_method` | VARCHAR(50) | NOT NULL — "manual" / "scheduler" / "api"                   |
| `status`         | VARCHAR(20) | NOT NULL — pending / running / completed / failed / partial |
| `is_latest`      | BOOLEAN     | NOT NULL, DEFAULT TRUE                                      |


---

## FINDINGS

Intelligence findings produced by agents during a run trigger execution.


| Column           | Type        | Constraints                                                                           |
| ---------------- | ----------- | ------------------------------------------------------------------------------------- |
| `user_id`        | INTEGER     | NOT NULL, FK → `users.id`, INDEXED                                                   |
| `content`        | TEXT        | NULLABLE — full extracted content (markdown)                                          |
| `summary`        | TEXT        | NULLABLE — AI-generated summary                                                       |
| `run_trigger_id` | INTEGER     | NOT NULL, FK → `run_triggers.id`                                                      |
| `src_url`        | TEXT        | NOT NULL — original source URL                                                        |
| `category`       | VARCHAR(50) | NULLABLE — models / apis / pricing / benchmarks / safety / tooling / research / other |
| `confidence`     | FLOAT       | NOT NULL, DEFAULT 0.5 — range 0.0–1.0                                                 |


---

## SNAPSHOTS

Per-source execution summary within a run trigger. Tracks how many findings a source produced.


| Column           | Type        | Constraints                                     |
| ---------------- | ----------- | ----------------------------------------------- |
| `run_trigger_id` | INTEGER     | NOT NULL, FK → `run_triggers.id`                |
| `source_id`      | INTEGER     | NOT NULL, FK → `sources.id`                     |
| `total_findings` | INTEGER     | NOT NULL, DEFAULT 0                             |
| `summary`        | TEXT        | NULLABLE — short AI summary of results          |
| `status`         | VARCHAR(30) | NOT NULL — created / processed / used_in_digest |


---

## DIGESTS

Compiled intelligence reports generated from a run trigger's findings.


| Column           | Type         | Constraints                         |
| ---------------- | ------------ | ----------------------------------- |
| `user_id`        | INTEGER      | NOT NULL, FK → `users.id`, INDEXED  |
| `run_trigger_id` | INTEGER      | NOT NULL, FK → `run_triggers.id`    |
| `pdf_path`       | VARCHAR(500) | NULLABLE                            |
| `html_path`      | VARCHAR(500) | NULLABLE                            |
| `status`         | VARCHAR(30)  | NOT NULL — draft / published / sent |


---

## DIGESTSNAPSHOTS

Join table linking digests to the snapshots that contributed to them.


| Column        | Type    | Constraints                   |
| ------------- | ------- | ----------------------------- |
| `digest_id`   | INTEGER | NOT NULL, FK → `digests.id`   |
| `snapshot_id` | INTEGER | NOT NULL, FK → `snapshots.id` |


---

## ORCHESTRATOR_CONFIG

Single-row table storing the orchestrator's runtime configuration as a JSON document.

| Column       | Type          | Constraints                         |
| ------------ | ------------- | ----------------------------------- |
| `id`         | VARCHAR(36)   | PK, default `"default"`             |
| `config`     | JSON          | NOT NULL, default `{}`              |
| `updated_at` | DATETIME (tz) | DEFAULT utcnow, on-update           |


