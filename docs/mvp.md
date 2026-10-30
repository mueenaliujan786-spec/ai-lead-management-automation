# MVP Scope: AI-Powered Lead Management & Follow-Up Automation

## What the MVP does

1. A customer submits a lead (name, email, message, source) to a webhook.
2. The backend validates the data and rejects bad or duplicate leads.
3. Valid leads are saved in PostgreSQL.
4. n8n sends the lead message to an AI and gets back structured JSON:
   category, priority, summary, recommended action, email draft.
5. The backend validates the AI response and saves it.
6. A human logs in to a dashboard, reviews the AI analysis,
   and approves, edits, or rejects the email draft.
7. Approved emails are sent through an email provider.
8. Every workflow run (success or failure) is recorded.

## MVP features (build these first)

- Lead submission webhook
- Input validation and duplicate detection
- PostgreSQL storage with lead status history
- AI analysis with validated JSON output
- Human approval before any email is sent
- Login for dashboard users
- Dashboard: lead list, lead details, draft approval
- Execution log with limited retries (no unlimited retries)

## Version 2 features (build later)

- Scheduled follow-up reminders
- Unsubscribe and opt-out handling
- Analytics and charts
- Error and retry monitoring page
- Role-based permissions
- Multiple AI providers

## Rules that must never be broken

- No email is sent without human approval.
- The same email is never sent twice.
- Retries always have a maximum limit.
- No passwords or API keys are stored in GitHub.
- AI output is a recommendation, not a verified fact.

## Definition of done for the MVP

A fake lead can be submitted, analyzed by AI, approved by a human,
and emailed, and every step is visible in the database and dashboard.