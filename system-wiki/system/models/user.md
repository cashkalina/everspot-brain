---
model: User
module: System
table: users
connection: central
primary_source: app/Models/User.php
source_paths: []
traits:
  - Authenticatable
  - Authorizable
  - CanResetPassword
  - HasApiTokens
  - MustVerifyEmail
  - Notifiable
  - TwoFactorAuthenticatable
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# User

## Overview

The User model represents a **central-database administrator or staff account** — the identity that logs in to manage Everspot itself. It stores credentials, authentication state, and security tracking in the `users` table of the central database and is entirely separate from the tenant-side user model (`modules/Common/Models/User.php`), which lives in each tenant's own database and carries a different schema (27 columns vs. the 17 here).

This model does **not** extend `BaseModel` — it extends Laravel's plain `Model` directly. It implements the three standard Laravel auth contracts (`AuthenticatableContract`, `AuthorizableContract`, `CanResetPasswordContract`) and fulfils them through the corresponding framework traits. On top of the framework auth stack, it uses Laravel Sanctum for API token issuance and Laravel Fortify for two-factor authentication.

The security surface is deliberately tracked at the database level: `failed_login_attempts`, `locked_out_at`, and `last_login_attempt_at` provide brute-force lockout signals, while `last_login_ip` supports audit trails. The `is_active` flag controls whether an account may authenticate at all. The `isESUser()` method distinguishes internal Everspot staff accounts (by domain + verified email) from external admin users.

> **Not the tenant user.** The tenant-side `User` model (documented at `modules/common/models/user.md`) shares the name but is a completely different class, stored in each tenant's own database, and used for cemetery staff/operators. Always clarify which user you mean when writing queries or policies.

## Schema

<!-- rendered from schema/central.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| first_name | varchar | No | - | User's first name |
| last_name | varchar | No | - | User's last name |
| email | varchar | No | - | Login email address; unique |
| email_verified_at | timestamp | Yes | - | When the email was verified (null = unverified) |
| password | varchar | No | - | Bcrypt-hashed password (hidden from serialization) |
| two_factor_secret | text | Yes | - | Encrypted TOTP secret (via [TwoFactorAuthenticatable](../traits/index.md#twofactorauthenticatable) — see trait doc) |
| two_factor_recovery_codes | text | Yes | - | Encrypted recovery codes (via [TwoFactorAuthenticatable](../traits/index.md#twofactorauthenticatable) — see trait doc) |
| two_factor_confirmed_at | timestamp | Yes | - | When 2FA was confirmed/activated (via [TwoFactorAuthenticatable](../traits/index.md#twofactorauthenticatable) — see trait doc) |
| is_active | varchar | No | 1 | Whether the account can authenticate (`"1"` / `"0"`) |
| remember_token | varchar | Yes | - | "Remember me" cookie token (hidden from serialization) |
| failed_login_attempts | int | No | 0 | Count of consecutive failed login attempts |
| locked_out_at | timestamp | Yes | - | When the account was locked due to failed attempts |
| last_login_attempt_at | timestamp | Yes | - | Timestamp of the most recent login attempt |
| last_login_ip | varchar | Yes | - | IP address of the most recent login attempt |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** _None_

**Indexes:** unique index on `email`

## Casts

_None declared on this model._ (Two-factor columns are encrypted by Fortify at the application layer, not via model casts.)

## Attributes

**Fillable:** `['first_name', 'last_name', 'email', 'password']`
**Hidden:** `['password', 'remember_token']`
**Visible:** _None._
**Appends:** _None._ (accessors below are not auto-appended to array/JSON output)
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getFullNameAttribute(): string` — concatenates `first_name` and `last_name` with a space (trimmed); e.g. `"Jane Smith"`
- `getNameAttribute(): string` — alias for `full_name`; returns the same value as `getFullNameAttribute()`
- `getInitialsAttribute(): string` — one uppercase character from `first_name` (if set) and one from `last_name` (if set), concatenated; e.g. `"JS"`. Returns an empty string if both names are null.

## Traits

- [Authenticatable](../traits/index.md#authenticatable) — provides `getAuthIdentifier()`, `getAuthPassword()`, `getRememberToken()`/`setRememberToken()` and related session-login helpers
- [Authorizable](../traits/index.md#authorizable) — proxies `can()` / `cannot()` / `canAny()` checks through the Laravel Gate facade
- [CanResetPassword](../traits/index.md#canresetpassword) — dispatches the password-reset notification email via `sendPasswordResetNotification()`
- [HasApiTokens](../traits/index.md#hasapitokens) — Laravel Sanctum; issues and manages API bearer tokens (`createToken()`, `tokenCan()`, `tokens()` relationship)
- [MustVerifyEmail](../traits/index.md#mustverifyemail) — provides `hasVerifiedEmail()`, `markEmailAsVerified()`, and `sendEmailVerificationNotification()` for email verification flow
- [Notifiable](../traits/index.md#notifiable) — adds `notify()` / `notifyNow()` and the `notifications()` morphMany relationship for Laravel notifications
- [TwoFactorAuthenticatable](../traits/index.md#twofactorauthenticatable) — Fortify TOTP two-factor auth: manages the `two_factor_secret`, `two_factor_recovery_codes`, and `two_factor_confirmed_at` columns; provides `hasEnabledTwoFactorAuthentication()`, `twoFactorQrCodeSvg()`

## Relationships

_None defined on this model._ (Sanctum's `tokens()` relationship is contributed by [HasApiTokens](../traits/index.md#hasapitokens); Notifiable's `notifications()` is contributed by [Notifiable](../traits/index.md#notifiable).)

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

- `isESUser(): bool` — returns `true` when the user's email ends with `@everspot.io` **and** the email has been verified; used to gate internal Everspot staff access paths

## Common Usage

```php
// Find a user by email
$user = User::where('email', 'admin@example.com')->firstOrFail();

// Display name helpers
echo $user->full_name;  // "Jane Smith"
echo $user->name;       // "Jane Smith" (alias)
echo $user->initials;   // "JS"

// Check if the user is an internal Everspot staff member
if ($user->isESUser()) {
    // grant elevated access
}

// Check whether 2FA is active
if ($user->hasEnabledTwoFactorAuthentication()) {
    // require OTP challenge
}

// Issue a Sanctum API token
$token = $user->createToken('mobile-app')->plainTextToken;

// Check whether an email is verified
if ($user->hasVerifiedEmail()) {
    // proceed
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
