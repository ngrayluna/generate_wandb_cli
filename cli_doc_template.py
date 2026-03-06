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

## Examples

{examples}


## Arguments

| Name | Default | Type |
|------|---------|------|
{arguments}

## Options

| Flag | Type | Description |
|------|------|-------------|
{options}
"""