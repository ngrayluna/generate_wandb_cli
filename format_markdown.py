"""
Custom formatting for markdown files and Mintlify integration.

Converts md-click bullet point options/arguments to markdown tables.
"""
import argparse
import glob
import os
import re
from typing import Optional

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


def format_markdown_file(content: str) -> str:
    """Apply all formatting transformations to markdown content.

    Args:
        content: Full markdown file content

    Returns:
        Modified content with all transformations applied
    """
    content = format_usage_code_block(content)
    content = convert_options_to_tables(content)
    content = convert_arguments_to_tables(content)
    content = remove_empty_arguments_section(content)
    content = remove_h1_title(content)
    return content


def main(args: argparse.Namespace) -> None:
    """Process all markdown files in the specified directory.

    Args:
        args: Parsed command-line arguments with markdown_directory attribute.
    """
    pattern = os.path.join(os.getcwd(), args.markdown_directory, "*.md")
    files = glob.glob(pattern)

    # Check if any files found
    if not files:
        print(f"No markdown files found in {args.markdown_directory}")
        return

    # Process each file
    for filename in files:
        print(f"Processing... {filename}")

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        # If error reading file, skip
        except IOError as e:
            print(f"Error reading {filename}: {e}")
            continue

        # Apply formatting
        formatted = format_markdown_file(content)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(formatted)
        # If error writing file, skip
        except IOError as e:
            print(f"Error writing {filename}: {e}")
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-process md-click-2 markdown.")
    parser.add_argument(
        "--markdown_directory",
        default="docs",
        help="Directory containing markdown files to process"
    )
    main(parser.parse_args())