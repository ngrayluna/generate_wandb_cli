"""
Utils for inspecting Click commands and options to extract structured metadata for documentation generation.

This module provides functions to classify Click options into documentation-friendly types and to inspect Click commands to extract option metadata. The extracted metadata can be used to enhance the generated documentation with accurate information about command-line options, their types, defaults, and flags.

This is a patch to add structured metadata extraction for Click options, which is not natively provided by md-click-2. By classifying options into categories like boolean flags, dual flags, and value-based options, we can generate more informative documentation that accurately reflects the behavior of the CLI.
"""
import argparse
import click
import json
from typing import Dict, List
from wandb.cli.cli import cli
from format_markdown import load_source_info


def classify_option(param: click.Option) -> str:
    """
    Classify a Click option into a documentation-friendly type.
    
    Returns one of:
        - "boolean-flag"
        - "boolean-dual-flag"
        - "boolean-value"
        - "other"
    """
    if param.is_flag:
        if param.secondary_opts:
            return "boolean-dual-flag"
        return "boolean-flag"

    if isinstance(param.type, click.types.BoolParamType):
        return "boolean-value"

    return "other"


def inspect_command(command: click.Command) -> List[Dict]:
    """
    Inspect a Click command and return structured option metadata.
    """
    results = []

    for param in command.params:
        if isinstance(param, click.Option):
            option_info = {
                "name": param.name,
                "opts": param.opts,
                "secondary_opts": param.secondary_opts,
                "default": param.default,
                "required": param.required,
                "classification": classify_option(param),
                "type": type(param.type).__name__,
            }
            results.append(option_info)

    return results

def main(args):

    # Get the commands from the CLI group
    commands = getattr(cli, 'commands', {})

    # Read in source_info JSON and print out the options for each command
    source_info = load_source_info(args.source_info)

    # Update the source_info withi this new info
    for name, cmd in commands.items():
        if name in source_info:
            cmd_metadata = inspect_command(cmd)
            source_info[name]['options'] = cmd_metadata
            print(f"Updated source_info for command: {name}")
        else:
            print(f"Command {name} not found in source_info, skipping.")

    # Save the updated source_info back to the JSON file
    with open(args.source_info, 'w', encoding='utf-8') as f:
        json.dump(source_info, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect Click commands and extract option metadata")
    parser.add_argument("--source-info", type=str, required=True, help="Path to source_info JSON file")
    args = parser.parse_args()