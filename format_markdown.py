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
        Dict mapping func_name -> {name, func_name, source_file, line_number, ...}
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def _github_button(href_links):
    """Add a GitHub button with the given URL.
    
    Args:
        href_links (str): URL for the GitHub button.
    """
    return '<GitHubLink url="' + href_links + '" />' + "\n\n"

def add_github_import_statement():
    """Add GitHub import statement to the markdown file.
    
    Args:
        filename (str): Name of the file.
    """
    return "import { GitHubLink } from '/snippets/en/_includes/github-source-link.mdx';" + "\n\n"


def format_github_button(
    source_file: str,
    line_number: int,
    release_tag: Optional[str] = None
) -> str:
    """Build a GitHub source link button for a file.

    Args:
        source_file: Local path to source file (from inspect.getfile)
        line_number: Line number in source file
        release_tag: Git tag for GitHub URL (e.g., 'v0.18.3'). Defaults to 'main'.

    Returns:
        GitHubLink component string

    Example output URL:
        https://github.com/wandb/wandb/blob/v0.18.3/wandb/cli/cli.py#L314
    """
    # Extract repo-relative path (e.g., "wandb/cli/cli.py")
    _, sep, after = source_file.rpartition('/wandb/')
    repo_path = 'wandb/' + after if sep else source_file

    git_ref = release_tag if release_tag else "main"
    github_url = f"https://github.com/wandb/wandb/blob/{git_ref}/{repo_path}#L{line_number}"

    return _github_button(github_url)



def add_source_link(content: str, source_file: str, line_number: int, release_tag: str = None) -> str:
    """Add a source code link at the top of the content (after frontmatter).

    Args:
        content: Markdown content
        source_file: Path to source file (local path from inspect.getfile)
        line_number: Line number in source file
        release_tag: Git tag for GitHub URL (e.g., 'v0.18.3')

    Returns:
        Content with source link inserted at the top
    """
    # Build the import statement and GitHub button
    import_statement = add_github_import_statement()
    github_button = format_github_button(source_file, line_number, release_tag)
    source_link = f"{import_statement}{github_button}"

    # Insert at the beginning (frontmatter is added separately in main())
    return source_link + content


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

def add_description_heading(content: str) -> str:
    """Add a '## Description' heading after the <GitHubLink ... /> line."""
    return re.sub(
        r'(<GitHubLink\s+url="[^"]*"\s*/>)',
        r'\1\n\n## Description',
        content,
    )


def move_usage_before_description(content: str) -> str:
    """Move the ## Usage section above the ## Description section."""
    pattern = r'(## Description\n.*?)(## Usage\n.*?)(?=\n## |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content
    return content[:match.start()] + match.group(2) + '\n' + match.group(1) + content[match.end():]


def format_examples_section(content: str) -> str:
    """Replace 'Examples:' with '## Examples' as a markdown heading."""
    return content.replace('Examples:', '## Examples')


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


_TYPE_DISPLAY_NAMES = {
    "StringParamType": "STR",
    "IntParamType": "INT",
    "IntRange": "INT",
    "FloatParamType": "FLOAT",
    "FloatRange": "FLOAT",
    "BoolParamType": "BOOL",
    "Path": "PATH",
}


def normalize_click_type(raw_type: str, classification: str) -> str:
    """Map Click type class names to clean display names.

    Returns one of: STR, INT, FLOAT, BOOL, BOOL Flag, or the raw type name
    as a fallback for uncommon types (e.g. Choice, Path, File).
    """
    if classification in ("boolean-flag", "boolean-dual-flag"):
        return "BOOL Flag"
    return _TYPE_DISPLAY_NAMES.get(raw_type, raw_type)


def build_options_table_from_json(json_options: list) -> str:
    """Build markdown option tables from structured JSON option metadata.

    Args:
        json_options: List of option dicts from inspect_click_commands.py

    Returns:
        Formatted markdown string with tables for each option
    """
    tables = []
    for option in json_options:
        name = option["name"]
        description = option.get("help") or "No description available."
        default = option.get("default", "")
        opt_type = normalize_click_type(
            option.get("type", ""),
            option.get("classification", ""),
        )

        # Build flags string based on classification
        if option.get("classification") == "boolean-dual-flag":
            primary = ", ".join(option.get("opts", []))
            secondary = ", ".join(option.get("secondary_opts", []))
            flags = f"{primary} / {secondary}"
        else:
            all_opts = option.get("opts", []) + option.get("secondary_opts", [])
            flags = ", ".join(all_opts)

        table = f"""### `{name}`

{description}

| Flag | Default | Type |
|------|---------|------|
| `{flags}` | {default} | {opt_type} |
"""
        tables.append(table)

    return "\n".join(tables)


