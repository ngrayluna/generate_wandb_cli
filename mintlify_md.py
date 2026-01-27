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


def main(args):
    for filename in glob.glob(os.path.join(os.getcwd(), args.markdown_directory, "*.md")):
        print("Mintlify-ing docs...", filename)
        with open(filename, 'r') as f:
            content = f.read()
        frontmatter = add_frontmatter(filename)
        with open(filename, 'w') as f:
            f.write(frontmatter + content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-process md-click-2 markdown.")
    parser.add_argument("--markdown_directory", default="docs",
                        help="Directory containing markdown files to process")
    main(parser.parse_args())