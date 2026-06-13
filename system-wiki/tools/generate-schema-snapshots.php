#!/usr/bin/env php
<?php

/**
 * Standalone Schema Snapshot Generator for Everspot System Wiki
 *
 * Boots Everspot's Laravel framework in-process and introspects database schema
 * WITHOUT writing any files to Everspot repository (read-only).
 *
 * Usage:
 *   php tools/generate-schema-snapshots.php \
 *     --central schema/central.json \
 *     --tenant schema/tenant.json \
 *     --tenant-id <throwaway-tenant-id>
 *
 * Requirements:
 *   - Everspot repository must be available at path specified in wiki.config.json
 *   - Everspot must have vendor/autoload.php (composer install completed)
 *   - Database connections must be configured in Everspot's .env
 *   - A valid tenant ID must be provided for tenant schema extraction
 *
 * @see meta/phase4-fix-and-validate.md Task 2 for specification
 */

// Parse command line arguments
$options = getopt('', ['central:', 'tenant:', 'tenant-id:', 'help']);

if (isset($options['help'])) {
    echo "Usage: php generate-schema-snapshots.php [OPTIONS]\n\n";
    echo "Options:\n";
    echo "  --central <path>     Path to write central schema JSON (required)\n";
    echo "  --tenant <path>      Path to write tenant schema JSON (required)\n";
    echo "  --tenant-id <id>     Tenant ID to use for tenant context (required)\n";
    echo "  --help               Show this help message\n\n";
    echo "Example:\n";
    echo "  php tools/generate-schema-snapshots.php \\\n";
    echo "    --central schema/central.json \\\n";
    echo "    --tenant schema/tenant.json \\\n";
    echo "    --tenant-id throwaway-test-tenant\n\n";
    exit(0);
}

// Validate arguments
$centralOutput = $options['central'] ?? null;
$tenantOutput = $options['tenant'] ?? null;
$tenantId = $options['tenant-id'] ?? null;

if (!$centralOutput || !$tenantOutput || !$tenantId) {
    fwrite(STDERR, "ERROR: Missing required arguments\n");
    fwrite(STDERR, "Run with --help for usage information\n");
    exit(1);
}

// Resolve paths relative to script directory (tools/)
$scriptDir = __DIR__;
$wikiRoot = dirname($scriptDir);

$centralOutput = resolveOutputPath($centralOutput, $wikiRoot);
$tenantOutput = resolveOutputPath($tenantOutput, $wikiRoot);

// Load wiki configuration
$configPath = $wikiRoot . '/wiki.config.json';
if (!file_exists($configPath)) {
    fwrite(STDERR, "ERROR: wiki.config.json not found at: {$configPath}\n");
    exit(1);
}

$config = json_decode(file_get_contents($configPath), true);
if (!isset($config['everspot_repo_path'])) {
    fwrite(STDERR, "ERROR: everspot_repo_path not configured in wiki.config.json\n");
    exit(1);
}

$everspotPath = $config['everspot_repo_path'];

// Validate Everspot repository
if (!is_dir($everspotPath)) {
    fwrite(STDERR, "ERROR: Everspot repository not found at: {$everspotPath}\n");
    fwrite(STDERR, "Update wiki.config.json with correct path\n");
    exit(1);
}

$autoloadPath = $everspotPath . '/vendor/autoload.php';
if (!file_exists($autoloadPath)) {
    fwrite(STDERR, "ERROR: Composer autoload not found at: {$autoloadPath}\n");
    fwrite(STDERR, "Run 'composer install' in Everspot repository first\n");
    exit(1);
}

$bootstrapPath = $everspotPath . '/bootstrap/app.php';
if (!file_exists($bootstrapPath)) {
    fwrite(STDERR, "ERROR: Laravel bootstrap not found at: {$bootstrapPath}\n");
    fwrite(STDERR, "Not a valid Laravel application\n");
    exit(1);
}

echo "==> Using Everspot repository: {$everspotPath}\n";
echo "==> Wiki repository: {$wikiRoot}\n";
echo "==> Tenant ID: {$tenantId}\n\n";

