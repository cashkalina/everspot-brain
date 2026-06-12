# extract-model-skeleton.php

Extracts deterministic, mechanical parts of model documentation from Everspot source code, leaving only prose sections for AI to write.

## Purpose

This script mechanizes Phase 5 of the wiki build process by:
- Extracting all code-derivable metadata from models
- Handling inheritance (parent classes, traits)
- Deriving source paths automatically
- Producing partial markdown with AI sections clearly marked

## Usage

```bash
php tools/extract-model-skeleton.php <model-path>
```

**Example:**
```bash
php tools/extract-model-skeleton.php modules/Transaction/Models/Payment.php > modules/transaction/models/payment.draft.md
```

## Input

- **model-path**: Relative path from Everspot repo root to the model file
  - Example: `modules/Transaction/Models/Payment.php`
  - Example: `app/Models/User.php`

## Output

The script outputs to STDOUT a partial markdown document with:

**MECHANICAL SECTIONS (fully populated):**
- Frontmatter (except `connection` if not explicit, `tags`, `completeness`)
- `source_paths` array (model + parent + traits + scopes)
- `related` array (extracted from relationship methods)
- Properties section with casts, fillable, guarded, etc.
- Relationship method signatures (with inheritance separated)
- Public method signatures (with inheritance separated)
- Scope methods (global and query scopes)
- Section structure and headers

**AI SECTIONS (marked with `<!-- AI: ... -->`):**
- Overview prose
- Connection determination (if not explicit in $connection)
- Relationship descriptions
- Method descriptions
- Common Usage examples
- Tags selection
- Completeness assessment
- Events and observers documentation

## How It Works

1. **Reads from git**: Fetches model source via `git show origin/main:<path>` from Everspot repo
2. **Parses model class**: Extracts namespace, class name, parent, traits, properties, methods
3. **Handles inheritance**: Recursively parses parent classes (Transaction, BaseModel)
4. **Derives source paths**: Finds all trait files, scope files, parent classes
5. **Extracts relationships**: Identifies relationship methods by return type
6. **Generates markdown**: Outputs partial doc with mechanical sections filled

## Features

**Inheritance Handling:**
- Parses parent classes recursively
- Separates "Defined in X" vs "Inherited from Y" sections
- Merges table/connection from parent if not overridden
- Includes parent's traits in source paths

**STI Pattern Support:**
- Detects Single Table Inheritance (e.g., Payment extends Transaction)
- Uses parent's table name if child doesn't define one
- Includes parent model in `related` array
- Extracts TransactionByTypeScope global scopes

**Source Path Derivation:**
- Model file itself
- Parent class files (Transaction, BaseModel)
- All trait files (HasModelNumbering, HasMoneyFields, etc.)
- Global scope files (TransactionByTypeScope)
- Searches common locations: modules/Common/Traits/, app/Models/, etc.

**Property Extraction:**
- $casts (with type mapping)
- $fillable, $guarded (notes empty array = mass-assignable)
- $appends, $hidden
- $moneyAttributes (custom property)
- $searchableColumns (custom property)

**Method Extraction:**
- Public methods with signatures and return types
- Separates relationship methods (HasMany, BelongsTo, etc.)
- Filters out magic methods (__construct, etc.)
- Filters out booted/boot lifecycle hooks
- Preserves scope methods (scopeActive, etc.)

**Relationship Detection:**
- Identifies by return type: HasMany, BelongsTo, MorphTo, etc.
- Extracts from both model and parent classes
- Derives related model names (heuristic: refunds() → Refund)

## Limitations

1. **Schema rendering**: Requires schema snapshots (schema/tenant.json, schema/central.json)
   - Script leaves placeholder for AI to render from snapshot
   - Future: could read snapshot and render table automatically

2. **Connection inference**: Cannot always determine tenant vs central
   - Leaves `<!-- AI: Determine connection -->` marker if not explicit
   - Future: could check which snapshot contains the table

3. **Related model names**: Uses heuristic pluralization
   - refunds() → Refund (works)
   - journalEntries() → JournalEntrie (fails on 'ies' pluralization)
   - Polymorphic relationships: Transactionable, Postable (correct but abstract)

4. **Method body analysis**: Does not parse method bodies
   - Cannot extract event dispatches, observer registrations
   - Cannot determine what events are fired
   - Leaves `<!-- AI: Document events and observers -->` marker

5. **Trait method extraction**: Does not parse trait methods
   - Only lists traits in source_paths
   - AI must describe what each trait provides

6. **Constants and enums**: Not extracted
   - Does not capture TYPES, STATUSES, METHODS constants
   - AI must document these from source

## Integration Points

**Generate Command (future):**
```bash
# Generate skeleton
php tools/extract-model-skeleton.php modules/Transaction/Models/Payment.php > /tmp/payment.skeleton.md

# AI fills in prose sections
claude-code --context /tmp/payment.skeleton.md "Fill in all AI sections marked with <!-- AI: ... -->"

# Validate against snapshot
php tools/validate-model-doc.php modules/transaction/models/payment.md

# Commit if valid
git add modules/transaction/models/payment.md
```

**Sync Command (future):**
- For each affected model: regenerate skeleton
- Preserve human-authored content (<!-- human:begin -->...<!-- human:end -->)
- AI re-fills AI-owned sections
- Validate before commit

## Configuration

Requires `wiki.config.json` in wiki root:
```json
{
  "everspot_repo_path": "/Users/cashkalina/code/everspot",
  "canonical_branch": "main"
}
```

## Exit Codes

- `0`: Success, markdown written to STDOUT
- `1`: Error (config missing, model not found, parse failure)

Errors written to STDERR, markdown to STDOUT (pipe-friendly).

## Testing

Verify against the Payment vertical slice:

```bash
# Generate skeleton
php tools/extract-model-skeleton.php modules/Transaction/Models/Payment.php > /tmp/payment-test.md

# Compare mechanical sections to hand-written payment.md
# (Expect differences only in AI-written prose)
```

## Known Issues

1. **Pluralization edge cases**: "entries" → "Entrie" instead of "Entry"
   - Workaround: AI corrects in relationship descriptions
   - Future: improve pluralization heuristic

2. **Polymorphic type names**: Generates abstract names like "Transactionable"
   - Expected: These are correct but represent multiple concrete types
   - AI should document in relationship description

3. **Duplicate guarded in parent/child**: Both show `guarded: []`
   - Acceptable: Shows explicitly that both classes are mass-assignable
   - Alternative: could suppress if identical to parent

4. **Scope methods in Key Methods**: Query scopes appear in methods section
   - Acceptable: They are public methods
   - Also listed in Scopes section for discoverability
