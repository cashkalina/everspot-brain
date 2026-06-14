---
model: User
module: Common
table: users
connection: tenant
primary_source: modules/Common/Models/User.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Providers/CommonServiceProvider.php
  - modules/Common/Observers/UserObserver.php
  - modules/Common/Database/Factories/UserFactory.php
  - modules/Common/Pivots/DashboardUserPivot.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/Dashboard.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Models/Note.php
  - modules/Common/Models/Token.php
  - modules/Commission/Models/CommissionPlan.php
  - modules/Commission/Pivots/CommissionPlanUserPivot.php
  - modules/Event/Models/Calendar.php
  - modules/Task/Models/Task.php
traits:
  - HasFactory
  - HasFiles
  - HasSearch
  - HasSettings
related_models: [Cemetery, CommissionPlan, Dashboard, ListOption, Note, Token, Calendar]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [core, admin]
---

# User

## Overview

The `Modules\Common\Models\User` model is the **tenant-side** user — the authenticated employee or staff member who works within a specific cemetery tenant. It is distinct from `app/Models/User` (the central-database user, documented at `system/models/user.md`). All `HasByUserFields` audit relationships (`createdBy()`, `updatedBy()`, `deletedBy()`) throughout the system target this model.

The model implements multiple Laravel contracts (Authenticatable, Authorizable, CanResetPassword, MustVerifyEmail) and extends `BaseModel`. It integrates Spatie Permission (`HasRoles`) for RBAC, Laravel Fortify two-factor authentication (`TwoFactorAuthenticatable`), Sanctum API tokens (`HasApiTokens`), Spatie Activitylog (`CausesActivity`), and media attachments for user avatars (`HasFiles`).

The model tracks login security state: failed login attempts, lockout timestamps, last login IP and attempt time, and SSO provider details. A user account is locked after 10 consecutive failed login attempts. Multi-factor authentication is required for `@everspot.io` accounts in production and optionally for other accounts via settings hierarchy.

The `manager_id` and `sales_manager_id` self-referential relationships create management hierarchies used by `GetAllSubordinatesForUser` to determine which user calendars and tasks a user can view.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| first_name | varchar | No | - | First name |
| last_name | varchar | No | - | Last name |
| email | varchar | No | - | Email address (unique) |
| email_verified_at | timestamp | Yes | - | When email was verified |
| password | varchar | No | - | Hashed password (hidden) |
| sso_provider | varchar | Yes | - | SSO provider name |
| sso_provider_id | varchar | Yes | - | SSO provider user ID |
| two_factor_secret | text | Yes | - | Encrypted TOTP secret (hidden) |
| two_factor_recovery_codes | text | Yes | - | Encrypted recovery codes (hidden) |
| two_factor_confirmed_at | timestamp | Yes | - | When 2FA was confirmed |
| access_pin | varchar | Yes | - | Access PIN for quick authentication (unique, hidden) |
| is_active | varchar | No | 1 | Whether the user account is active |
| login_access | varchar | No | 1 | Whether the user can log in |
| calendar_color | varchar | Yes | - | Hex color for calendar events |
| position | varchar | Yes | - | Job position/title |
| department_id | bigint | Yes | - | FK → list_options: department |
| cemetery_id | bigint | Yes | - | FK → cemeteries: primary cemetery |
| manager_id | bigint | Yes | - | FK → users: line manager |
| sales_manager_id | bigint | Yes | - | FK → users: sales manager |
| remember_token | varchar | Yes | - | Laravel remember-me token (hidden) |
| failed_login_attempts | int | No | 0 | Consecutive failed login attempts |
| locked_out_at | timestamp | Yes | - | When the account was locked |
| last_login_attempt_at | timestamp | Yes | - | Timestamp of last login attempt |
| last_login_ip | varchar | Yes | - | IP address of last login attempt |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Unique indexes:** `email`; `access_pin`; composite (`sso_provider`, `sso_provider_id`)

**Foreign keys:** `cemetery_id` → `cemeteries.id`; `department_id` → `list_options.id`; `manager_id`, `sales_manager_id` → `users.id`

**Indexes:** `locked_out_at`; composite (`email`, `locked_out_at`); `manager_id`; `sales_manager_id`.

## Casts

