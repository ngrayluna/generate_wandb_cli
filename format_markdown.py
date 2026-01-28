"""
Custom formatting for markdown files and Mintlify integration.

Converts md-click bullet point options/arguments to markdown tables.
"""
import argparse
import glob
import json
import os
import re
from typing import Optional


def load_source_info(filepath: str) -> dict:
    """Load source info from JSON file and return as a mapping.

    Args:
        filepath: Path to JSON file with command source info

    Returns:
        Dict mapping func_name -> {name, func_name, source_file, line_number}
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        commands = json.load(f)
    return {cmd['func_name']: cmd for cmd in commands}

def add_source_link(content: str, source_file: str, line_number: int) -> str:
    """Add a source code link before the ## Usage section.

    Args:
        content: Markdown content
        source_file: Path to source file
        line_number: Line number in source file

    Returns:
        Content with source link inserted before ## Usage
    """
    # Extract just the filename from the full path (e.g., "wandb/cli/cli.py")
    if 'site-packages/' in source_file:
        short_path = source_file.split('site-packages/')[-1]
    else:
        short_path = source_file

    # Create the source link (using GitHub URL format)
    # This assumes wandb/wandb repo structure
    github_base = "https://github.com/wandb/wandb/blob/main"
    github_url = f"{github_base}/{short_path}#L{line_number}"
    source_link = f"\n[View source on GitHub]({github_url})\n\n"

    # Insert before ## Usage section
    usage_match = re.search(r'^## Usage', content, re.MULTILINE)
    if usage_match:
        return content[:usage_match.start()] + source_link + content[usage_match.start():]
    else:
        # If no Usage section, append at the end
        return content + source_link


def add_frontmatter(filename: str) -> str:
    """Add Mintlify frontmatter to a markdown file.

    Args:
        filename: Name of the markdown file
        content: Full markdown file content

    Returns:
        Content with frontmatter added
    """
    title = os.path.splitext(os.path.basename(filename))[0].replace('_', ' ')
    return f"---\ntitle: wandb {title}\n---\n\n"

def remove_h1_title(content: str) -> str:
    """Remove the first H1 title from the markdown content.

    Matches '# title' at the start of a line and removes it along with the newline.
    """
    return re.sub(r'^# .+\n+', '', content, count=1, flags=re.MULTILINE)


def format_usage_code_block(content: str) -> str:
    """Format the code block after ## Usage section.

    Changes:
        - Code block language from ``` to ```shell
        - "Usage: <command>" to "wandb <command>"

    Before:
        ## Usage

        ```
        Usage: docker [OPTIONS] [DOCKER_RUN_ARGS]... [DOCKER_IMAGE]
        ```

    After:
        ## Usage

        ```shell
        wandb docker [OPTIONS] [DOCKER_RUN_ARGS]... [DOCKER_IMAGE]
        ```
    """
    # Pattern to match: ## Usage followed by a code block containing "Usage: ..."
    # Captures: (## Usage\n\n)(```)(code content)(```)
    pattern = r'(## Usage\n\n)(```)\n(Usage: )(.+?)\n(```)'

    def replace_usage(match):
        header = match.group(1)       # "## Usage\n\n"
        code_start = '```shell'       # Change to ```shell
        command = match.group(4)      # The command after "Usage: "
        code_end = match.group(5)     # "```"

        return f'{header}{code_start}\nwandb {command}\n{code_end}'

    return re.sub(pattern, replace_usage, content, flags=re.DOTALL)


def format_flags(usage_str: str) -> str:
    """Convert usage string to formatted flags (short flag first, then long flag).

    Example: '--project\n-p' -> '-p, --project'
    """
    # Split by whitespace or newlines
    flags = re.split(r'[\s\n]+', usage_str.strip())

    short_flags = [f for f in flags if f.startswith('-') and not f.startswith('--')]
    long_flags = [f for f in flags if f.startswith('--')]

    # Combine: short flags first, then long flags
    all_flags = short_flags + long_flags
    return ', '.join(all_flags)


def parse_option_block(block: str) -> Optional[dict]:
    """Parse a single option block and return its components.

    Input format:
        * `option_name`:
            * Type: STRING
            * Default: `None`
            * Usage: `--option
        -o`
            Description text here.

    Returns:
        Dict with keys: name, type, default, flags, description.
        Returns None if the block cannot be parsed.
    """
    # Extract option name
    name_match = re.search(r'^\* `([^`]+)`:', block, re.MULTILINE)
    if not name_match:
        return None
    name = name_match.group(1)

    # Extract type
    type_match = re.search(r'\* Type: (.+)', block)
    opt_type = type_match.group(1).strip() if type_match else ''

    # Extract default (handle backticks)
    default_match = re.search(r'\* Default: `([^`]*)`', block)
    default = default_match.group(1) if default_match else ''

    # Extract usage/flags (may span multiple lines, ends with backtick)
    usage_match = re.search(r'\* Usage: `([^`]+)`', block, re.DOTALL)
    usage = usage_match.group(1).strip() if usage_match else ''
    flags = format_flags(usage) if usage.startswith('-') else usage

    # Extract description: text after the last bullet point line
    # Find where the Usage line ends (after the closing backtick)
    usage_end = block.rfind('`')
    if usage_end != -1:
        remaining = block[usage_end + 1:].strip()
        # Remove any leading bullet points that might be left
        description = re.sub(r'^\s*\*.*$', '', remaining, flags=re.MULTILINE).strip()
    else:
        description = ''

    return {
        'name': name,
        'type': opt_type,
        'default': default,
        'flags': flags,
        'description': description or 'No description available.'
    }


def convert_section_to_tables(section_content: str, section_type: str = 'options') -> str:
    """Convert a section's bullet points to markdown tables.

    Args:
        section_content: The content after the section header
        section_type: 'options' or 'arguments'

    Returns:
        Formatted markdown string with tables
    """
    # Split into individual option/argument blocks
    # Each block starts with "* `name`:"
    blocks = re.split(r'(?=^\* `[^`]+`:)', section_content, flags=re.MULTILINE)
    blocks = [b.strip() for b in blocks if b.strip()]

    tables = []
    for block in blocks:
        opt = parse_option_block(block)
        if opt:
            if section_type == 'options':
                # Options have flags
                table = f"""### `{opt['name']}`

