#!/usr/bin/env php
<?php
/**
 * Model Documentation Skeleton Extractor
 *
 * Purpose: Extract deterministic, mechanical parts of model documentation from Everspot source code.
 * Leaves only prose sections for AI to write.
 *
 * Usage: php tools/extract-model-skeleton.php <model-path>
 * Example: php tools/extract-model-skeleton.php modules/Transaction/Models/Payment.php
 *
 * Reads Everspot via git show origin/main:<path> pattern.
 * Outputs partial markdown with mechanical sections filled and AI sections marked.
 */

define('WIKI_ROOT', dirname(__DIR__));

// Load config
$configPath = WIKI_ROOT . '/wiki.config.json';
if (!file_exists($configPath)) {
    fwrite(STDERR, "ERROR: wiki.config.json not found. Copy wiki.config.example.json and configure.\n");
    exit(1);
}

$config = json_decode(file_get_contents($configPath), true);
$everspotPath = $config['everspot_repo_path'] ?? null;
$canonicalBranch = $config['canonical_branch'] ?? 'main';

if (!$everspotPath || !is_dir($everspotPath)) {
    fwrite(STDERR, "ERROR: Invalid everspot_repo_path in wiki.config.json\n");
    exit(1);
}

// Parse arguments
if ($argc < 2) {
    fwrite(STDERR, "Usage: php extract-model-skeleton.php <model-path>\n");
    fwrite(STDERR, "Example: php extract-model-skeleton.php modules/Transaction/Models/Payment.php\n");
    exit(1);
}

$modelPath = $argv[1];

// Fetch model source from git
function fetchFromGit($repoPath, $branch, $filePath) {
    $command = sprintf(
        'cd %s && git show %s:%s 2>&1',
        escapeshellarg($repoPath),
        escapeshellarg("origin/$branch"),
        escapeshellarg($filePath)
    );

    $output = [];
    $returnCode = 0;
    exec($command, $output, $returnCode);

    if ($returnCode !== 0) {
        return null;
    }

    return implode("\n", $output);
}

