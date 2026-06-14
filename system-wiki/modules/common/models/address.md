---
model: Address
module: Common
table: addresses
connection: tenant
primary_source: modules/Common/Models/Address.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Providers/CommonServiceProvider.php
  - modules/Common/Observers/AddressObserver.php
  - modules/Common/Models/State.php
  - modules/Common/Models/Country.php
  - modules/Common/Models/ListOption.php
traits: []
related_models: [Country, ListOption, State]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [core, admin]
---

# Address

## Overview

The Address model stores physical and mailing address records for any entity in the system via a polymorphic `addressable` relationship. Customers, entities, and other addressable models can each have multiple addresses, each tagged as a default billing address (`billing_default = 1`), a default shipping address (`shipping_default = 1`), or neither.

Beyond basic street address fields (`line_one`, `line_two`, `line_three`, `city`, `state_id`, `postcode`, `country_id`), an address can optionally hold an individual's name (first, last, suffix) and company name, plus contact details (email and phone). The `meta` JSON column stores additional per-address metadata. Phone numbers are stripped to digits only on write via a mutator.

The model has no traits of its own beyond what is inherited from `BaseModel`. Lifecycle events are handled by `AddressObserver`, registered in `CommonServiceProvider`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| addressable_type | varchar | No | - | Morph type — the class name of the owning model |
| addressable_id | bigint | No | - | Morph ID — the owning model's primary key |
| country_id | bigint | Yes | - | FK → countries: country |
| title_id | bigint | Yes | - | FK → list_options: name title |
| first_name | varchar | Yes | - | Address recipient first name |
| last_name | varchar | Yes | - | Address recipient last name |
| suffix_id | bigint | Yes | - | FK → list_options: name suffix |
| company_name | varchar | Yes | - | Company name |
| line_one | varchar | Yes | - | Street address line 1 |
| line_two | varchar | Yes | - | Street address line 2 |
| line_three | varchar | Yes | - | Street address line 3 |
| city | varchar | Yes | - | City |
| state_id | bigint | Yes | - | FK → states: state/province |
| postcode | varchar | Yes | - | Postal / ZIP code |
| delivery_instructions | varchar | Yes | - | Free-text delivery instructions |
| contact_email | varchar | Yes | - | Contact email |
| contact_phone | varchar | Yes | - | Contact phone (digits only; normalized on set) |
| meta | json | Yes | - | Additional metadata |
| shipping_default | tinyint | No | 0 | Whether this is the default shipping address |
| billing_default | tinyint | No | 0 | Whether this is the default billing address |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `country_id` → `countries.id`; `state_id` → `states.id`; `title_id`, `suffix_id` → `list_options.id`

**Indexes:** composite index on (`addressable_type`, `addressable_id`); FK-backing indexes on `country_id`, `state_id`, `title_id`, `suffix_id`.

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** N/A — `$guarded` not set; however `$disabledReportColumns` excludes `meta` from report columns
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** `shipping_default` = 0; `billing_default` = 0 (database defaults)

## Accessors & Mutators

- `getTitleAttribute(): ?string` — name of the related title [ListOption](./list-option.md) (`titleOption?->name`)
- `getSuffixAttribute(): ?string` — name of the related suffix [ListOption](./list-option.md) (`suffixOption?->name`)
- `getTitleFullNameAttribute(): string` — title + first + last name joined, extra whitespace collapsed
- `getFormattedPhoneNumberAttribute(): ?string` — `contact_phone` run through the `FormatPhoneNumber` action
- `getPreviewAttribute(): string` — one-line address preview: `line_one, line_two, city, STATE postcode`
- `getParagraphFullAddressAttribute(): string` — multi-line HTML address block with name, company, street lines, city/state/postcode, phone, and email (`<br>`-separated)
- `getParagraphAddressAttribute(): string` — multi-line HTML address block with street lines, city/state/postcode only (no name/contact fields, `<br>`-separated)
- `setContactPhoneAttribute($value): void` — **mutator**: strips all non-digits from `contact_phone` on write (null-safe)

## Traits

_None._

## Relationships

- `addressable()` — morphTo: the owning model (may be Customer, Entity, or any other addressable)
- `state()` — belongs to [State](./state.md) (`state_id`): state or province
- `country()` — belongs to [Country](./country.md) (`country_id`): country
- `titleOption()` — belongs to [ListOption](./list-option.md) (`title_id`): name title
- `suffixOption()` — belongs to [ListOption](./list-option.md) (`suffix_id`): name suffix

## Scopes

_None._

## Events

_None._

## Observers

- `AddressObserver` — registered in `CommonServiceProvider::registerObservers()` (`Address::observe(AddressObserver::class)`). Handles:
  - `saving` — normalizes address data before save
  - `created` — fires post-creation side effects
  - `updated` — fires post-update side effects
  - `deleted`, `restored`, `forceDeleted` — cleanup hooks

## Key Methods

_None beyond accessors and relationships._

## Common Usage

```php
// Add a billing address to a customer
$customer->addresses()->create([
    'line_one'        => '123 Main St',
    'city'            => 'Springfield',
    'state_id'        => $state->id,
    'postcode'        => '12345',
    'billing_default' => 1,
]);

// Retrieve the default billing address
$billing = $customer->defaultBillingAddress;

// One-line preview
echo $billing->preview;   // "123 Main St, Springfield, IL 12345"

// Full HTML address block
echo $billing->paragraph_full_address;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
