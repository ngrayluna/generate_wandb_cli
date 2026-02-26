"""
Check if a Click command belongs to a Group. If it does, create a directory
for the group and place the commands inside it. If not, place the command in
the root directory. This helps organize the documentation by grouping related
commands together.

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

    click_group = []
    for cmd in public_commands:
        if cmd['is_click_group']:
            click_group.append({'name': cmd['name'], 'func_name': cmd['func_name']})
    
    # Make a directory for each click group
    for group in click_group:
        group_dir = os.path.join(args.output_markdown, "wandb-" + group['name'])
        #print(f"Creating directory for group {group['name']}: {group_dir}")
        if not os.path.exists(group_dir):
            os.makedirs(group_dir)

    # Read in markdown files in the output markdown directory
    # If the file names contains the name of a click group, move the file to
    # the directory for that group
    for filename in os.listdir(args.output_markdown):
        if not filename.endswith(".md"):
            continue
        #print(f"Checking file: {filename}")
        for group in click_group:
            if group['name'] in filename:
                old_path = os.path.join(args.output_markdown, filename)
                #print(f"Moving {old_path} to {group['name']} directory")

                new_path = os.path.join(args.output_markdown, "wandb-" + group['name'], filename)
                # print(f"New path: {new_path}")
                os.rename(old_path, new_path)