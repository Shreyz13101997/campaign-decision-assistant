# Campaign Decision Assistant

AI-powered assistant that analyzes marketing campaign data and generates evidence-backed recommendations.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

Copy the environment template and fill in your values:

```bash
cp .env.example .env
```

## Run

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## Docker

```bash
docker build -t campaign-assistant .
docker run -p 8000:8000 campaign-assistant
```

## Tests

```bash
pytest
```

## Project Structure

```
app/
├── api/          REST endpoints
├── core/         Config, logging
├── database/     SQLAlchemy models, session
├── loaders/      Data loaders for JSON/CSV sources
├── services/     Business orchestration
├── prompts/      LLM prompt templates
├── rules/        Deterministic claim-rule validation
├── approval/     Human approval workflow
├── storage/      Persistence helpers
├── schemas/      Pydantic request/response models
└── utils/        Generic utilities
```

## TODO

- [ ] Implement data loaders (JSON, CSV)
- [ ] Implement rule engine
- [ ] Implement LLM prompt management
- [ ] Implement analysis service
- [ ] Implement approval workflow
- [ ] Implement storage layer
- [ ] Add comprehensive tests
