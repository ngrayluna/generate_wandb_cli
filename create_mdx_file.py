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

### Main logic to read source info and generate MDX file for "login" command
with open('source_info_debug.json', 'r', encoding='utf-8') as file:
    json_file = json.load(file)


test_command = "login"


cmd_name = json_file.get(test_command, {}).get("name", [])


all_arguments = "\n".join([
    f"| {arg['name']} | {arg['type']} | {arg['default']} | {arg['required']} |" for arg in json_file.get(test_command, {}).get("arguments", [])
])

# Only include options that are not hidden
all_options = "\n".join([
    f"| {', '.join(opt['opts'])} | {opt['type']} | {opt['description']} **Default**: {opt['default']} |" for opt in json_file.get(test_command, {}).get("options", []) if not opt['hidden']
])


with open(f"output_debugz/wandb-{cmd_name}.mdx", "w", encoding="utf-8") as f:
    f.write(mdx_template.format(
        name=test_command,
        description=json_file.get(test_command, {}).get("description", ""),
        options=all_options,
        arguments=all_arguments,
        examples=format_code_block(json_file.get(test_command, {}).get("examples", "")),
        import_statements = github_import_statement(),
        github_path=format_github_button(json_file[test_command].get("source_file", ""), json_file[test_command].get("line_number", "")),
        usage=json_file.get(test_command, {}).get("usage", "")
        )
    )