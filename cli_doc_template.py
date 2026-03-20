"""
Templates for generating MDX documentation files for Click commands. These templates are used by `create_mdx_file.py` to create the content of the MDX files based on the extracted information from the Click commands.

Templates include placeholders for various sections such as usage, description, examples, arguments, and options, which are filled in with the actual content when generating the MDX files.
"""

## Template for individual Click commands (commands that do not have subcommands)
mdx_template = """---
title: wandb {name}
---

{import_statements}
{github_path}

## Usage

```bash
{usage}
```

## Description

{description}

{examples_section}

{arguments_section}

{options_section}
"""

## Template for Click command groups (commands that have subcommands)

mdx_group_template = """---
title: wandb {name}
---

{import_statements}
{github_path}

## Usage

```bash
{usage}
```

## Description

{description}

{subcommands_section}
"""