// Parse PHP class for metadata
function parseModel($source, $isParent = false) {
    $data = [
        'namespace' => null,
        'className' => null,
        'extends' => null,
        'traits' => [],
        'table' => null,
        'connection' => null,
        'casts' => [],
        'fillable' => [],
        'guarded' => [],
        'appends' => [],
        'hidden' => [],
        'moneyAttributes' => [],
        'searchableColumns' => [],
        'methods' => [],
        'scopes' => [],
        'globalScopes' => [],
        'relationshipMethods' => [],
        'isParent' => $isParent,
    ];

    // Extract namespace
    if (preg_match('/namespace\s+([\w\\\\]+);/', $source, $matches)) {
        $data['namespace'] = $matches[1];
    }

    // Extract class name and parent
    if (preg_match('/class\s+(\w+)(?:\s+extends\s+([\w\\\\]+))?/', $source, $matches)) {
        $data['className'] = $matches[1];
        $data['extends'] = $matches[2] ?? null;
    }

    // Extract traits
    if (preg_match_all('/use\s+([\w\\\\]+(?:\s*,\s*[\w\\\\]+)*);/m', $source, $matches)) {
        foreach ($matches[1] as $traitList) {
            $traits = array_map('trim', explode(',', $traitList));
            $data['traits'] = array_merge($data['traits'], $traits);
        }
    }

    // Extract table property
    if (preg_match('/protected\s+\$table\s*=\s*[\'"]([^\'"]+)[\'"];/', $source, $matches)) {
        $data['table'] = $matches[1];
    }

    // Extract connection property
    if (preg_match('/protected\s+\$connection\s*=\s*[\'"]([^\'"]+)[\'"];/', $source, $matches)) {
        $data['connection'] = $matches[1];
    }

    // Extract casts array
    if (preg_match('/protected\s+\$casts\s*=\s*\[(.*?)\];/s', $source, $matches)) {
        preg_match_all('/[\'"]([^\'"]+)[\'"]\s*=>\s*([^\n,]+)/s', $matches[1], $castMatches);
        for ($i = 0; $i < count($castMatches[1]); $i++) {
            $data['casts'][$castMatches[1][$i]] = trim($castMatches[2][$i], " \t\n\r,'\"");
        }
    }

    // Extract fillable array
    if (preg_match('/protected\s+\$fillable\s*=\s*\[(.*?)\];/s', $source, $matches)) {
        preg_match_all('/[\'"]([^\'"]+)[\'"]/', $matches[1], $fillableMatches);
        $data['fillable'] = $fillableMatches[1];
    }

    // Extract guarded array
    if (preg_match('/protected\s+\$guarded\s*=\s*\[(.*?)\];/s', $source, $matches)) {
        preg_match_all('/[\'"]([^\'"]+)[\'"]/', $matches[1], $guardedMatches);
        $data['guarded'] = $guardedMatches[1];
    }

    // Extract appends array
    if (preg_match('/protected\s+\$appends\s*=\s*\[(.*?)\];/s', $source, $matches)) {
        preg_match_all('/[\'"]([^\'"]+)[\'"]/', $matches[1], $appendsMatches);
        $data['appends'] = $appendsMatches[1];
    }

    // Extract hidden array
    if (preg_match('/protected\s+\$hidden\s*=\s*\[(.*?)\];/s', $source, $matches)) {
        preg_match_all('/[\'"]([^\'"]+)[\'"]/', $matches[1], $hiddenMatches);
        $data['hidden'] = $hiddenMatches[1];
    }

    // Extract moneyAttributes array
    if (preg_match('/public\s+array\s+\$moneyAttributes\s*=\s*\[(.*?)\];/s', $source, $matches)) {
        preg_match_all('/[\'"]([^\'"]+)[\'"]/', $matches[1], $moneyMatches);
        $data['moneyAttributes'] = $moneyMatches[1];
    }

    // Extract searchableColumns array
    if (preg_match('/protected\s+\$searchableColumns\s*=\s*\[(.*?)\];/s', $source, $matches)) {
        preg_match_all('/[\'"]([^\'"]+)[\'"]/', $matches[1], $searchMatches);
        $data['searchableColumns'] = $searchMatches[1];
    }

    // Extract global scopes from booted() method
    if (preg_match('/static::addGlobalScope\(new\s+([\w\\\\]+)\((.*?)\)\);/', $source, $matches)) {
        $data['globalScopes'][] = [
            'class' => $matches[1],
            'args' => trim($matches[2], " '\""),
        ];
    }

    // Extract public methods
    preg_match_all('/public\s+function\s+(\w+)\s*\((.*?)\)(?:\s*:\s*([^\n{]+))?/s', $source, $methodMatches, PREG_SET_ORDER);

    $relationshipTypes = ['HasMany', 'HasOne', 'BelongsTo', 'BelongsToMany', 'MorphTo', 'MorphMany', 'MorphOne', 'HasManyThrough'];

    foreach ($methodMatches as $methodMatch) {
        $methodName = $methodMatch[1];
        $params = $methodMatch[2];
        $returnType = isset($methodMatch[3]) ? trim($methodMatch[3]) : null;

        // Skip magic methods and lifecycle hooks
        if (strpos($methodName, '__') === 0 || in_array($methodName, ['booted', 'boot'])) {
            continue;
        }

        $method = [
            'name' => $methodName,
            'params' => $params,
            'returnType' => $returnType,
        ];

        // Check if it's a relationship method
        $isRelationship = false;
        if ($returnType) {
            foreach ($relationshipTypes as $relType) {
                if (strpos($returnType, $relType) !== false) {
                    $isRelationship = true;
                    break;
                }
            }
        }

        if ($isRelationship) {
            $data['relationshipMethods'][] = $method;
        } else {
            $data['methods'][] = $method;
        }
    }

    // Extract scope methods
    preg_match_all('/public\s+function\s+(scope\w+)\s*\(\s*\$query(?:,\s*([^)]*))?\)/s', $source, $scopeMatches, PREG_SET_ORDER);
    foreach ($scopeMatches as $scopeMatch) {
        $data['scopes'][] = [
            'name' => lcfirst(substr($scopeMatch[1], 5)), // Remove 'scope' prefix and lowercase first char
            'fullName' => $scopeMatch[1],
            'params' => isset($scopeMatch[2]) ? $scopeMatch[2] : '',
        ];
    }

    return $data;
}

