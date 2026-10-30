# Database Design (PostgreSQL)

This is the first draft. It will be refined in Phase 3 when migrations are written.

## Tables

### 1. users
Dashboard users who can log in and approve emails.
- id (PK)
- email (unique)
- password_hash (never store plain passwords)
- full_name
- role (admin, reviewer)
- is_active
- created_at

### 2. leads
Every valid lead received.
- id (PK)
- full_name
- email
- phone (optional)
- company (optional)
- service_interest
- message
- source (website, landing page, api, manual)
- status (new, analyzed, awaiting_approval, contacted, closed, opted_out)
- follow_up_paused (true/false)
- created_at
- updated_at

### 3. lead_status_history
Every time a lead's status changes.
- id (PK)
- lead_id (FK -> leads.id)
- old_status
- new_status
- changed_by (FK -> users.id, can be empty for automatic changes)
- changed_at

### 4. lead_ai_analyses
The AI's analysis of a lead. This is a recommendation, not a verified fact.
- id (PK)
- lead_id (FK -> leads.id)
- category
- priority (High, Medium, Low)
- intent
- summary
- recommended_action
- ai_model
- status (success, failed)
- created_at

### 5. email_drafts
Draft emails waiting for human review.
- id (PK)
- lead_id (FK -> leads.id)
- analysis_id (FK -> lead_ai_analyses.id)
- subject
- body
- status (pending, approved, rejected, sent)
- reviewed_by (FK -> users.id)
- reviewed_at
- created_at

### 6. email_messages
Emails that were actually sent.
- id (PK)
- draft_id (FK -> email_drafts.id, unique so the same draft is never sent twice)
- provider_message_id
- delivery_status
- sent_at

### 7. follow_up_tasks
Scheduled follow-up reminders (Version 2).
- id (PK)
- lead_id (FK -> leads.id)
- due_at
- status (scheduled, done, cancelled)
- created_at

### 8. workflow_executions
Technical log of every workflow run.
- id (PK)
- lead_id (FK -> leads.id)
- workflow_name
- n8n_execution_id
- stage
- status (running, success, failed)
- error_message
- retry_count
- last_retry_at
- started_at
- finished_at

### 9. audit_logs
Business actions done by users or the system.
- id (PK)
- actor_user_id (FK -> users.id, can be empty for system actions)
- action (lead_created, email_approved, email_rejected, ...)
- entity_type
- entity_id
- created_at

## Relationships

- One lead has many status history rows.
- One lead has many AI analyses.
- One lead has many email drafts.
- One email draft has at most one sent email message.
- One lead has many follow-up tasks.
- One lead has many workflow executions.
- One user can approve many email drafts.

## Important rules

- The same email is never sent twice (unique draft_id in email_messages).
- Passwords are stored only as hashes.
- Do not store more personal data than needed.
- Add indexes on leads.email, leads.status, and workflow_executions.status for fast searching.