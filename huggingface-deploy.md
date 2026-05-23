# Deploying to Hugging Face Spaces

HF Spaces natively supports Marimo via Docker.
The app runs in "app mode" (code cells hidden, only interactive outputs shown).

Two approaches below: **A** (fork template -- simplest) and **B** (manual -- more control).

---

## Prerequisites

- Hugging Face account with a **Write** access token ([https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens))
- Git installed locally

Authenticate once:

```bash
pip install huggingface_hub
hf auth login
```

---

## Approach A -- Fork the Official Template (Recommended)

This is the path recommended by both marimo docs and HF docs.

### 1. Duplicate the template

Go to [https://huggingface.co/spaces/marimo-team/marimo-app-template](https://huggingface.co/spaces/marimo-team/marimo-app-template) and click **Duplicate this Space**.

- Set your Space name (e.g. `cootefoo-board`)
- Set visibility (Public or Private)

### 2. Clone your new Space

```bash
git clone https://huggingface.co/spaces/<YOUR_HF_USERNAME>/<YOUR_SPACE_NAME>
cd cootefoo-board
```

### 3. Replace app files

Copy from this project repo into the cloned Space:

```bash
cp /path/to/dataviz1-veto-branch/index.py   ./app.py
cp /path/to/dataviz1-veto-branch/_build_d1.py .
cp /path/to/dataviz1-veto-branch/_build_d2.py .
cp /path/to/dataviz1-veto-branch/_build_d3.py .
cp /path/to/dataviz1-veto-branch/_build_d4.py .
```

Note: `index.py` is renamed to `app.py` to match the template's Dockerfile CMD.

### 4. Update requirements.txt

Replace contents with:

```
marimo>=0.23.3
numpy==2.4.4
pandas==3.0.2
requests==2.33.1
scikit-learn==1.8.0
svg.py==1.10.0
```

### 5. Update the Dockerfile

The template Dockerfile uses Python 3.12. Since our app requires Python >= 3.13,
replace the template Dockerfile with:

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.4.20 /uv /bin/uv

RUN useradd -m -u 1000 user
ENV PATH="/home/user/.local/bin:$PATH"
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

COPY --link --chown=user ./requirements.txt requirements.txt
RUN uv pip install -r requirements.txt

COPY --link --chown=user . /app
RUN mkdir -p /app/__marimo__ && \
    chown -R user:user /app && \
    chmod -R 755 /app
USER user

CMD ["marimo", "run", "app.py", "--host", "0.0.0.0", "--port", "7860"]
```

### 6. Update README.md frontmatter

```yaml
---
title: COOTEFOO Board Investigation
sdk: docker
app_port: 7860
pinned: false
---
```

### 7. (Optional) Copy data for faster, offline-proof loading

The app already falls back to GitHub raw URLs if local files are missing.
But for reliability, copy the data folder:

```bash
cp -r /path/to/dataviz1-veto-branch/data ./data
```

Do **not** copy: `.venv/`, `__pycache__/`, `__marimo__/`, `Claude-Design/`, `docs/`, `plan/`, `notebook/`, `report/`.

### 8. Push

```bash
git add .
git commit -m "Initial deployment"
git push
```

HF auto-builds from the Dockerfile. Watch the **Build** tab in your Space. First build: ~2-3 min.

### 9. Verify

Open `https://huggingface.co/spaces/<YOUR_HF_USERNAME>/cootefoo-board`.
All four tabs should load.

---

## Approach B -- Create from Scratch

Use this if you prefer full control or don't want to fork.

### 1. Create a new Space

Go to [https://huggingface.co/new-space](https://huggingface.co/new-space)

- **SDK:** Docker
- **Name:** e.g. `cootefoo-board`
- Click **Create Space**

### 2. Clone, add files, push

Same as Steps 2-8 above. The only difference is you start from an empty repo
instead of the template, so you must create all three files yourself
(`Dockerfile`, `requirements.txt`, `README.md`).

---

## Data loading strategy

The app loads data in this order:

1. Local files via `mo.notebook_location() / "data" / ...`
2. Fallback: `https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/data/...`

If you include the `data/` folder in the Space, step 1 works and loading is instant.
If you skip it, step 2 fetches from GitHub on each cold start (adds a few seconds).

---

## Troubleshooting


| Problem                      | Fix                                                                                                                      |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Build fails                  | Check Space build logs. Usually a missing package in `requirements.txt`.                                                 |
| App loads, data empty        | GitHub fallback URLs point to `tvakul/dataviz1` main branch. Verify the repo is public. Or include `data/` in the Space. |
| Port error                   | `app_port: 7860` in README.md must match `--port 7860` in Dockerfile CMD.                                                |
| Python version error         | App requires >= 3.13. Ensure Dockerfile uses `python:3.13-slim`.                                                         |
| Import error for `_build_d`* | Ensure all four `_build_d*.py` files are in the Space root alongside `app.py`.                                           |


---

## Updating after changes

```bash
git add .
git commit -m "Update dashboard"
git push
```

HF rebuilds automatically on every push.