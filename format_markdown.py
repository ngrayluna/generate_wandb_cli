"""
Custom formatting for markdown files and Mintlify integration.

Converts md-click bullet point options/arguments to markdown tables.
"""
import os
import argparse
import glob
import re

def remove_h1_title(content):
    """Remove the first H1 title from the markdown content.

    Matches '# title' at the start of a line and removes it along with the newline.
    """
    return re.sub(r'^# .+\n+', '', content, count=1, flags=re.MULTILINE)


def format_usage_code_block(content):
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


def format_flags(usage_str):
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


def parse_option_block(block):
    """Parse a single option block and return its components.

    Input format:
        * `option_name`:
            * Type: STRING
            * Default: `None`
            * Usage: `--option
        -o`
            Description text here.

    Returns dict with: name, type, default, flags, description
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
        'description': description
    }


def convert_section_to_tables(section_content, section_type='options'):
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


def convert_options_to_tables(content):
    """Convert the ## Options section from bullet points to markdown tables.

    Args:
        content: Full markdown file content

    Returns:
        Modified content with Options section converted to tables
    """
    # Find the ## Options section (ends at next ## or end of file)
    options_pattern = r'(## Options\n)(.*?)(?=\n## |\Z)'
    options_match = re.search(options_pattern, content, re.DOTALL)

    if not options_match:
        return content

    options_header = options_match.group(1)
    options_content = options_match.group(2)

    # Convert to tables
    new_options_content = convert_section_to_tables(options_content, 'options')

    # Replace the options section
    new_options = options_header + '\n' + new_options_content
    new_content = content[:options_match.start()] + new_options + content[options_match.end():]

    return new_content


def convert_arguments_to_tables(content):
    """Convert the ## Arguments section from bullet points to markdown tables.

    Args:
        content: Full markdown file content

    Returns:
        Modified content with Arguments section converted to tables
    """
    # Find the ## Arguments section (ends at next ## or end of file)
    args_pattern = r'(## Arguments\n)(.*?)(?=\n## |\Z)'
    args_match = re.search(args_pattern, content, re.DOTALL)

    if not args_match:
        return content

    args_header = args_match.group(1)
    args_content = args_match.group(2)

    # Skip if empty
    if not args_content.strip():
        return content

    # Convert to tables
    new_args_content = convert_section_to_tables(args_content, 'arguments')

    # Replace the arguments section
    new_args = args_header + '\n' + new_args_content
    new_content = content[:args_match.start()] + new_args + content[args_match.end():]

    return new_content


def format_markdown_file(content):
    """Apply all formatting transformations to markdown content.

    Args:
        content: Full markdown file content

    Returns:
        Modified content with all transformations applied
    """
    content = format_usage_code_block(content)
    content = convert_options_to_tables(content)
    content = convert_arguments_to_tables(content)
    content = remove_h1_title(content)
    return content


def main(args):
    for filename in glob.glob(os.path.join(os.getcwd(), args.markdown_directory, "*.md")):
        print("Processing...", filename)

        with open(filename, 'r') as f:
            content = f.read()

        formatted = format_markdown_file(content)

        with open(filename, 'w') as f:
            f.write(formatted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-process md-click-2 markdown.")
    parser.add_argument("--markdown_directory", default="docs",
                        help="Directory containing markdown files to process")
    main(parser.parse_args())