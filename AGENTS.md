# turniere-match Agent Notes

Python / Flask event-day operator UI and synchronisation bridge.
Runs on port **7070**. No build step; Python 3 with pip dependencies in
`requirements.txt`.

## Default Workflow

Use `tasks.py` and prefer `inv ...` for local setup, config writing, and startup.

```sh
inv setup
inv write-config --username=... --password=... --tournament-code=... --main-instance-url=http://127.0.0.1:3000
inv start --username=... --password=... --tournament-code=... --main-instance-url=http://127.0.0.1:3000
```

Assume Python 3 is already installed locally.

What the invoke tasks do:

- `inv setup` creates `.venv` and installs `requirements.txt` plus `invoke`
- `inv write-config ...` writes `config.yaml`
- `inv check-backend --main-instance-url=...` waits for backend `/healthz`
- `inv start ...` can auto-run setup on first use, waits for backend health, writes config, and starts Flask on `:7070`

The lower-level manual flow still works:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt invoke
cp config.example.yaml config.yaml
.venv/bin/python main.py
```

In Docker (production) the container is started with `docker-compose up` via
`turniere-infra`. The config file is volume-mounted as `/app/config.yaml`.

## Configuration

All runtime config lives in `config.yaml` (see `config.example.yaml`):

```yaml
username: 'operator-email@example.com'
password: 'operator-password'
tournament_code: '8'           # numeric tournament ID from the backend
main_instance_url: 'http://backend:3000'    # local onsite backend (Docker service name)
remote_instance_url: 'https://backend.turnie.re'  # internet-facing backend
```

For local single-backend development, leave `remote_instance_url` empty.
In that mode, the app still writes to the main backend but skips the background
remote replay worker. This avoids double-writing the same action back into the
same local backend.

To intentionally prevent the service from starting (e.g. no live event is
running), add `DO_NOT_RUN_MATCH: true` to `config.yaml`. The process will
detect it and exit cleanly.

## Architecture

```
main.py      Flask app – handles operator HTTP routes, calls main_instance first
turniere.py  Turniere client – wraps all backend HTTP calls (login, stages, etc.)
worker.py    Background thread – consumes a Queue and replays actions to remote_instance
config.py    Reads config.yaml into a Config dataclass
```

### Write path (for every operator action)

1. User submits form in the UI.
2. Flask route handler calls `main_instance.login()` then the appropriate
   `main_instance.*()` method – **local write happens synchronously here**.
3. The same action is wrapped in an `Action` namedtuple and placed on
   `w.queue` (a `queue.Queue`).
4. The Worker thread (daemon) dequeues the action, calls `remote_instance.login()`
   then the same method on the remote backend, and retries forever until it
   succeeds.
5. Flask redirects the browser back to `/` or `/teams`.

This means **local write is blocking, remote write is eventual**. If the remote
backend is unreachable, the operator can keep scoring and the worker will
catch up later.

## Actions Mirrored to Remote

Worker handles these `Action.type` strings:

| type | what it does |
|---|---|
| `next_group_matches` | starts first unplayed match in each group |
| `next_stage_matches` | starts all matches in a playoff stage |
| `submit_results` | sets both match scores, optionally finishes match |
| `stop_group_stage` | patches stage state to `finished` |
| `update_team_name` | renames a team |
| `set_timer_end` | sets tournament countdown timer end timestamp |

## API Calls Made to the Backend

All calls go through `Turniere._request()` which attaches auth headers obtained
from `login()`. The API contract mirrors `turniere-backend` routes:

- `POST /users/sign_in` → auth tokens
- `GET /tournaments/:code` → stages, teams, timer
- `GET /stages/:id` → stage detail (for next_stage_matches)
- `PATCH /matches/:id` → change match state (`in_progress` / `finished`)
- `PATCH /match_scores/:id` → set score points
- `PATCH /stages/:id` → finish a stage
- `PATCH /teams/:id` → rename team
- `GET /tournaments/:code/timer_end` → current timer
- `PATCH /tournaments/:code/set_timer_end` → set timer

## Timer Calculation

`set_timer_seconds` (the "countdown" form) converts seconds → absolute ISO
timestamp in the **Flask process** before queueing, so both backends receive
the same timestamp string rather than independently computing it.

## What Matters During a Rewrite

- The dual-write pattern (local-first, remote-eventual) is the most important
  operational invariant. Any replacement must preserve it or explicitly
  replace it with something equivalent.
- The Worker's indefinite-retry loop is intentional – internet connectivity
  during a tournament can be spotty.
- `Turniere` in `turniere.py` is the complete client-side API contract for the
  operator write path. It is the reference for which backend endpoints are
  actually used at event time.
- `login()` is called before **every** action individually (not session-cached),
  because tokens can expire and the latency of an extra sign-in call is
  acceptable for infrequent operator actions.
