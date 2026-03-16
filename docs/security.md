# Security Baseline

## Secrets

- Store secrets in environment variables or a secret manager.
- Never commit real `.env` files.
- Rotate JWT, SMTP, and Telegram secrets on environment bootstrap.

## Identity controls

- Passwords must be hashed with Argon2 or bcrypt.
- Use short-lived access tokens and rotated refresh tokens.
- Require verification for email and Telegram identity binding.
- Enforce RBAC for `user`, `admin`, and `superadmin`.

## Service-level controls

- Enable HTTPS in deployed environments.
- Protect webhooks with signatures or shared secrets.
- Add rate limiting on auth and bot endpoints.
- Audit privileged actions in `admin_audit_logs`.

## Data handling

- Minimize personally identifiable data.
- Support user export and deletion flows.
- Retain analytics and audit logs separately from profile data.
