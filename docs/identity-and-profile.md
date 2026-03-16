# Identity And Profile

## Auth service scope

- email registration and sign-in
- refresh token rotation
- Telegram account linking
- role assignment for `user`, `admin`, `superadmin`
- session lifecycle and password reset

## Shared identity models

- `UserAccount`
- `UserIdentity`
- `TokenPair`

These are implemented in `packages/common/identity.py` and are intended to be reused across `auth-service`, `api-gateway`, and `bot-service`.

## Profile service scope

- career headline and summary
- target roles
- location and work format preferences
- salary expectations
- skill inventory and self-assessment

## Shared profile models

- `ProfilePreference`
- `ProfileSkill`
- `CareerProfile`

These are implemented in `packages/common/profile.py` and are intended to be reused across `profile-service`, `recommendation-service`, and `assessment-service`.