def build_arguments_table_from_json(json_arguments: list) -> str:
    """Build markdown argument tables from structured JSON argument metadata.

    Args:
        json_arguments: List of argument dicts from inspect_click_commands.py

    Returns:
        Formatted markdown string with tables for each argument
    """
    tables = []
    for argument in json_arguments:
        name = argument["name"]
        default = argument.get("default", "")
        arg_type = normalize_click_type(argument.get("type", ""), "")

        table = f"""### `{name}`

| Name | Default | Type |
|------|---------|------|
| `{name}` | {default} | {arg_type} |
"""
        tables.append(table)

    return "\n".join(tables)


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
                table = f"""### `{opt['name']}`

{opt['description']}                

| Flag | Default | Type | 
|------|---------|------|
| `{opt['flags']}` | {opt['default']} | {opt['type']} |
"""
            elif section_type == 'arguments':
                # Arguments don't have flags, just the name
                table = f"""### `{opt['name']}`

| Name | Default | Type |
|------|---------|------|
| `{opt['name']}` | {opt['default']} | {opt['type']} |
"""                
            else:
                # Fallback to a generic table if section_type is unrecognized
                table = f"""### `{opt['name']}`

| Name | Default | Type | Description |
|------|---------|------|-------------|
| `{opt['name']}` | {opt['default']} | {opt['type']} | {opt['description']} |
"""
            tables.append(table)

    return '\n'.join(tables)


def _convert_section(content: str, section_name: str, section_type: str, json_options: list = None) -> str:
    """Convert a markdown section's bullet points to tables.

    Args:
        content: Full markdown file content
        section_name: Section header name (e.g., 'Options', 'Arguments')
        section_type: Type for table formatting ('options' or 'arguments')
        json_options: Optional structured option metadata from inspect_click_commands.py

    Returns:
        Modified content with section converted to tables
    """
    pattern = rf'(## {section_name}\n)(.*?)(?=\n## |\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return content

    header = match.group(1)
    section_content = match.group(2)

    if json_options and section_type == 'options':
        new_section_content = build_options_table_from_json(json_options)
    elif json_options and section_type == 'arguments':
        new_section_content = build_arguments_table_from_json(json_options)
    else:
        new_section_content = convert_section_to_tables(section_content, section_type)

    new_section = header + '\n' + new_section_content
    return content[:match.start()] + new_section + content[match.end():]


def convert_options_to_tables(content: str, json_options: list = None) -> str:
    """Convert the ## Options section from bullet points to markdown tables."""
    return _convert_section(content, 'Options', 'options', json_options=json_options)


def convert_arguments_to_tables(content: str, json_arguments: list = None) -> str:
    """Convert the ## Arguments section from bullet points to markdown tables."""
    return _convert_section(content, 'Arguments', 'arguments', json_options=json_arguments)


def remove_cli_help_section(content: str) -> str:
    """Remove the ## CLI Help section (heading and its fenced code block)."""
    return re.sub(r'## CLI Help\n.*?(?=\n## |\Z)', '', content, flags=re.DOTALL)


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
    line_number: Optional[int] = None,
    release_tag: Optional[str] = None,
    options: list = None,
    arguments: list = None
) -> str:
    """Apply all formatting transformations to markdown content.

    Args:
        content: Full markdown file content
        source_file: Optional path to source file for GitHub link
        line_number: Optional line number in source file
        release_tag: Optional git tag for GitHub URL (e.g., 'v0.18.3')
        options: Optional structured option metadata from inspect_click_commands.py
        arguments: Optional structured argument metadata from inspect_click_commands.py

    Returns:
        Modified content with all transformations applied
    """
    content = format_usage_code_block(content)
    content = convert_options_to_tables(content, json_options=options)
    content = convert_arguments_to_tables(content, json_arguments=arguments)
    content = remove_empty_arguments_section(content)
    content = remove_cli_help_section(content)
    content = format_examples_section(content)
    content = remove_h1_title(content)

    # Add source link if source info is provided
    if source_file and line_number:
        content = add_source_link(content, source_file, line_number, release_tag)
        content = add_description_heading(content)
        content = move_usage_before_description(content)

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
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            print(f"Error reading {filename}: {e}")
            continue

        # Get source info for this command if available
        basename = os.path.splitext(os.path.basename(filename))[0]
        # TO DO: replace dash with space?
        func_name = basename.replace('-', '_')  # Handle "docker-run" -> "docker_run"

        # Default to None if not found
        source_file = None
        line_number = None

        # Look up source info
        options = None
        arguments = None
        if func_name in source_info:
            cmd_info = source_info[func_name]
            source_file = cmd_info.get('source_file')
            line_number = cmd_info.get('line_number')
            options = cmd_info.get('options', []) or None
            arguments = cmd_info.get('arguments', []) or None

        # Apply all formatting transformations (including source link if available)
        formatted = format_markdown_file(content, source_file, line_number, args.release_tag, options=options, arguments=arguments)

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
    parser.add_argument(
        "--release-tag",
        metavar="TAG",
        help="Git release tag for GitHub source links (e.g., 'v0.18.3'). Defaults to 'main'."
    )
    main(parser.parse_args())