// Infer table name from model name
function inferTableName($className) {
    // Simple pluralization (doesn't handle all cases, but works for most)
    $table = strtolower(preg_replace('/(?<!^)[A-Z]/', '_$0', $className));

    // Basic pluralization rules
    if (substr($table, -1) === 'y') {
        $table = substr($table, 0, -1) . 'ies';
    } elseif (!in_array(substr($table, -1), ['s', 'x', 'z'])) {
        $table .= 's';
    }

    return $table;
}

// Infer module name from path
function inferModuleName($modelPath) {
    if (preg_match('#modules/([^/]+)/#', $modelPath, $matches)) {
        return $matches[1];
    }
    if (strpos($modelPath, 'app/Models/') === 0) {
        return 'Core';
    }
    return 'Unknown';
}

// Recursively parse model with inheritance
function parseModelWithInheritance($repoPath, $branch, $modelPath) {
    $source = fetchFromGit($repoPath, $branch, $modelPath);
    if ($source === null) {
        return null;
    }

    $modelData = parseModel($source, false);

    // Parse parent class if it exists
    $parentData = null;
    if ($modelData['extends'] && !in_array($modelData['extends'], ['Model', 'Authenticatable'])) {
        $parentClass = $modelData['extends'];
        $modelDir = dirname($modelPath);

        // Try to find parent class file
        $parentFile = $modelDir . '/' . $parentClass . '.php';
        $parentSource = fetchFromGit($repoPath, $branch, $parentFile);

        if ($parentSource === null) {
            $parentFile = 'app/Models/' . $parentClass . '.php';
            $parentSource = fetchFromGit($repoPath, $branch, $parentFile);
        }

        if ($parentSource !== null) {
            $parentData = parseModel($parentSource, true);
            $parentData['_filePath'] = $parentFile;

            // Merge inherited properties (parent values are defaults unless overridden)
            if (!$modelData['table'] && $parentData['table']) {
                $modelData['table'] = $parentData['table'];
            }
            if (!$modelData['connection'] && $parentData['connection']) {
                $modelData['connection'] = $parentData['connection'];
            }

            // Store parent data for section rendering
            $modelData['_parentData'] = $parentData;
        }
    }

    return $modelData;
}

// Determine source paths
function deriveSourcePaths($repoPath, $branch, $modelPath, $modelData) {
    $paths = [$modelPath];

    // Add parent class if extends
    if (isset($modelData['_parentData'])) {
        $paths[] = $modelData['_parentData']['_filePath'];

        // Check if parent also has a parent
        $parentData = $modelData['_parentData'];
        if ($parentData['extends'] && !in_array($parentData['extends'], ['Model', 'Authenticatable'])) {
            $parentClass = $parentData['extends'];
            $parentFile = 'app/Models/' . $parentClass . '.php';
            $content = fetchFromGit($repoPath, $branch, $parentFile);
            if ($content !== null) {
                $paths[] = $parentFile;
            }
        }

        // Add parent's traits
        foreach ($parentData['traits'] as $trait) {
            $traitName = basename(str_replace('\\', '/', $trait));
            $traitPaths = [
                'modules/Common/Traits/' . $traitName . '.php',
                dirname($modelData['_parentData']['_filePath']) . '/Concerns/' . $traitName . '.php',
            ];

            foreach ($traitPaths as $traitPath) {
                $content = fetchFromGit($repoPath, $branch, $traitPath);
                if ($content !== null) {
                    $paths[] = $traitPath;
                    break;
                }
            }
        }
    }

    // Add trait files
    foreach ($modelData['traits'] as $trait) {
        $traitName = basename(str_replace('\\', '/', $trait));

        // Common trait locations
        $traitPaths = [
            'modules/Common/Traits/' . $traitName . '.php',
            dirname($modelPath) . '/Concerns/' . $traitName . '.php',
            dirname($modelPath) . '/Traits/' . $traitName . '.php',
        ];

        foreach ($traitPaths as $traitPath) {
            $content = fetchFromGit($repoPath, $branch, $traitPath);
            if ($content !== null) {
                $paths[] = $traitPath;
                break;
            }
        }
    }

    // Add global scope files
    foreach ($modelData['globalScopes'] as $scope) {
        $scopeName = basename(str_replace('\\', '/', $scope['class']));
        $scopePath = dirname($modelPath) . '/Scopes/' . $scopeName . '.php';

        $content = fetchFromGit($repoPath, $branch, $scopePath);
        if ($content !== null) {
            $paths[] = $scopePath;
        }
    }

    return array_unique($paths);
}

