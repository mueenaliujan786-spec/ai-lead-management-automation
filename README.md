# AI-Powered Lead Management & Follow-Up Automation System

An automation platform that receives customer leads, validates and stores them, analyzes them with AI, and helps a human reviewer approve follow-up emails.

**Status:** In development (Phase 1 complete: planning and design)

## What it does

1. Receives a lead through a webhook
2. Validates the data and detects duplicates
3. Stores the lead in PostgreSQL
4. Uses AI to categorize the lead, set a priority, and draft an email
5. A human approves, edits, or rejects the draft in a dashboard
6. Approved emails are sent, and every workflow run is logged

## Tech stack

- n8n (workflow automation)
- Python + FastAPI (backend)
- PostgreSQL (database)
- React + Tailwind CSS (dashboard)
- Docker (local development)

## Documentation

- [MVP scope](docs/mvp.md)
- [Architecture](docs/architecture.md)
- [Database design](docs/database.md)

## Roadmap

- [x] Phase 1: Requirements and planning
- [ ] Phase 2: Environment setup
- [ ] Phase 3: Backend development
- [ ] Phase 4: n8n workflows
- [ ] Phase 5: Email and approval system
- [ ] Phase 6: Frontend dashboard
- [ ] Phase 7: Testing and security
- [ ] Phase 8: Deployment
- [ ] Phase 9: Portfolio preparation