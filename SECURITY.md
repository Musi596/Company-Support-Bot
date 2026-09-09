# 🛡️ Security Policy

## Scope

This document defines the security requirements and threat mitigation strategies for the **SoftClub Support Telegram Bot** and its associated PostgreSQL database.

The system processes and manages:
* User support tickets and message histories
* Administrator responses and ticket state transitions
* Telegram user identities (`user_id`, `username`, display names)
* Authorized group chat IDs and access rights
* Environment variables and deployment credentials

---

## Supported Versions

Only official release versions and the primary deployment branch receive active security updates and patches.

| Version | Supported | Notes |
| :--- | :--- | :--- |
| `v1.2.x` (Latest Release) | ✅ Yes | Current stable release |
| `v1.0.x` | ✅ Yes | Production-ready baseline |
| Latest `main` branch | ✅ Yes | Active development |
| Pre-releases (`v1.x.x-rc`) | ⚠️ Testing only | Not recommended for production |
| Legacy tags / commits | ❌ No | Please upgrade to the latest patch |

---

## Core Security Principles

1. **Zero Trust for Inputs**: Every Telegram message, command, and callback payload must be treated as untrusted data.
2. **Strict Authorization**: Admin functionality must require explicit validation against trusted database records on every request.
3. **Secret Isolation**: Secrets, tokens, and database passwords must never exist within source code or version control.
4. **Least Privilege**: Application database users must possess only the minimum required CRUD privileges.
5. **Data Privacy in Logs**: Logs must never capture authorization tokens, raw database credentials, or sensitive personal payload.

---

## Secret Management

* Store all credentials in environment variables using `.env` files for local development.
* Ensure `.env` and all secret-bearing files are explicitly declared in `.gitignore`.
* Use safe secret injection mechanisms in production (e.g., Docker secrets, systemd environment files, or Vault).

### Required Environment Variables

```env
# Telegram Configuration
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyZ

# PostgreSQL Credentials
DB_HOST=localhost
DB_PORT=5432
DB_NAME=support_bot
DB_USER=bot_app_user
DB_PASSWORD=use_a_strong_generated_password

# Access Control
SUPERADMIN_TG_ID=123456789
```

---

## Admin & Group Access Control

### Command & Action Guarding
All administrative commands, FSM states, and inline callback queries must pass strict role validation. 

```python
# Guard example for handlers and callbacks
if not await services.is_admin(pool, event.from_user.id):
    if isinstance(event, CallbackQuery):
        await event.answer("Access denied.", show_alert=True)
    return
```

### Mandatory Access Checks
Enforce `is_admin` validation across:
* `/start` administrative menu branches
* Ticket queue navigation and inspection
* Ticket status mutations (`reply`, `skip`, `close`)
* Group broadcast and newsletter dispatch workflows

### Group Chat Isolation
* The bot must reject commands from unauthorized group chats.
* Group chats must only be registered via authorized administrative routines (`/add_group`).

---

## Input Validation & Database Security

### SQL Injection Prevention
* Direct string concatenation or formatted strings (`f"SELECT ... {input}"`) in SQL queries are strictly prohibited.
* Use prepared statements and parameterized queries with `asyncpg`:

```python
# CORRECT
await pool.fetch("SELECT * FROM tickets WHERE id = $1 AND status = $2", ticket_id, status)

# INCORRECT (Vulnerable)
await pool.fetch(f"SELECT * FROM tickets WHERE id = {ticket_id}")
```

### Callback Payload Validation
* Validate callback formats before splitting or parsing parameters.
* Ensure ticket IDs extracted from `reply_tk:<id>` or `skip_tk:<id>` are valid integers before database queries.

---

## Telegram Bot & Network Security

### Webhook Security (Production)
When operating on Webhook mode instead of Long Polling:
* Always configure `secret_token` in `setWebhook`.
* Validate the `X-Telegram-Bot-Api-Secret-Token` header on incoming HTTP requests.
* Restrict incoming traffic to official Telegram IP ranges.

### Rate Limiting (Anti-Spam)
* Implement an Aiogram `BaseMiddleware` rate-limiter (Throttling) to prevent request flooding.
* Enforce cool-down periods on ticket creation and global broadcasting commands.

---

## Logging and Privacy

* Never log the `BOT_TOKEN` or PostgreSQL connection strings containing passwords.
* Log security events (e.g., unauthorized admin attempts, group registration failures) with sanitized metadata (`user_id`, `action`, `timestamp`).

---

## Vulnerability Reporting

If you discover a security vulnerability, please report it responsibly instead of opening a public GitHub issue.

### How to Report
Send a detailed security report directly to the maintainer:
* **Email**: `nuso3813@gmail.com`
* **Telegram**: `@SeattleWLF`

### Report Details
Please include:
1. Description and potential impact of the vulnerability
2. Affected files, endpoints, or handlers
3. Step-by-step Proof of Concept (PoC) to reproduce
4. Suggested remediation or patch (if available)

### Disclosure Timeline
* **Acknowledgement**: Within 24–48 hours
* **Assessment & Fix Plan**: Within 7 business days
* **Patch Release**: Prior to public disclosure

---

## Pre-Deployment Security Checklist

Before deploying the bot to production, ensure all checks pass:

- [ ] `.env` is omitted from Git history and present in `.gitignore`.
- [ ] Database user has restricted privileges (no `SUPERUSER` or `DROP TABLE` rights).
- [ ] Prepared statements (`asyncpg`) are used for all database interactions.
- [ ] Admin validation middleware/guards are applied to all sensitive handlers.
- [ ] Callback query payloads are strictly validated and type-checked.
- [ ] Webhook `secret_token` validation is active (if running via Webhook).
- [ ] Rate-limiting (throttling middleware) is active on user inputs.
- [ ] Logs are verified to contain no exposed tokens or database passwords.
