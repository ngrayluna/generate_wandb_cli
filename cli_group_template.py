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

## Subcommands

| Command | Description |
|---------|-------------|
{subcommands}
"""