// Boot Everspot framework
echo "==> Booting Everspot Laravel framework...\n";

require $autoloadPath;
$app = require $bootstrapPath;

// Boot console kernel
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

echo "    ✓ Framework booted successfully\n";
echo "    Laravel version: " . $app->version() . "\n\n";

// Get Everspot's current git commit
$everspotCommit = getEverspotCommit($everspotPath);
echo "    Everspot commit: {$everspotCommit}\n\n";

// Define framework/noise tables to skip
$skipTables = [
    'migrations',
    'jobs',
    'failed_jobs',
    'cache',
    'cache_locks',
    'sessions',
    'password_reset_tokens',
];

// Skip telescope, nova, pulse tables (pattern matching)
$skipPatterns = [
    '/^telescope_/',
    '/^nova_/',
    '/^pulse_/',
    '/^personal_access_tokens$/',
];

// Extract central schema
echo "==> Extracting central schema...\n";
$centralSnapshot = extractSchema($app, 'central', $everspotCommit, $skipTables, $skipPatterns);

// Ensure output directory exists
ensureDirectoryExists(dirname($centralOutput));

// Write central snapshot
file_put_contents($centralOutput, json_encode($centralSnapshot, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
echo "    ✓ Written to: {$centralOutput}\n";
echo "    Tables captured: " . count($centralSnapshot['tables']) . "\n\n";

// Extract tenant schema
echo "==> Extracting tenant schema...\n";
echo "    Initializing tenant context: {$tenantId}\n";

try {
    // Get tenant model class from config
    $tenantModelClass = config('tenancy.tenant_model');

    // Find the tenant
    $tenant = $tenantModelClass::find($tenantId);

    if (!$tenant) {
        throw new Exception("Tenant not found: {$tenantId}");
    }

    echo "    ✓ Tenant found\n";

    // Initialize tenancy
    tenancy()->initialize($tenant);
    echo "    ✓ Tenancy initialized\n";

    // Extract schema from tenant connection
    $tenantSnapshot = extractSchema($app, 'tenant', $everspotCommit, $skipTables, $skipPatterns);

    // End tenancy
    tenancy()->end();
    echo "    ✓ Tenancy ended\n";

} catch (Exception $e) {
    fwrite(STDERR, "\nERROR: Failed to extract tenant schema\n");
    fwrite(STDERR, $e->getMessage() . "\n");
    exit(1);
}

// Ensure output directory exists
ensureDirectoryExists(dirname($tenantOutput));

// Write tenant snapshot
file_put_contents($tenantOutput, json_encode($tenantSnapshot, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
echo "    ✓ Written to: {$tenantOutput}\n";
echo "    Tables captured: " . count($tenantSnapshot['tables']) . "\n\n";

echo "==> Schema snapshots generated successfully!\n\n";
echo "Files:\n";
echo "  - {$centralOutput}\n";
echo "  - {$tenantOutput}\n\n";

exit(0);

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Resolve output path (make absolute if relative)
 */
function resolveOutputPath(string $path, string $wikiRoot): string
{
    if ($path[0] === '/') {
        return $path; // Already absolute
    }
    return $wikiRoot . '/' . $path;
}

/**
 * Get Everspot's current git commit
 */
function getEverspotCommit(string $everspotPath): string
{
    $cwd = getcwd();
    chdir($everspotPath);

    // Try origin/main first
    $commit = trim(shell_exec('git rev-parse origin/main 2>/dev/null') ?: '');

    if (!$commit) {
        // Fallback to HEAD
        $commit = trim(shell_exec('git rev-parse HEAD 2>/dev/null') ?: 'unknown');
        if ($commit !== 'unknown') {
            echo "    ⚠ Warning: origin/main not found, using HEAD commit\n";
        }
    }

    chdir($cwd);
    return $commit;
}

/**
 * Ensure directory exists
 */
function ensureDirectoryExists(string $dir): void
{
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
    }
}

/**
 * Check if table should be skipped
 */
function shouldSkipTable(string $tableName, array $skipTables, array $skipPatterns): bool
{
    // Check exact matches
    if (in_array($tableName, $skipTables)) {
        return true;
    }

    // Check pattern matches
    foreach ($skipPatterns as $pattern) {
        if (preg_match($pattern, $tableName)) {
            return true;
        }
    }

    return false;
}

/**
 * Extract schema from a database connection
 */
function extractSchema($app, string $connection, string $commit, array $skipTables, array $skipPatterns): array
{
    $schema = Illuminate\Support\Facades\Schema::connection($connection);
    $db = Illuminate\Support\Facades\DB::connection($connection);

    // Verify connection
    try {
        $db->getPdo();
    } catch (Exception $e) {
        throw new Exception("Cannot connect to database '{$connection}': " . $e->getMessage());
    }

    $tables = [];
    $skippedTables = [];

    foreach ($schema->getTables() as $table) {
        $tableName = $table['name'];

        // Skip framework/noise tables
        if (shouldSkipTable($tableName, $skipTables, $skipPatterns)) {
            $skippedTables[] = $tableName;
            continue;
        }

        echo "    Extracting: {$tableName}\n";

        $tables[$tableName] = [
            'columns' => extractColumns($schema, $tableName),
            'indexes' => extractIndexes($schema, $tableName),
            'foreign_keys' => extractForeignKeys($schema, $tableName),
        ];
    }

    if ($skippedTables) {
        echo "    Skipped " . count($skippedTables) . " framework tables: " . implode(', ', $skippedTables) . "\n";
    }

    return [
        'snapshot_commit' => $commit,
        'generated_at' => now()->toISOString(),
        'connection' => $connection,
        'tables' => $tables,
        'meta' => [
            'extraction_method' => 'laravel_schema_builder',
            'laravel_version' => $app->version(),
            'database_driver' => config("database.connections.{$connection}.driver"),
            'table_count' => count($tables),
            'generated_by' => 'generate-schema-snapshots.php (standalone introspection)',
        ],
    ];
}

/**
 * Extract column definitions for a table
 */
function extractColumns($schema, string $table): array
{
    $columns = [];

    foreach ($schema->getColumns($table) as $column) {
        $columns[] = [
            'name' => $column['name'],
            'type' => normalizeType($column),
            'nullable' => $column['nullable'],
            'default' => $column['default'],
            'auto_increment' => $column['auto_increment'] ?? false,
            'comment' => $column['comment'] ?? '',
        ];
    }

    return $columns;
}

/**
 * Extract index definitions for a table
 */
function extractIndexes($schema, string $table): array
{
    $indexes = [];

    foreach ($schema->getIndexes($table) as $index) {
        $indexes[] = [
            'name' => $index['name'],
            'columns' => $index['columns'],
            'type' => $index['primary'] ? 'primary' : ($index['unique'] ? 'unique' : 'index'),
            'unique' => $index['unique'] ?? false,
        ];
    }

    return $indexes;
}

/**
 * Extract foreign key constraints for a table
 */
function extractForeignKeys($schema, string $table): array
{
    $foreignKeys = [];

    foreach ($schema->getForeignKeys($table) as $fk) {
        $foreignKeys[] = [
            'columns' => $fk['columns'],
            'foreign_table' => $fk['foreign_table'],
            'foreign_columns' => $fk['foreign_columns'],
            'on_delete' => $fk['on_delete'] ?? 'restrict',
            'on_update' => $fk['on_update'] ?? 'restrict',
        ];
    }

    return $foreignKeys;
}

/**
 * Normalize column type to consistent format
 */
function normalizeType(array $column): string
{
    $type = $column['type_name'] ?? $column['type'];

    // Add length/precision if available
    if (isset($column['length']) && $column['length']) {
        $type .= "({$column['length']})";
    } elseif (isset($column['precision']) && isset($column['scale'])) {
        $type .= "({$column['precision']},{$column['scale']})";
    }

    return $type;
}
