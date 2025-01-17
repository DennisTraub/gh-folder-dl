"""Command-line interface for gh-folder-dl."""

import click
import asyncio
from . import GitHubDownloader


@click.command()
@click.argument("url")
@click.option("--output", "-o", default="./output", help="Output directory path")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
@click.option("--recursive", "-r", is_flag=True, help="Download files from subfolders recursively")
def main(url: str, output: str, debug: bool, recursive: bool):
    """Download files from a GitHub repository folder.

    URL should point to a folder in a public GitHub repository, e.g.:
    https://github.com/aws/aws-sdk-js-v3/tree/main/codegen/sdk-codegen/aws-models

    Files are downloaded to the output directory (default: ./output) maintaining
    the original directory structure. A SQLite database tracks downloaded files
    to avoid re-downloading unchanged content.
    """
    try:
        downloader = GitHubDownloader(output_path=output, debug=debug)
        files_downloaded = asyncio.run(downloader.download_folder(url, recursive=recursive))
        if files_downloaded == 0:
            click.echo("No new files downloaded.")
        else:
            click.echo(f"Successfully downloaded {files_downloaded} files.")
    except Exception as e:
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
