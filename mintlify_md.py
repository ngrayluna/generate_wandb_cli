"""
Reads in markdown files and adds metadata and other post-processing for Mintlify.
"""
import argparse
import glob
import os
import re

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

def rename_markdown_files(directory: str, convert_to_mdx: bool = False) -> None:
    """Rename markdown files in the specified directory.

    Renames file.md to wandb-file.mdx if convert_to_mdx is True, else keeps .md extension.

    Args:
        directory: Directory containing markdown files
        convert_to_mdx: If True, convert .md files to .mdx
    """
    pattern = os.path.join(os.getcwd(), directory, "*.md")
    files = glob.glob(pattern)

    for filename in files:
        base, ext = os.path.splitext(filename)
        if convert_to_mdx:
            new_filename = "wandb-" + os.path.basename(base) + ".mdx"
        else:
            new_filename = filename  # No change
        if new_filename != filename:
            os.rename(filename, new_filename)

def group_markdown_files(directory: str) -> None:
    """Group markdown files into subdirectories based on command hierarchy.

    For example, artifact-ls.md, and artifact-cache.md go into an 'wandb-artifact' subdirectory.

    Args:
        directory: Directory containing markdown files
    """
    pattern = os.path.join(os.getcwd(), directory, "*.md")
    files = glob.glob(pattern)

    # Read in files and parse command names

    # Find out if more than one command shares the same prefix

    # If yes, create subdirectory

    # move those files into that subdirectory

    # for filename in files:
    #     base = os.path.basename(filename)
    #     command_name = os.path.splitext(base)[0]
    #     parts = command_name.split('_')

    #     print(f"Base:{base}")
    #     print(command_name)
    #     print(parts)

    #     if len(parts) > 1:
    #         subdir = os.path.join(os.getcwd(), directory, "wandb-" + parts[0])
    #         os.makedirs(subdir, exist_ok=True)
    #         new_path = os.path.join(subdir, base)
    #         os.rename(filename, new_path)


def main(args):
    for filename in glob.glob(os.path.join(os.getcwd(), args.markdown_directory, "*.md")):
        print("Mintlify-ing docs...", filename)
        with open(filename, 'r') as f:
            content = f.read()
        frontmatter = add_frontmatter(filename)
        with open(filename, 'w') as f:
            f.write(frontmatter + content)

    # Group commands into subdirectories if needed
    #group_markdown_files(args.markdown_directory)

    # Rename files if needed
    #rename_markdown_files(args.markdown_directory, convert_to_mdx=args.convert_to_mdx)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-process md-click-2 markdown.")
    parser.add_argument("--markdown_directory", default="docs",
                        help="Directory containing markdown files to process")
    parser.add_argument("--convert_to_mdx", action='store_true',
                        help="Convert .md files to .mdx for Mintlify")
    main(parser.parse_args())