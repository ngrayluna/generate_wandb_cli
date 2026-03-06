import re
import json
from cli_doc_template import mdx_template

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

with open('source_info_debug.json', 'r', encoding='utf-8') as file:
    json_file = json.load(file)


cmd_name = json_file.get("login", {}).get("name", [])


all_arguments = "\n".join([
    f"| {arg['name']} | {arg['type']} | {arg['default']} | {arg['required']} |" for arg in json_file.get("login", {}).get("arguments", [])
])

all_options = "\n".join([
    f"| {opt['name']} | {opt['type']} | {opt['description']} **Default**: {opt['default']} |" for opt in json_file.get("login", {}).get("options", [])
])


with open(f"output_debugz/wandb-{cmd_name}.mdx", "w", encoding="utf-8") as f:
    f.write(mdx_template.format(
        name="login",
        description=json_file.get("login", {}).get("description", ""),
        options=all_options,
        arguments=all_arguments,
        examples=format_code_block(json_file.get("login", {}).get("examples", ""))
        )
    )