// Extract related models from relationships
function extractRelatedModels($modelData) {
    $related = [];

    // Add parent model if STI
    if (isset($modelData['_parentData'])) {
        $related[] = $modelData['_parentData']['className'];
    }

    // Extract from own relationships
    foreach ($modelData['relationshipMethods'] as $method) {
        $methodName = $method['name'];
        $singular = rtrim($methodName, 's');
        $modelName = ucfirst($singular);
        $related[] = $modelName;
    }

    // Extract from parent relationships
    if (isset($modelData['_parentData'])) {
        foreach ($modelData['_parentData']['relationshipMethods'] as $method) {
            $methodName = $method['name'];
            $singular = rtrim($methodName, 's');
            $modelName = ucfirst($singular);
            $related[] = $modelName;
        }
    }

    return array_unique($related);
}

// Get current commit hash
function getCurrentCommit($repoPath, $branch) {
    $command = sprintf(
        'cd %s && git rev-parse origin/%s 2>&1',
        escapeshellarg($repoPath),
        escapeshellarg($branch)
    );

    $output = [];
    exec($command, $output, $returnCode);

    if ($returnCode !== 0) {
        return 'unknown';
    }

    return trim($output[0]);
}

// Generate markdown skeleton
function generateMarkdownSkeleton($modelPath, $modelData, $sourcePaths, $relatedModels, $commitHash) {
    $className = $modelData['className'];
    $moduleName = inferModuleName($modelPath);
    $tableName = $modelData['table'] ?? inferTableName($className);
    $connection = $modelData['connection'] ?? '<!-- AI: Determine connection (tenant or central) -->';

    $markdown = "---\n";
    $markdown .= "model: $className\n";
    $markdown .= "module: $moduleName\n";
    $markdown .= "table: $tableName\n";
    $markdown .= "connection: $connection\n";
    $markdown .= "source_paths:\n";
    foreach ($sourcePaths as $path) {
        $markdown .= "  - $path\n";
    }
    if (!empty($relatedModels)) {
        $markdown .= "related: [" . implode(', ', $relatedModels) . "]\n";
    }
    $markdown .= "built_at: $commitHash\n";
    $markdown .= "last_updated: " . date('Y-m-d') . "\n";
    $markdown .= "completeness: <!-- AI: Assess completeness (complete/partial/stub) -->\n";
    $markdown .= "deprecated: false\n";
    $markdown .= "tags: <!-- AI: Add 2-4 tags from controlled vocabulary -->\n";
    $markdown .= "---\n\n";

    $markdown .= "# $className\n\n";
    $markdown .= "**Primary source:** `$modelPath`\n\n";

    $markdown .= "## Overview\n\n";
    $markdown .= "<!-- AI: Write 2-4 paragraph overview explaining:\n";
    $markdown .= "- What this model represents and its business purpose\n";
    $markdown .= "- Key characteristics (STI, polymorphic, etc.)\n";
    $markdown .= "- How it fits into the system\n";
    $markdown .= "-->\n\n";

    $markdown .= "## Connection & Table\n\n";
    if ($connection === '<!-- AI: Determine connection (tenant or central) -->') {
        $markdown .= "<!-- AI: Determine connection --> · `$tableName`\n\n";
    } else {
        $markdown .= ucfirst($connection) . " · `$tableName`\n\n";
    }

    $markdown .= "## Schema\n\n";
    $markdown .= "<!-- Render from schema/{connection}.json when available -->\n";
    $markdown .= "<!-- Table: $tableName -->\n\n";
    $markdown .= "| Column | Type | Nullable | Default | Description |\n";
    $markdown .= "|--------|------|----------|---------|-------------|\n";
    $markdown .= "| <!-- Extract from snapshot --> | | | | |\n\n";

    $markdown .= "## Properties / Casts\n\n";

    $hasParent = isset($modelData['_parentData']);

    // Defined in this model
    $hasOwnProps = !empty($modelData['moneyAttributes']) || !empty($modelData['casts']) ||
                   !empty($modelData['searchableColumns']) || !empty($modelData['fillable']) ||
                   !empty($modelData['guarded']) || !empty($modelData['appends']) || !empty($modelData['hidden']);

    if ($hasOwnProps && $hasParent) {
        $markdown .= "### Defined in {$modelData['className']}\n\n";
    }

    if (!empty($modelData['moneyAttributes'])) {
        $markdown .= "**Money Attributes:**\n";
        $markdown .= "- `moneyAttributes` = `['" . implode("', '", $modelData['moneyAttributes']) . "']`\n\n";
    }

    if (!empty($modelData['casts'])) {
        $markdown .= "**Casts:**\n";
        foreach ($modelData['casts'] as $field => $type) {
            $markdown .= "- `$field` → `$type`\n";
        }
        $markdown .= "\n";
    }

    if (!empty($modelData['searchableColumns'])) {
        $markdown .= "**Searchable:**\n";
        $markdown .= "- `searchableColumns` = `['" . implode("', '", $modelData['searchableColumns']) . "']`\n\n";
    }

    if (!empty($modelData['fillable'])) {
        $markdown .= "**Fillable:**\n";
        $markdown .= "- `['" . implode("', '", $modelData['fillable']) . "']`\n\n";
    }

    if (isset($modelData['guarded'])) {
        $guardedList = empty($modelData['guarded']) ? '[]' : "['" . implode("', '", $modelData['guarded']) . "']";
        $markdown .= "**Guarded:**\n";
        $markdown .= "- `$guardedList`";
        if (empty($modelData['guarded'])) {
            $markdown .= " — All fields are mass-assignable";
        }
        $markdown .= "\n\n";
    }

    if (!empty($modelData['appends'])) {
        $markdown .= "**Appended Attributes:**\n";
        $markdown .= "- `['" . implode("', '", $modelData['appends']) . "']`\n\n";
    }

    if (!empty($modelData['hidden'])) {
        $markdown .= "**Hidden Attributes:**\n";
        $markdown .= "- `['" . implode("', '", $modelData['hidden']) . "']`\n\n";
    }

    // Inherited properties
    if ($hasParent) {
        $parentData = $modelData['_parentData'];
        $hasParentProps = !empty($parentData['moneyAttributes']) || !empty($parentData['casts']) ||
                          !empty($parentData['searchableColumns']) || !empty($parentData['fillable']) ||
                          !empty($parentData['guarded']) || !empty($parentData['appends']) || !empty($parentData['hidden']);

        if ($hasParentProps) {
            $markdown .= "### Inherited from {$parentData['className']}\n\n";

            if (!empty($parentData['moneyAttributes'])) {
                $markdown .= "**Money Attributes:**\n";
                $markdown .= "- `moneyAttributes` = `['" . implode("', '", $parentData['moneyAttributes']) . "']`\n\n";
            }

            if (!empty($parentData['casts'])) {
                $markdown .= "**Casts:**\n";
                foreach ($parentData['casts'] as $field => $type) {
                    $markdown .= "- `$field` → `$type`\n";
                }
                $markdown .= "\n";
            }

            if (!empty($parentData['searchableColumns'])) {
                $markdown .= "**Searchable:**\n";
                $markdown .= "- `searchableColumns` = `['" . implode("', '", $parentData['searchableColumns']) . "']`\n\n";
            }

            if (isset($parentData['guarded'])) {
                $guardedList = empty($parentData['guarded']) ? '[]' : "['" . implode("', '", $parentData['guarded']) . "']";
                $markdown .= "**Guarded:**\n";
                $markdown .= "- `$guardedList`";
                if (empty($parentData['guarded'])) {
                    $markdown .= " — All fields are mass-assignable";
                }
                $markdown .= "\n\n";
            }
        }
    }

    $markdown .= "## Relationships\n\n";

    // Own relationships
    if (!empty($modelData['relationshipMethods']) && $hasParent) {
        $markdown .= "### Defined in {$modelData['className']}\n\n";
    }

    if (!empty($modelData['relationshipMethods'])) {
        foreach ($modelData['relationshipMethods'] as $method) {
            $relType = $method['returnType'] ?? 'relationship';
            $markdown .= "- `{$method['name']}()` — $relType";
            $markdown .= " <!-- AI: Add description and link to related model -->\n";
        }
        $markdown .= "\n";
    }

    // Inherited relationships
    if ($hasParent && !empty($modelData['_parentData']['relationshipMethods'])) {
        $markdown .= "### Inherited from {$modelData['_parentData']['className']}\n\n";
        foreach ($modelData['_parentData']['relationshipMethods'] as $method) {
            $relType = $method['returnType'] ?? 'relationship';
            $markdown .= "- `{$method['name']}()` — $relType";
            $markdown .= " <!-- AI: Add description and link to related model -->\n";
        }
        $markdown .= "\n";
    }

    if (empty($modelData['relationshipMethods']) && (!$hasParent || empty($modelData['_parentData']['relationshipMethods']))) {
        $markdown .= "<!-- None defined -->\n\n";
    }

    $markdown .= "## Key Methods\n\n";

    // Own methods
    if (!empty($modelData['methods']) && $hasParent) {
        $markdown .= "### Defined in {$modelData['className']}\n\n";
    }

    if (!empty($modelData['methods'])) {
        foreach ($modelData['methods'] as $method) {
            $signature = "{$method['name']}({$method['params']})";
            if ($method['returnType']) {
                $signature .= ": {$method['returnType']}";
            }
            $markdown .= "- `$signature`";
            $markdown .= " <!-- AI: Add method description -->\n";
        }
        $markdown .= "\n";
    }

    // Inherited methods
    if ($hasParent && !empty($modelData['_parentData']['methods'])) {
        $markdown .= "### Inherited from {$modelData['_parentData']['className']}\n\n";
        foreach ($modelData['_parentData']['methods'] as $method) {
            $signature = "{$method['name']}({$method['params']})";
            if ($method['returnType']) {
                $signature .= ": {$method['returnType']}";
            }
            $markdown .= "- `$signature`";
            $markdown .= " <!-- AI: Add method description -->\n";
        }
        $markdown .= "\n";
    }

    if (empty($modelData['methods']) && (!$hasParent || empty($modelData['_parentData']['methods']))) {
        $markdown .= "<!-- None defined -->\n\n";
    }

    $markdown .= "## Scopes / Events / Observers\n\n";

    $hasOwnScopes = !empty($modelData['globalScopes']) || !empty($modelData['scopes']);
    $hasParentScopes = $hasParent && (!empty($modelData['_parentData']['globalScopes']) || !empty($modelData['_parentData']['scopes']));

    if (!empty($modelData['globalScopes'])) {
        $markdown .= "**Global Scopes:**\n";
        foreach ($modelData['globalScopes'] as $scope) {
            $args = $scope['args'] ? "'{$scope['args']}'" : '';
            $markdown .= "- `{$scope['class']}($args)`";
            $markdown .= " <!-- AI: Add scope description -->\n";
        }
        $markdown .= "\n";
    }

    if (!empty($modelData['scopes'])) {
        $markdown .= "**Query Scopes:**\n";
        foreach ($modelData['scopes'] as $scope) {
            $params = $scope['params'] ? ", {$scope['params']}" : '';
            $markdown .= "- `{$scope['name']}(\$query$params)`";
            $markdown .= " <!-- AI: Add scope description -->\n";
        }
        $markdown .= "\n";
    }

    // Inherited scopes
    if ($hasParent) {
        $parentData = $modelData['_parentData'];

        if (!empty($parentData['scopes'])) {
            $markdown .= "**Query Scopes (Inherited from {$parentData['className']}):**\n";
            foreach ($parentData['scopes'] as $scope) {
                $params = $scope['params'] ? ", {$scope['params']}" : '';
                $markdown .= "- `{$scope['name']}(\$query$params)`";
                $markdown .= " <!-- AI: Add scope description -->\n";
            }
            $markdown .= "\n";
        }
    }

    if (!$hasOwnScopes && !$hasParentScopes) {
        $markdown .= "<!-- AI: Document events and observers -->\n\n";
    } else {
        $markdown .= "<!-- AI: Document model events and observers -->\n\n";
    }

    $markdown .= "## Common Usage\n\n";
    $markdown .= "<!-- AI: Write 3-5 code examples showing:\n";
    $markdown .= "- Creating instances\n";
    $markdown .= "- Common queries\n";
    $markdown .= "- Relationship usage\n";
    $markdown .= "- Key method calls\n";
    $markdown .= "-->\n\n";
    $markdown .= "```php\n";
    $markdown .= "// Examples here\n";
    $markdown .= "```\n\n";

    $markdown .= "<!-- human:begin -->\n";
    $markdown .= "## Business Logic Notes\n\n";
    $markdown .= "<!-- human:end -->\n";

    return $markdown;
}

