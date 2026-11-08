# AI-Powered Lead Management & Follow-Up Automation System

An automation system that captures customer leads from a website form, stores them in a database, analyzes them with AI, writes a personalized follow-up email, and only sends it after a human approves it.

**Status:** Core pipeline working end to end and tested with a real email inbox (form, intake, AI analysis, draft, approval, email). A React dashboard for approvals is planned; for now approvals go through the API.

## What it does

1. A visitor fills in a public **contact form** (built with n8n).
2. The **Lead Intake** workflow sends the lead to the backend, which validates it, detects duplicates and saves it in PostgreSQL.
3. **Google Gemini** analyzes the lead (category, priority) and drafts a reply email. The AI output is validated before it is saved, and failures are handled without losing the lead.
4. The draft waits with the status `pending`. A human **approves or rejects** it through the API.
5. The **Send Approved Emails** workflow picks up approved drafts and sends them by email. The lead then moves to `contacted` and the draft to `sent`.

Every status change is recorded in a history table.

## Demo walkthrough

A real run of the system, from form submission to the email arriving in an inbox.

### 1. A visitor fills in the contact form
![Contact form filled in](docs/screenshots/demo-1-form-filled.png)

### 2. The form is submitted
![Form submitted](docs/screenshots/demo-2-form-submitted.png)

### 3. The lead is saved and the AI draft is waiting for approval
The lead is `awaiting_approval` and the draft is `pending`. No email can be sent yet.

![Lead and draft pending in PostgreSQL](docs/screenshots/demo-3-pending.png)

### 4. A human approves the draft through the API
![Draft approved via the API](docs/screenshots/demo-4-approved.png)

### 5. The email arrives in the inbox
![Email received in Gmail](docs/screenshots/demo-5-gmail.png)

### 6. The database confirms the result
The lead is now `contacted` and the draft is `sent`.

![Lead contacted, draft sent](docs/screenshots/demo-6-sent.png)

## n8n workflows

### Lead Intake: webhook, create lead, Gemini analysis, validation, save
Every step ran successfully in this execution, with a separate path for AI errors.

![Lead Intake workflow execution](docs/screenshots/demo-7-lead-intake-run.png)

### Send Approved Emails: fetch approved drafts, send, mark as sent
It runs on a schedule and can also be started manually.

![Send Approved Emails workflow](docs/screenshots/demo-8-send-approved-run.png)

### Local test inbox (Mailpit)
During development, emails are caught by Mailpit so no real emails are sent.

![Mailpit test inbox](docs/screenshots/mailpit-inbox.png)

The exported workflows are in the [n8n-workflows](n8n-workflows) folder.

## Architecture

```
Contact form (n8n)
      |
      v
Website Form workflow --> Lead Intake workflow (n8n webhook)
                                   |
                                   v
                          FastAPI backend --> PostgreSQL
                                   |
                                   v
                         Gemini AI analysis + email draft
                                   |
                                   v
                    Draft saved as "pending" (awaiting approval)
                                   |
                       Human approves via API
                                   |
                                   v
              Send Approved Emails workflow (n8n) --> Email sent
```

## Tech stack

- **n8n**: workflow automation (form, intake, AI step, email sending)
- **Python + FastAPI**: backend API with validation and API key protection
- **PostgreSQL 16**: leads, AI analyses, email drafts and status history
- **Alembic**: database migrations
- **Google Gemini API** (free tier): lead analysis and email drafting
- **Docker Compose**: PostgreSQL, n8n and Mailpit
- **SMTP email**: tested with a real Gmail inbox; Mailpit is used for local testing
- **pytest**: automated backend tests

## Security and reliability

- The webhook and the backend both require secret keys (`x-api-key`), compared in constant time.
- Secrets live in a `.env` file that is excluded from Git; exported n8n workflows contain only credential names, never values.
- Duplicate leads are rejected with a clear error.
- Human approval is required before any email is sent, and a draft can only be reviewed once.
- If the AI call fails, the lead is still saved and the failure is recorded.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/leads` | Create a lead (validation and duplicate detection) |
| POST | `/leads/{id}/analysis` | Save the AI analysis and draft |
| GET | `/drafts/approved` | List approved drafts waiting to be sent |
| POST | `/drafts/{id}/review` | Approve or reject a draft |
| POST | `/drafts/{id}/sent` | Mark a draft as sent |

All endpoints under `/drafts` require the `x-api-key` header.

## Getting started

These steps assume Docker Desktop, Python 3.11 and Git are installed.

1. **Clone the repository**
   ```bash
   git clone https://github.com/mueenaliujan786-spec/ai-lead-management-automation.git
   cd ai-lead-management-automation
   ```
2. **Create your `.env` file** from `.env.example` and fill in your own values. `WEBHOOK_API_KEY` must be at least 32 characters.
3. **Start PostgreSQL, n8n and Mailpit**
   ```bash
   docker compose up -d
   ```
4. **Set up and start the backend** (from the `backend` folder, with a virtual environment active)
   ```bash
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --port 8000
   ```
5. **Import the workflows** from the `n8n-workflows` folder into n8n (`http://localhost:5678`), create the credentials they reference (a webhook secret, the backend API key, a Gemini API key and an SMTP login), then publish them.
6. **Open the form** from the Contact Form node's Production URL, submit a test lead, approve the draft through the API, and check the inbox.

## Documentation

- [MVP scope](docs/mvp.md)
- [Architecture](docs/architecture.md)
- [Database design](docs/database.md)

## Roadmap

- [x] Phase 1: Requirements and planning
- [x] Phase 2: Environment setup
- [x] Phase 3: Backend development
- [x] Phase 4: n8n workflows
- [x] Phase 5: Email and approval system
- [ ] Phase 6: Frontend dashboard (React + Tailwind)
- [ ] Phase 7: Extended testing and security review
- [ ] Phase 8: Deployment
- [ ] Phase 9: Portfolio preparation
