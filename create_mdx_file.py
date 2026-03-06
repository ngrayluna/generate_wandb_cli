import re
import json
from typing import Optional

from cli_doc_template import mdx_template

def _github_button(href_links):
    """Add a GitHub button with the given URL.
    
    Args:
        href_links (str): URL for the GitHub button.
    """
    return '<GitHubLink url="' + href_links + '" />' + "\n\n"

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

def github_import_statement():
    """Mintlify-friendly import statement for GitHubLink component used in MDX templates."""
    return "import { GitHubLink } from '/snippets/en/_includes/github-source-link.mdx';" + "\n\n"

def format_code_block(content: str) -> str:
    """Convert indented '$ wandb ...' lines into fenced bash code blocks.

    Before:
        Verify the currently configured W&B instance.

            $ wandb verify --host https://my-wandb-instance.com

    After:
        Verify the currently configured W&B instance.

        ```bash
        wandb verify --host https://my-wandb-instance.com
        ```
    """
    def replace_match(match):
        command = match.group(1).strip()
        return f"\n```bash\n{command}\n```"

    return re.sub(r'^\s*\$ (.+)$', replace_match, content, flags=re.MULTILINE)

_TYPE_DISPLAY_NAMES = {
    "StringParamType": "STR",
    "IntParamType": "INT",
    "IntRange": "INT",
    "FloatParamType": "FLOAT",
    "FloatRange": "FLOAT",
    "BoolParamType": "BOOL",
    "Path": "PATH",
}

def normalize_type(raw_type: str, classification: str) -> str:
    """Map Click type class names to clean display names."""
    if classification in ("boolean-flag", "boolean-dual-flag"):
        return "BOOL Flag"
    return _TYPE_DISPLAY_NAMES.get(raw_type, raw_type)


# test_command = "login"
# cmd_name = json_file.get(test_command, {}).get("name", [])

### Main logic to read source info and generate MDX file for "login" command
with open('source_info_debug.json', 'r', encoding='utf-8') as file:
    json_file = json.load(file)

for command_name, command_info in json_file.items():
    arguments = command_info.get("arguments","")
    options = command_info.get("options", "")
    line_number = command_info.get("line_number","")
    source_file = command_info.get("source_file","")
    examples = command_info.get("examples", "")
    description = command_info.get("description", "")

    all_arguments = "\n".join([
        f"| `{arg['name']}` | {normalize_type(arg['type'], arg.get('classification', ''))} | {arg['default']} | {arg['required']} |" for arg in arguments
    ])

    # Only include options that are not hidden
    all_options = "\n".join([
        f"| `{', '.join(opt['opts'])}` | {normalize_type(opt['type'], opt.get('classification', ''))} | {opt['description']} **Default**: {opt['default']} |" for opt in options if not opt['hidden']
    ])


    with open(f"output_debugz/wandb-{command_name}.mdx", "w", encoding="utf-8") as f:
        f.write(mdx_template.format(
            name=command_name,
            description=description,
            options=all_options,
            arguments=all_arguments,
            examples=format_code_block(examples),
            import_statements = github_import_statement(),
            github_path=format_github_button(source_file, line_number),
            usage=json_file.get(command_name, {}).get("usage", "")
            )
        )