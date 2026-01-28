#!/bin/bash
# Generate markdown reference documentation for wandb CLI commands using md-click

OUTPUT_JSON="source_info.json"
OUTPUT_DIR="output"

# Activate the correct Python environment
source $(pyenv root)/versions/cli_docs/bin/activate

# Create docs directory if it doesn't exist
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
python format_markdown.py --markdown_directory "$OUTPUT_DIR" --source-info "$OUTPUT_JSON"