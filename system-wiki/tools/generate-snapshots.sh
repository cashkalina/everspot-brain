#!/usr/bin/env bash

#
# Schema Snapshot Generation Script
#
# Automates the extraction of central and tenant schema snapshots from Everspot.
# Run this script whenever migrations have been applied to regenerate snapshots.
#
# This script now uses the standalone generate-schema-snapshots.php which boots
# Everspot's framework in-process WITHOUT writing any files to Everspot.
#
# Usage:
#   ./tools/generate-snapshots.sh [tenant-id]
#
# If tenant-id is not provided, will attempt to use first available tenant.
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKI_ROOT="$(dirname "$SCRIPT_DIR")"
EVERSPOT_PATH="${EVERSPOT_PATH:-}"

# Load wiki config if exists
if [ -f "$WIKI_ROOT/wiki.config.json" ]; then
    if command -v jq &> /dev/null; then
        EVERSPOT_PATH=$(jq -r '.everspot_repo_path // empty' "$WIKI_ROOT/wiki.config.json")
    fi
fi

# Validate Everspot path
if [ -z "$EVERSPOT_PATH" ]; then
    echo "ERROR: Everspot repository path not configured"
    echo ""
    echo "Set EVERSPOT_PATH environment variable or configure wiki.config.json"
    echo "Example: export EVERSPOT_PATH=/path/to/everspot"
    exit 1
fi

if [ ! -d "$EVERSPOT_PATH" ]; then
    echo "ERROR: Everspot repository not found at: $EVERSPOT_PATH"
    exit 1
fi

if [ ! -f "$EVERSPOT_PATH/artisan" ]; then
    echo "ERROR: Not a valid Laravel project (no artisan): $EVERSPOT_PATH"
    exit 1
fi

echo "==> Using Everspot repository: $EVERSPOT_PATH"
echo "==> Wiki repository: $WIKI_ROOT"
echo ""

# Determine tenant ID
TENANT_ID="${1:-}"
if [ -z "$TENANT_ID" ]; then
    echo "==> Finding first available tenant..."
    cd "$EVERSPOT_PATH"

    # Attempt to get first tenant ID
    TENANT_MODEL_CLASS=$(php artisan tinker --execute='echo config("tenancy.tenant_model");' 2>/dev/null || echo "")

    if [ -n "$TENANT_MODEL_CLASS" ]; then
        TENANT_ID=$(php artisan tinker --execute="echo ${TENANT_MODEL_CLASS}::first()->id ?? '';" 2>/dev/null || echo "")
    fi

    if [ -z "$TENANT_ID" ]; then
        echo ""
        echo "ERROR: No tenant ID provided and could not find a tenant automatically"
        echo ""
        echo "Usage: $0 <tenant-id>"
        echo ""
        echo "Or create a tenant first:"
        echo "  cd $EVERSPOT_PATH"
        echo "  php artisan tenants:create"
        exit 1
    fi

    echo "    Using tenant: $TENANT_ID"
    echo ""
fi

# Generate snapshots using standalone script
php "$SCRIPT_DIR/generate-schema-snapshots.php" \
    --central "$WIKI_ROOT/schema/central.json" \
    --tenant "$WIKI_ROOT/schema/tenant.json" \
    --tenant-id "$TENANT_ID"

# Verify snapshots
echo "==> Verifying snapshots..."

if command -v jq &> /dev/null; then
    echo "    Validating JSON format..."
    jq . "$WIKI_ROOT/schema/central.json" > /dev/null && echo "    ✓ central.json valid"
    jq . "$WIKI_ROOT/schema/tenant.json" > /dev/null && echo "    ✓ tenant.json valid"

    echo ""
    echo "    Table counts:"
    CENTRAL_COUNT=$(jq '.meta.table_count' "$WIKI_ROOT/schema/central.json")
    TENANT_COUNT=$(jq '.meta.table_count' "$WIKI_ROOT/schema/tenant.json")
    echo "    - Central: $CENTRAL_COUNT tables"
    echo "    - Tenant:  $TENANT_COUNT tables"

    # Check for errors
    if jq -e '.error' "$WIKI_ROOT/schema/central.json" > /dev/null 2>&1; then
        echo "    ⚠ Warning: central.json contains error markers"
    fi
    if jq -e '.error' "$WIKI_ROOT/schema/tenant.json" > /dev/null 2>&1; then
        echo "    ⚠ Warning: tenant.json contains error markers"
    fi
else
    echo "    (jq not available - skipping validation)"
fi

echo ""
echo "==> Snapshots generated successfully!"
echo ""
echo "Next steps:"
echo "  1. Review the generated snapshots"
echo "  2. Commit to wiki repository if changes detected"
echo "  3. Run wiki sync to update affected model documents"
echo ""
