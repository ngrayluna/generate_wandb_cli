#!/bin/bash
# Generate markdown reference documentation for wandb CLI commands using md-click

# Activate the correct Python environment
source $(pyenv root)/versions/cli_docs/bin/activate

# Create docs directory if it doesn't exist
mkdir -p docs

# Get list of public (non-hidden) commands
PUBLIC_COMMANDS=$(python get_public_commands.py)

# Generate markdown documentation for each public command
for cmd in $PUBLIC_COMMANDS; do
    echo "Generating docs for: $cmd"
    mdclick dumps --baseModule wandb.cli.cli --baseCommand "$cmd" --docsPath docs
done
