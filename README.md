## AI Lead Management Automation

A small-business lead pipeline: a customer fills in a web form, an AI classifies the inquiry and drafts a reply, **a human approves it**, and only then is the email sent.

### How it works

1. A customer submits the web form (n8n form).
2. The lead is saved in PostgreSQL through a FastAPI backend.
3. Gemini classifies the lead, sets a priority and drafts a polite reply.
4. The draft waits as `pending` until a person approves or rejects it.
5. Approved drafts are emailed automatically and the lead becomes `contacted`.

### Safety and reliability

- Webhook protected by a secret header (strangers get 403 and nothing is saved).
- Prompt-injection test: a message asking for a "90% discount" did not change the AI draft.
- Duplicate leads and double approvals are refused (one email can never be sent twice).
- Failed AI calls are retried and recorded instead of lost.
- Secrets live in `.env` (not in Git); API keys were rotated after testing.

### Tech stack

n8n, FastAPI (Python), PostgreSQL, Docker Compose, Gemini API, Mailpit (local test inbox).

### Run locally

1. Copy `.env.example` to `.env` and fill in the values.
2. Run `docker compose up -d`.
3. Open n8n at http://localhost:5678, API docs at http://localhost:8000/docs, test inbox at http://localhost:8025.
4. The three n8n workflows are Lead Intake, Send Approved Emails and Website Form.

### Demo

| Step | Screenshot |
|---|---|
| 1. Customer fills in the form | ![Form](docs/screenshots/demo-1-form-filled.png) |
| 2. Form submitted | ![Submitted](docs/screenshots/demo-2-form-submitted.png) |
| 3. Lead waits for approval | ![Pending](docs/screenshots/demo-3-pending.png) |
| 4. A person approves the draft | ![Approved](docs/screenshots/demo-4-approved.png) |
| 5. The email arrives | ![Email](docs/screenshots/demo-5-gmail.png) |
| 6. Status becomes contacted and sent | ![Sent](docs/screenshots/demo-6-sent.png) |
| 7. Lead Intake workflow run | ![Run 1](docs/screenshots/demo-7-lead-intake-run.png) |
| 8. Send Approved Emails workflow run | ![Run 2](docs/screenshots/demo-8-send-approved-run.png) |

### Limitations

Runs locally with a test inbox. Real Gmail delivery was tested once for the demo. The free Gemini tier can be slow or busy, so a retry workflow is a planned improvement.
