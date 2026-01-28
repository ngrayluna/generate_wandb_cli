#!/bin/bash
# Generate markdown reference documentation for wandb CLI commands using md-click

OUTPUT_DIR="output"

# Activate the correct Python environment
source $(pyenv root)/versions/cli_docs/bin/activate

# Create docs directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Get list of public (non-hidden) commands
PUBLIC_COMMANDS=$(python get_public_commands.py)

# Generate markdown documentation for each public command
for cmd in $PUBLIC_COMMANDS; do
    echo "Generating docs for: $cmd"
    mdclick dumps --baseModule wandb.cli.cli --baseCommand "$cmd" --docsPath "$OUTPUT_DIR"
done

# Format the generated markdown files
python format_markdown.py --markdown_directory "$OUTPUT_DIR"

# Mintlify the formatted markdown files
#python rename_files.py --markdown_directory "$OUTPUT_DIR"