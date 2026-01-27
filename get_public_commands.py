#!/usr/bin/env python
"""Get list of public (non-hidden) CLI commands for documentation generation."""

import click
from wandb.cli.cli import cli


def get_public_commands():
    """Return list of public command function names (excluding hidden commands)."""
    commands = getattr(cli, 'commands', {})
    public_commands = []

    for name, cmd in commands.items():
        if not getattr(cmd, 'hidden', False):
            # Use the callback function name (underscores) instead of CLI name (hyphens)
            func_name = cmd.callback.__name__ if cmd.callback else name
            public_commands.append(func_name)

    return public_commands


if __name__ == "__main__":
    for cmd in get_public_commands():
        print(cmd)
