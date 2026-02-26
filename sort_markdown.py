"""
Check if a Click command belongs to a Group. If it does, create a directory
for the group and place the commands inside it.

Do not move the top level Group commands, only the subcommands. For example,
if we have a group "docker" with subcommands "run" and "build", create a
directory "wandb-docker" and move "wandb-docker-run.md" and
"wandb-docker-build.md" into "wandb-docker". The "wandb-docker.md" file 
should remain in the top level output directory.

Python commands that are Click groups have "is_click_group": true in the
output of get_public_commands_with_source(). We can use this to determine
which commands are groups and create directories for them. 
"""

import argparse
import json
import os
from get_public_commands import get_public_commands_with_source

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get list of public CLI commands for documentation generation."
    )
    parser.add_argument(
        "--source-info",
        type=str,
        default="public_commands.json",
        help="Path to output JSON file with public command information.",
    )
    parser.add_argument(
        "--output-markdown",
        type=str,
        default="output",
        help="Path to output directory for markdown files.",
    )
    args = parser.parse_args()

    print(f"Sorting markdown files in directory: {args.output_markdown}\nUsing source info from: {args.source_info}")

    # Get public commands with source information
    public_commands = get_public_commands_with_source()
    with open(args.source_info, "w") as f:
        json.dump(public_commands, f, indent=4)

    # Get list of click groups from the commands
    click_group = []
    for cmd in public_commands:
        if cmd['is_click_group']:
            click_group.append({'name': cmd['name'], 'func_name': cmd['func_name']})
    
    # Make a directory for each click group
    for group in click_group:
        group_dir = os.path.join(args.output_markdown, "wandb-" + group['name'])
        if not os.path.exists(group_dir):
            os.makedirs(group_dir)

    # Read in markdown files in the output markdown directory
    # If the file names contains the name of a click group, move the file to
    # the directory for that group
    for filename in os.listdir(args.output_markdown):
        if not filename.endswith(".md"):
            continue
        for group in click_group:
            if group['name'] in filename and filename != f"{group['name']}.md":
                old_path = os.path.join(args.output_markdown, filename)

                new_path = os.path.join(args.output_markdown, "wandb-" + group['name'], filename)
                os.rename(old_path, new_path)