| Flag | Default | Type | Description |
|------|---------|------|-------------|
| `{opt['flags']}` | {opt['default']} | {opt['type']} | {opt['description']} |
"""
            else:
                # Arguments don't have flags, just the name
                table = f"""### `{opt['name']}`

| Name | Default | Type | Description |
|------|---------|------|-------------|
| `{opt['name']}` | {opt['default']} | {opt['type']} | {opt['description']} |
"""
            tables.append(table)

    return '\n'.join(tables)


def _convert_section(content: str, section_name: str, section_type: str) -> str:
    """Convert a markdown section's bullet points to tables.

    Args:
        content: Full markdown file content
        section_name: Section header name (e.g., 'Options', 'Arguments')
        section_type: Type for table formatting ('options' or 'arguments')

    Returns:
        Modified content with section converted to tables
    """
    pattern = rf'(## {section_name}\n)(.*?)(?=\n## |\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return content

    header = match.group(1)
    section_content = match.group(2)

    new_section_content = convert_section_to_tables(section_content, section_type)

    new_section = header + '\n' + new_section_content
    return content[:match.start()] + new_section + content[match.end():]


def convert_options_to_tables(content: str) -> str:
    """Convert the ## Options section from bullet points to markdown tables."""
    return _convert_section(content, 'Options', 'options')


def convert_arguments_to_tables(content: str) -> str:
    """Convert the ## Arguments section from bullet points to markdown tables."""
    return _convert_section(content, 'Arguments', 'arguments')


def remove_empty_arguments_section(content: str) -> str:
    """Remove the ## Arguments section if it's empty.

    Args:
        content: Full markdown file content

    Returns:
        Modified content with empty Arguments section removed
    """
    # Match ## Arguments followed by only whitespace until next ## or end of file
    pattern = r'## Arguments\n\s*(?=\n## |\Z)'
    return re.sub(pattern, '', content)


def format_markdown_file(
    content: str,
    source_file: Optional[str] = None,
    line_number: Optional[int] = None
) -> str:
    """Apply all formatting transformations to markdown content.

    Args:
        content: Full markdown file content
        source_file: Optional path to source file for GitHub link
        line_number: Optional line number in source file

    Returns:
        Modified content with all transformations applied
    """
    content = format_usage_code_block(content)
    content = convert_options_to_tables(content)
    content = convert_arguments_to_tables(content)
    content = remove_empty_arguments_section(content)
    content = remove_h1_title(content)

    # Add source link if source info is provided
    if source_file and line_number:
        content = add_source_link(content, source_file, line_number)

    return content


def main(args):
    # Find all markdown files in the specified directory
    pattern = os.path.join(os.getcwd(), args.markdown_directory, "*.md")
    files = glob.glob(pattern)

    # Check if any files found
    if not files:
        print(f"No markdown files found in {args.markdown_directory}")
        return

    # Load source JSON info if provided
    source_info = {}
    if args.source_info:
        try:
            source_info = load_source_info(args.source_info)
            print(f"Loaded source info for {len(source_info)} commands")
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load source info: {e}")

    # Process each markdown file
    for filename in files:
        print(f"Processing... {filename}")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            print(f"Error reading {filename}: {e}")
            continue

        # Get source info for this command if available
        basename = os.path.splitext(os.path.basename(filename))[0]
        func_name = basename.replace('-', '_')  # Handle "docker-run" -> "docker_run"

        # Default to None if not found
        source_file = None
        line_number = None

        # Look up source info
        if func_name in source_info:
            cmd_info = source_info[func_name]
            source_file = cmd_info.get('source_file')
            line_number = cmd_info.get('line_number')

        # Apply all formatting transformations (including source link if available)
        formatted = format_markdown_file(content, source_file, line_number)

        # Write back to file with frontmatter
        print(f"Writing formatted content to {filename}")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(add_frontmatter(filename))
            f.write(formatted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-process md-click-2 markdown.")
    parser.add_argument(
        "--markdown_directory",
        default="docs",
        help="Directory containing markdown files to process"
    )
    parser.add_argument(
        "--source-info",
        metavar="FILE",
        help="JSON file with command source info (from get_public_commands.py --output-json)"
    )
    main(parser.parse_args())