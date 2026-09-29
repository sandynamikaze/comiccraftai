# ComicCraft AI

A FastAPI web application that turns a story prompt into a five-panel comic using Gemini text and image generation.

## Features

- Story prompt form
- Character name, setting, tone and art style
- Five-panel story generation
- AI image generation for each panel
- Comic-page layout
- PDF export
- Retry handling for temporary Gemini 503/429 errors
- Render deployment configuration

## Local setup

### 1. Create and activate a virtual environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

Copy `.env.example` to `.env` and put your Gemini API key in it:

```env
GEMINI_API_KEY=your_real_key
```

Never commit `.env` to GitHub.

### 4. Run

```bash
uvicorn app.main:app --reload
```

Open:

http://127.0.0.1:8000

## Render

Create a Web Service from this repository.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Add `GEMINI_API_KEY` under Render Environment Variables.

The included `render.yaml` can also be used with Render Blueprint deployment.

## Important model note

Gemini model availability can change by account and API key. The text and image models are configurable through environment variables.

If a selected model is unavailable for your API key, use a model shown by the Gemini API model list and set the environment variable accordingly.

## Troubleshooting 503

A Gemini 503 means the upstream model is temporarily unavailable or overloaded. This project retries temporary failures and can fall back from the primary text model to the configured text fallback model.

If the API continues returning 503, wait and try again rather than repeatedly sending many requests.