// Main execution
fwrite(STDERR, "Extracting model skeleton from: $modelPath\n");

// Parse model with inheritance
$modelData = parseModelWithInheritance($everspotPath, $canonicalBranch, $modelPath);

if ($modelData === null) {
    fwrite(STDERR, "ERROR: Could not fetch model from git: origin/$canonicalBranch:$modelPath\n");
    exit(1);
}

if (!$modelData['className']) {
    fwrite(STDERR, "ERROR: Could not extract class name from model source\n");
    exit(1);
}

fwrite(STDERR, "Found model: {$modelData['className']}\n");
fwrite(STDERR, "Extends: " . ($modelData['extends'] ?? 'none') . "\n");
fwrite(STDERR, "Traits: " . count($modelData['traits']) . "\n");
fwrite(STDERR, "Relationships: " . count($modelData['relationshipMethods']) . "\n");
fwrite(STDERR, "Methods: " . count($modelData['methods']) . "\n");
fwrite(STDERR, "Scopes: " . count($modelData['scopes']) . "\n");

// Derive source paths
$sourcePaths = deriveSourcePaths($everspotPath, $canonicalBranch, $modelPath, $modelData);
fwrite(STDERR, "Source paths: " . count($sourcePaths) . "\n");

// Extract related models
$relatedModels = extractRelatedModels($modelData);

// Get current commit
$commitHash = getCurrentCommit($everspotPath, $canonicalBranch);
fwrite(STDERR, "Built at: $commitHash\n");

// Generate markdown
$markdown = generateMarkdownSkeleton($modelPath, $modelData, $sourcePaths, $relatedModels, $commitHash);

// Output to stdout
echo $markdown;

fwrite(STDERR, "\nSkeleton generated successfully!\n");
fwrite(STDERR, "Mechanical sections: frontmatter, properties, relationships (signatures), methods (signatures), scopes\n");
fwrite(STDERR, "AI sections marked: overview, connection (if not explicit), relationship descriptions, method descriptions, usage examples, tags, completeness\n");
