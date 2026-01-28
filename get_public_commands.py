#!/usr/bin/env python
"""Get list of public (non-hidden) CLI commands for documentation generation."""
import argparse
import inspect
import json
from wandb.cli.cli import cli


def get_command_source_info(cmd):
    """Get the source file and line number for a Click command.

    Args:
        cmd: A Click command object

    Returns:
        Tuple of (source_file, line_number) or (None, None) if not found
    """
    if not cmd.callback:
        return None, None

    try:
        # Unwrap decorated functions to get the original
        unwrapped = inspect.unwrap(cmd.callback)
        source_file = inspect.getfile(unwrapped)
        _, start_line = inspect.getsourcelines(unwrapped)
        return source_file, start_line
    except Exception:
        return None, None


def get_public_commands_with_source():
    """Return list of public commands with their source file and line number.

    Returns:
        List of dicts with keys: name, func_name, source_file, line_number
    """
    commands = getattr(cli, 'commands', {})
    result = []

    for name, cmd in commands.items():
        if not getattr(cmd, 'hidden', False):
            func_name = cmd.callback.__name__ if cmd.callback else name
            source_file, line_number = get_command_source_info(cmd)

            result.append({
                'name': name,              # CLI name (e.g., 'docker-run')
                'func_name': func_name,    # Python function name (e.g., 'docker_run')
                'source_file': source_file,
                'line_number': line_number
            })

    return result


def get_public_commands():
    """Return list of public command function names (excluding hidden commands)."""
    return [cmd['func_name'] for cmd in get_public_commands_with_source()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get list of public CLI commands for documentation generation."
    )
    parser.add_argument(
        "--output-json",
        metavar="FILE",
        help="Write command info with source locations to JSON file"
    )
    parser.add_argument(
        "--with-source",
        action="store_true",
        help="Print commands with source file and line number (tab-separated)"
    )
    args = parser.parse_args()

    if args.output_json:
        # Write to JSON file
        commands = get_public_commands_with_source()
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(commands, f, indent=2)
        print(f"Wrote {len(commands)} commands to {args.output_json}")

    elif args.with_source:
        # Print with source info (tab-separated)
        for cmd in get_public_commands_with_source():
            print(f"{cmd['func_name']}\t{cmd['line_number']}\t{cmd['source_file']}")

    else:
        # Default: just print function names
        for cmd in get_public_commands():
            print(cmd)
