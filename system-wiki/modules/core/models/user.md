---
model: User
module: Core
table: users
connection: central
source_paths:
  - app/Models/User.php
related: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-13
completeness: complete
deprecated: false
tags: [auth, user, core, central]
---

# User

**Primary source:** `app/Models/User.php`

## Overview

The User model represents system users who authenticate and access the Everspot platform. Users are stored in the central database and can access multiple tenants based on their permissions and tenant associations.

This model implements Laravel's authentication contracts and uses Fortify for authentication features including two-factor authentication, email verification, and password reset functionality. It leverages Sanctum for API token management.

Users are identified by email addresses and have basic profile information (first name, last name). The model tracks authentication security features including failed login attempts, account lockouts, and login history. Special handling exists for Everspot employees (users with @everspot.io email addresses) who have verified email addresses.

## Connection & Table

Central · `users`

## Schema

<!-- Rendered from schema/central.json -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| first_name | varchar | No | - | User's first name |
| last_name | varchar | No | - | User's last name |
| email | varchar | No | - | User's email address (unique) |
| email_verified_at | timestamp | Yes | - | Email verification timestamp |
| password | varchar | No | - | Hashed password |
| two_factor_secret | text | Yes | - | Two-factor authentication secret |
| two_factor_recovery_codes | text | Yes | - | Two-factor recovery codes |
| two_factor_confirmed_at | timestamp | Yes | - | Two-factor confirmation timestamp |
| is_active | varchar | No | 1 | Whether user account is active |
| remember_token | varchar | Yes | - | Remember me token |
| failed_login_attempts | int | No | 0 | Count of failed login attempts |
| locked_out_at | timestamp | Yes | - | Account lockout timestamp |
| last_login_attempt_at | timestamp | Yes | - | Last login attempt timestamp |
| last_login_ip | varchar | Yes | - | Last login IP address |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

## Properties / Casts

**Fillable:**
- `['first_name', 'last_name', 'email', 'password']`

**Hidden Attributes:**
- `['password', 'remember_token']` — Never exposed in arrays/JSON

**Casts:**
No explicit casts defined (uses defaults from authentication traits)

## Relationships

No relationships are defined in the base User model. Tenant-specific associations are likely handled through the `tenant_users` pivot table in the central database.

## Key Methods

- `getFullNameAttribute(): string` — Returns concatenated first and last name
- `getNameAttribute(): string` — Alias for full_name attribute
- `getInitialsAttribute(): string` — Returns uppercase initials from first and last name
- `isESUser(): bool` — Returns true if user has verified @everspot.io email address

## Scopes / Events / Observers

**Email Verification:**
- Uses `MustVerifyEmail` trait from Laravel
- Email verification required for full account access

**Two-Factor Authentication:**
- Uses `TwoFactorAuthenticatable` trait from Laravel Fortify
- Supports 2FA secret, recovery codes, and confirmation tracking

**API Authentication:**
- Uses `HasApiTokens` trait from Laravel Sanctum
- Supports API token generation and management

**Account Security:**
- `failed_login_attempts` — Incremented on failed logins
- `locked_out_at` — Set when account is locked due to failed attempts
- `last_login_attempt_at` — Updated on each login attempt
- `last_login_ip` — Records IP address of login attempts

## Common Usage

```php
// Create a new user
$user = User::create([
    'first_name' => 'Jane',
    'last_name' => 'Smith',
    'email' => 'jane@example.com',
    'password' => Hash::make('secure-password'),
]);

// Access computed name attributes
echo $user->full_name; // "Jane Smith"
echo $user->name; // "Jane Smith" (alias)
echo $user->initials; // "JS"

// Check if Everspot employee
if ($user->isESUser()) {
    // Grant special Everspot employee permissions
}

// Email verification
$user->markEmailAsVerified();
if ($user->hasVerifiedEmail()) {
    // Email is verified
}

// Two-factor authentication
if ($user->two_factor_secret) {
    // 2FA is enabled
}

// API tokens (Sanctum)
$token = $user->createToken('api-token')->plainTextToken;

// Authentication
Auth::attempt([
    'email' => 'jane@example.com',
    'password' => 'password'
]);

// Get authenticated user
$user = Auth::user();

// Password reset
$user->sendPasswordResetNotification($token);

// Check account status
if ($user->is_active && !$user->locked_out_at) {
    // Account is active and not locked
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
