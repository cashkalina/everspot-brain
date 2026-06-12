<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

/**
 * Wiki Schema Snapshot Generator
 *
 * Generates JSON schema snapshots for the Everspot System Wiki.
 * Must be copied to app/Console/Commands/ in the Everspot repository.
 *
 * Usage:
 *   Central: php artisan wiki:schema-snapshot central --output=/path/to/wiki/schema/central.json
 *   Tenant:  php artisan tenants:run <tenant-id> --command="wiki:schema-snapshot tenant"
 *
 * @see meta/commands.md §4 for specification
 * @see meta/phase3-build-log.md for implementation notes
 */
class WikiSchemaSnapshot extends Command
{
    protected $signature = 'wiki:schema-snapshot
                            {connection : Database connection (central or tenant)}
                            {--output= : Output file path (default: storage/schema-{connection}.json)}
                            {--wiki-path= : Path to wiki repository for direct write}';

    protected $description = 'Generate schema snapshot JSON for Everspot System Wiki';

    public function handle()
    {
        $connection = $this->argument('connection');

        // Validate connection
        if (!in_array($connection, ['central', 'tenant'])) {
            $this->error("Connection must be 'central' or 'tenant'");
            return 1;
        }

        // Verify connection exists
        try {
            DB::connection($connection)->getPdo();
        } catch (\Exception $e) {
            $this->error("Cannot connect to database: {$connection}");
            $this->error($e->getMessage());
            return 1;
        }

        // Determine output path
        $output = $this->option('output');
        if (!$output) {
            if ($wikiPath = $this->option('wiki-path')) {
                $output = rtrim($wikiPath, '/') . "/schema/{$connection}.json";
            } else {
                $output = storage_path("schema-{$connection}.json");
            }
        }

        // Ensure output directory exists
        $dir = dirname($output);
        if (!is_dir($dir)) {
            mkdir($dir, 0755, true);
        }

        $this->info("Extracting schema from connection: {$connection}");

        // Get current git commit
        $commit = trim(shell_exec('git rev-parse HEAD 2>/dev/null') ?: 'unknown');
        if ($commit === 'unknown') {
            $this->warn('Could not determine git commit (not in a git repository)');
        }

        // Build snapshot
        $tables = $this->extractTables($connection);

        $snapshot = [
            'snapshot_commit' => $commit,
            'generated_at' => now()->toISOString(),
            'connection' => $connection,
            'tables' => $tables,
            'meta' => [
                'extraction_method' => 'laravel_schema_builder',
                'laravel_version' => app()->version(),
                'database_driver' => config("database.connections.{$connection}.driver"),
                'table_count' => count($tables),
                'generated_by' => 'WikiSchemaSnapshot artisan command'
            ]
        ];

        // Write JSON
        $json = json_encode($snapshot, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
        file_put_contents($output, $json);

        $this->info("Schema snapshot written to: {$output}");
        $this->info("Tables captured: " . count($tables));
        $this->info("Snapshot commit: {$commit}");

        // Show table list
        if ($this->output->isVerbose()) {
            $this->line("\nTables:");
            foreach (array_keys($tables) as $tableName) {
                $columnCount = count($tables[$tableName]['columns']);
                $this->line("  - {$tableName} ({$columnCount} columns)");
            }
        }

        return 0;
    }

    /**
     * Extract all tables from the connection
     */
    protected function extractTables(string $connection): array
    {
        $schema = Schema::connection($connection);
        $tables = [];

        $this->info("Discovering tables...");

        foreach ($schema->getTables() as $table) {
            $tableName = $table['name'];

            // Skip migrations table
            if ($tableName === 'migrations') {
                continue;
            }

            $this->line("  Extracting: {$tableName}");

            $tables[$tableName] = [
                'columns' => $this->extractColumns($connection, $tableName),
                'indexes' => $this->extractIndexes($connection, $tableName),
                'foreign_keys' => $this->extractForeignKeys($connection, $tableName)
            ];
        }

        return $tables;
    }

    /**
     * Extract column definitions for a table
     */
    protected function extractColumns(string $connection, string $table): array
    {
        $columns = [];

        foreach (Schema::connection($connection)->getColumns($table) as $column) {
            $columns[] = [
                'name' => $column['name'],
                'type' => $this->normalizeType($column),
                'nullable' => $column['nullable'],
                'default' => $column['default'],
                'auto_increment' => $column['auto_increment'] ?? false,
                'comment' => $column['comment'] ?? ''
            ];
        }

        return $columns;
    }

    /**
     * Extract index definitions for a table
     */
    protected function extractIndexes(string $connection, string $table): array
    {
        $indexes = [];

        foreach (Schema::connection($connection)->getIndexes($table) as $index) {
            $indexes[] = [
                'name' => $index['name'],
                'columns' => $index['columns'],
                'type' => $index['primary'] ? 'primary' : ($index['unique'] ? 'unique' : 'index'),
                'unique' => $index['unique'] ?? false
            ];
        }

        return $indexes;
    }

    /**
     * Extract foreign key constraints for a table
     */
    protected function extractForeignKeys(string $connection, string $table): array
    {
        $foreignKeys = [];

        foreach (Schema::connection($connection)->getForeignKeys($table) as $fk) {
            $foreignKeys[] = [
                'columns' => $fk['columns'],
                'foreign_table' => $fk['foreign_table'],
                'foreign_columns' => $fk['foreign_columns'],
                'on_delete' => $fk['on_delete'] ?? 'restrict',
                'on_update' => $fk['on_update'] ?? 'restrict'
            ];
        }

        return $foreignKeys;
    }

    /**
     * Normalize column type to consistent format
     */
    protected function normalizeType(array $column): string
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
}