- `email_verified_at` → `TimezonedDateTime::class`
- `locked_out_at` → `datetime`
- `last_login_attempt_at` → `datetime`
- `two_factor_confirmed_at` → `datetime`
- `created_at` → `datetime`
- `updated_at` → `datetime`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['first_name', 'last_name', 'email', 'password', 'calendar_color', 'two_factor_confirmed_at', 'failed_login_attempts', 'locked_out_at', 'last_login_attempt_at', 'last_login_ip', 'sso_provider', 'sso_provider_id']`

**Hidden:** `['password', 'remember_token', 'access_pin', 'two_factor_secret', 'two_factor_recovery_codes']`

**Disabled report columns:** `password`, `remember_token`, `access_pin`, `two_factor_secret`, `two_factor_recovery_codes`

**File collections:** `['avatar' => 'single']`

## Accessors & Mutators

- `getDepartmentAttribute(): ?string` — name of the related department [ListOption](./list-option.md)
- `getFullNameAttribute(): string` — `"$first_name $last_name"` trimmed
- `getNameAttribute(): string` — alias for `full_name`
- `getInitialsAttribute(): string` — uppercase initials from first and last name characters
- `getAvatarHtmlBySize($size = null): string` — generates an HTML `<span>` avatar element (image or initials) with optional size class

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (wired to `UserFactory`)
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary attachments (avatar collection via `['avatar' => 'single']`)
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing; `addToSearchData()` provides `full_name` and `email` for Scout
- [HasSettings](../../../system/traits/index.md#hassettings) — key-value settings store scoped to this user (e.g. user-level `timezone`)

## Relationships

- `cemetery()` — belongs to [Cemetery](./cemetery.md) (`cemetery_id`): the user's primary cemetery
- `manager()` — belongs to [User](./user.md) (`manager_id`): the user's line manager
- `salesManager()` — belongs to [User](./user.md) (`sales_manager_id`): the user's sales manager
- `commissionPlans()` — belongs-to-many [CommissionPlan](../../commission/models/commission-plan.md) via `commission_plan_user` (using `CommissionPlanUserPivot`; pivot: `id`, `effective_start_date`, `effective_end_date`)
- `notes()` — morphMany [Note](./note.md) (`notable`): notes on this user
- `departmentOption()` — belongs to [ListOption](./list-option.md) (`department_id`): department lookup
- `tokens()` — morphMany [Token](./token.md) (`tokenable`): API/OAuth tokens for this user
- `dashboards()` — belongs-to-many [Dashboard](./dashboard.md) via `dashboard_user` (using `DashboardUserPivot`; pivot: `id`, `is_default`)
- `ownedCalendars()` — has many [Calendar](../../event/models/calendar.md) (`owner_id`): calendars this user owns
- `accessibleCalendars()` — belongs-to-many [Calendar](../../event/models/calendar.md) via `calendar_permissions` (pivot: `permission_type`, timestamps): calendars shared with this user
- `avatar()` — morphOne Media (from `media` table) where `collection_name = 'avatar'`

## Scopes

- `deliveryAgents($query): Builder` — filters to active users (`is_active = true`)

## Events

_None._

## Observers

- `UserObserver` — registered in `CommonServiceProvider::registerObservers()` (`User::observe(UserObserver::class)`). Handles:
  - `created` — post-creation side effects (e.g. analytics, CRM sync)
  - `updated` — post-update side effects
  - `saved` — fires after any save
  - `deleted` — cleanup hooks

## Key Methods

- `defaultDashboard(): ?Dashboard` — returns the user's is_default dashboard, or the first dashboard if none is default
- `allAccessibleCalendars()` — merges `ownedCalendars` and `accessibleCalendars` (distinct by ID)
- `getViewableUserCalendars(): Collection` — all users whose personal calendars this user may view (all users if has `viewAllCalendars` permission; otherwise sales + management subordinates)
- `getPersonalCalendar()` — returns this user's personal calendar (type `PERSONAL`) from `ownedCalendars`
- `getAdminCalendars(): Collection` — calendars where the user has admin permission (all if has global `calendar-update`; otherwise owned + explicitly permitted)
- `getViewableCalendars(): Collection` — full set of calendars visible to this user
- `getViewableUserTasks(): Collection` — users whose tasks this user can view (all if `viewAllTasks`; otherwise subordinates)
- `addToSearchData(): array` — returns `['full_name', 'email']` for search indexing
- `getActivitylogOptions(): LogOptions` — configures activity logging (all fields except sensitive ones; dirty-only; no empty logs)
- `isESUser(): bool` — `true` for verified `@everspot.io` email accounts
- `isMfaRequired(): bool` — `true` for ES users in production; otherwise checks `mfa_required` setting hierarchy (user → cemetery → tenant)
- `isLockedOut(): bool` — `true` when `failed_login_attempts >= 10` and `locked_out_at` is set
- `incrementFailedLoginAttempts(Request $request): void` — increments counter, records IP/time, locks after 10 failures
- `resetFailedLoginAttempts(): void` — resets counter and lockout
- `clearLockout(): void` — alias for `resetFailedLoginAttempts()` (used on password reset)
- `getTwoFactorSecret(): ?string` — decrypts and returns the TOTP secret
- `getRecoveryCodes(): array` — decrypts and returns recovery codes as an array
- `useRecoveryCode(string $code): bool` — validates and consumes a recovery code; returns `true` if used

## Common Usage

```php
// Get the authenticated user
$user = auth()->user();  // Modules\Common\Models\User instance

echo $user->full_name;    // "Jane Smith"
echo $user->initials;     // "JS"

// Check MFA requirement
if ($user->isMfaRequired() && !$user->two_factor_confirmed_at) {
    redirect()->route('two-factor.setup');
}

// Handle failed login
$user->incrementFailedLoginAttempts($request);
if ($user->isLockedOut()) {
    return response('Account locked', 403);
}

// Get user's default dashboard
$dashboard = $user->defaultDashboard();

// Get viewable calendars
$calendars = $user->getViewableCalendars();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
