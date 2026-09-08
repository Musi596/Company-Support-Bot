# Security Policy

## Scope

This document defines the security requirements for the SoftClub support Telegram bot and associated PostgreSQL database.

The project handles:
- user messages and support tickets;
- admin replies;
- Telegram user IDs and names;
- database records with user and ticket data;
- environment variables with secrets.

## Supported Versions

The project currently supports the latest committed version on the main branch.

Only the latest revision is considered supported for security fixes.

## Core Security Principles

1. Secrets must never be stored in source code.
2. Administrative access must be limited to trusted user IDs only.
3. Telegram input must be treated as untrusted data.
4. Access to ticket data and admin actions must be strictly authorized.
5. Logs must not contain personal data or secrets.

## Secret Management

- Store all secrets in environment variables only.
- Use `.env` files only locally and never commit them.
- Add `.env` and related secret files to `.gitignore`.
- Use a production-safe secret manager in deployment environments.

Required variables include, at minimum:
- `API_TOKEN`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

Example:

```env
API_TOKEN=your_telegram_bot_token
DB_NAME=support_bot
DB_USER=postgres
DB_PASSWORD=strong_password
```

## Admin Access Control

- Only verified admin accounts may access admin functions.
- Admin role must be assigned only through a trusted database change or secure admin setup flow.
- The bot must validate admin rights before showing admin-only commands, buttons, and ticket actions.
- Do not expose admin features to regular clients.

Recommended rule:

```python
if not await services.is_admin(pool, user_id):
    return
```

This validation must be enforced for:
- `/start` admin branch;
- admin ticket list;
- ticket selection;
- reply actions;
- skip actions;
- ticket closing logic.

## Input Validation and Safe Handling

Because Telegram messages come from users, all content must be treated as untrusted.

Rules:
- Do not execute user-provided text as code or SQL.
- Do not allow raw SQL construction from message content.
- Escape or parameterize all database queries.
- Limit message length if necessary to prevent abuse.
- Sanitize text before displaying to admins or users.

## Database Security

- Use PostgreSQL with restricted credentials.
- Grant the application only the required privileges.
- Never expose the database port publicly unless required.
- Use a private network or internal-only access in production.
- Keep PostgreSQL updated to the latest patched version.

Recommended practices:
- use a dedicated database user for the bot;
- separate admin and client roles in the application logic;
- keep the `users` and `tickets` tables protected by least-privilege access.

## Telegram Bot Security

- Do not trust callback data blindly.
- Validate that callback payloads match expected formats before parsing.
- Check that the user is an admin before processing admin callbacks like `reply_tk:*` or `skip_tk:*`.
- Reject unknown callback data and malformed ticket IDs.

Example validation:

```python
if not await services.is_admin(pool, callback.from_user.id):
    await callback.answer("Вы не администратор.", show_alert=True)
    return
```

## Logging and Monitoring

- Log security-relevant events such as admin actions, ticket replies, and errors.
- Do not log full Telegram tokens, database passwords, or raw credentials.
- Mask sensitive IDs when possible.
- Monitor failed admin access attempts and unexpected callback usage.

## Rate Limiting and Abuse Control

- Restrict repeated bot actions to prevent spam.
- Consider limiting:
  - ticket creation frequency;
  - admin reply actions;
  - callback processing bursts.
- Add basic anti-abuse controls if the bot is public or used by many users.

## Data Handling

The bot stores user tickets and messages. This information should be handled carefully:
- only store what is necessary;
- keep ticket data limited to support workflow requirements;
- avoid exposing raw ticket content to unauthorized users;
- ensure admin reply data is protected from unauthorized access.

## Vulnerability Reporting

If you discover a security vulnerability in this project, please report it privately and responsibly.

Please send details to the project maintainer via a secure channel and include:
- description of the vulnerability;
- affected files or code paths;
- steps to reproduce;
- impact assessment;
- any suggested fix or mitigation.

Do not create public GitHub issues for security vulnerabilities until the issue has been addressed or a responsible disclosure process is agreed.

## Disclosure Expectations

We aim to:
- acknowledge valid reports promptly;
- assess severity and impact;
- provide a fix or mitigation plan;
- keep the reporter informed during the remediation process.

## Security Checklist Before Deployment

Before running the bot in a production environment, verify:

- [ ] `.env` is excluded from version control
- [ ] API token is valid and not exposed in code
- [ ] database credentials are separate from local development values
- [ ] admin checks are enforced on all admin actions
- [ ] callback data is validated
- [ ] no direct SQL injection vectors exist
- [ ] error logs do not expose secrets
- [ ] bot is running with least-privilege permissions
- [ ] backups and database access are protected

## Final Note

This project is a support bot and therefore processes potentially sensitive user data. Security should be treated as a requirement, not an optional layer.
