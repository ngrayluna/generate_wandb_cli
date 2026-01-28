#!/bin/bash
# Generate markdown reference documentation for wandb CLI commands.
#
# This script:
#   1. Clones/updates the wandb/wandb repo to ./wandb-repo/
#   2. Checks out the specified release tag
#   3. Generates markdown docs using md-click from the checked-out source
#   4. Formats the docs with tables and GitHub source links
#
# Output is written to ./output/ directory.
#
# Usage: ./generate_cli.sh <release_tag>
# Example: ./generate_cli.sh v0.18.3

set -e  # Exit on error

# Check for required argument
if [ -z "$1" ]; then
    echo "Usage: $0 <release_tag>"
    echo "Example: $0 v0.18.3"
    exit 1
fi

RELEASE_TAG="$1"
REPO_URL="https://github.com/wandb/wandb.git"
REPO_DIR="wandb-repo"
OUTPUT_JSON="source_info.json"
OUTPUT_DIR="output"

# Activate the correct Python environment
source $(pyenv root)/versions/cli_docs/bin/activate

# Clone or update the wandb repository
if [ -d "$REPO_DIR" ]; then
    echo "Updating existing wandb repository..."
    git -C "$REPO_DIR" fetch --tags
else
    echo "Cloning wandb repository..."
    git clone --depth 1 --no-checkout "$REPO_URL" "$REPO_DIR"
    git -C "$REPO_DIR" fetch --tags --depth 1
fi

# Checkout the specified release tag
echo "Checking out $RELEASE_TAG..."
git -C "$REPO_DIR" checkout "$RELEASE_TAG" --force

# Set PYTHONPATH to use the checked-out repo
export PYTHONPATH="$PWD/$REPO_DIR:$PYTHONPATH"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Generate source info JSON (for source links in docs)
python get_public_commands.py --output-json "$OUTPUT_JSON"

# Extract command names from JSON
PUBLIC_COMMANDS=$(python -c "import json; print(' '.join(cmd['func_name'] for cmd in json.load(open('$OUTPUT_JSON'))))")

# Generate markdown documentation for each public command
for cmd in $PUBLIC_COMMANDS; do
    echo "Generating docs for: $cmd"
    mdclick dumps --baseModule wandb.cli.cli --baseCommand "$cmd" --docsPath "$OUTPUT_DIR"
done

# Format the generated markdown files with source links
python format_markdown.py --markdown_directory "$OUTPUT_DIR" --source-info "$OUTPUT_JSON" --release-tag "$RELEASE_TAG"

echo "Documentation generated for wandb $RELEASE_TAG in $OUTPUT_DIR/"