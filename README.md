# Generate W&B Models CLI

Generate markdown reference documentation for [W&B CLI commands](https://github.com/wandb/wandb/tree/main/wandb/cli).

## Usage

Specify the `wandb` GitHub release tag that you want to generate docs for:

```bash
./generate_cli.sh <release_tag>
```

Example:
```bash
./generate_cli.sh v0.18.3
```

## What it does

1. Clones/updates the `wandb/wandb` repo to `./wandb/`
2. Checks out the specified release tag
3. Discovers all public (non-hidden) CLI commands
4. Generates markdown docs using `md-click-2`
5. Formats docs with tables and GitHub source links

Output is written to `./output/`.

## Prerequisites

Install Python package requirements:
  ```bash
  pip install -r requirements.txt
  ```

## Files

| File | Description |
|------|-------------|
| `generate_cli.sh` | Main script that orchestrates the pipeline |
| `get_public_commands.py` | Discovers public CLI commands and their source locations |
| `format_markdown.py` | Formats markdown with tables, frontmatter, and GitHub links |

## Output format

Each generated markdown file includes:
- Mintlify frontmatter
- GitHub source link component
- Usage section with shell code block
- Options/Arguments as markdown tables
- CLI help output
