# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "requests",
#     "sqlite-utils",
# ]
# ///

import click
import requests
import sqlite_utils
import json
import os
import logging
import sqlite_utils.db
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def setup_logging(output_path, debug=False):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_dir = Path(output_path) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Setup file handlers
    execution_handler = logging.FileHandler(logs_dir / f"execution_{timestamp}.log")
    error_handler = logging.FileHandler(logs_dir / f"error_{timestamp}.log")
    console_handler = logging.StreamHandler()

    # Setup formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    execution_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure logger
    logger = logging.getLogger()
    log_level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(log_level)

    # Add handlers with appropriate levels
    execution_handler.setLevel(log_level)
    error_handler.setLevel(logging.ERROR)
    console_handler.setLevel(log_level)

    logger.addHandler(execution_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)

    return logger


def parse_github_url(url):
    """Extract repository owner, name, and path from GitHub URL."""
    parsed = urlparse(url)
    if parsed.netloc != "github.com":
        raise ValueError("URL must be a GitHub URL")

    parts = parsed.path.strip("/").split("/")
    if len(parts) < 5 or parts[2] != "tree":
        raise ValueError("URL must point to a folder in a GitHub repository")

    owner = parts[0]
    repo = parts[1]
    branch = parts[3]
    path = "/".join(parts[4:])

    return owner, repo, branch, path


def get_folder_contents(owner, repo, branch, path):
    """Fetch contents of a GitHub repository folder."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()


def download_file(url, output_path):
    """Download a file from GitHub."""
    response = requests.get(url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)


def init_database(db_path, logger):
    """Initialize SQLite database."""
    db = sqlite_utils.Database(db_path)
    if "files" not in db.tables:
        logger.debug("Creating new files table in database")
        db["files"].create({
            "filename": str,
            "sha": str,
            "timestamp": str
        }, pk="filename", if_not_exists=True)
        logger.debug("Files table created successfully")
    else:
        logger.debug("Files table already exists in database")
    return db


@click.command()
@click.argument("url")
@click.option("--output", "-o", default="./output", help="Output directory path")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging")
def main(url, output, debug):
    """Download files from a GitHub repository folder."""
    try:
        # Setup directory structure
        output_path = Path(output)
        files_dir = output_path / "files"
        db_dir = output_path / "database"

        # Setup logging first
        logger = setup_logging(output_path, debug)
        logger.debug("Logging system initialized successfully (debug mode: %s)", debug)

        # Create directories
        logger.debug("Setting up directory structure...")
        logger.debug(f"Creating directories: files_dir={files_dir}, db_dir={db_dir}")
        files_dir.mkdir(parents=True, exist_ok=True)
        db_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("Directory structure created successfully")

        # Parse GitHub URL
        logger.debug(f"Parsing GitHub URL: {url}")
        owner, repo, branch, path = parse_github_url(url)
        logger.info(f"Processing repository: {owner}/{repo}, branch: {branch}, path: {path}")
        logger.debug("URL parsing completed successfully")

        # Initialize database
        logger.debug(f"Initializing database at {db_dir / 'files.db'}")
        db = init_database(db_dir / "files.db", logger)
        files_table = db["files"]
        logger.debug("Database initialized successfully")

        # Fetch folder contents
        logger.debug(f"Fetching contents from GitHub API for {path}")
        contents = get_folder_contents(owner, repo, branch, path)
        logger.debug(f"Retrieved {len(contents)} items from GitHub API")

        # Process each file
        logger.debug("Beginning file processing...")
        for item in contents:
            if item["type"] != "file":
                logger.debug(f"Skipping non-file item: {item['name']}")
                continue

            filename = item["name"]
            sha = item["sha"]
            download_url = item["download_url"]
            file_path = files_dir / filename
            logger.debug(f"Processing file: name={filename}, sha={sha}, url={download_url}")

            # Check if file exists in database
            logger.debug(f"Checking database for existing record of {filename}")
            try:
                existing_record = files_table.get(filename)
                logger.debug(f"Found existing record for {filename}: sha={existing_record['sha']}")
                if existing_record["sha"] == sha:
                    logger.info(f"File {filename} already exists with same SHA, skipping...")
                    continue
                else:
                    logger.debug(f"SHA mismatch for {filename}. Old: {existing_record['sha']}, New: {sha}")
            except sqlite_utils.db.NotFoundError:
                logger.debug(f"No existing record found for {filename}, will download")
                existing_record = None
            # Download file
            logger.info(f"Downloading {filename}...")
            logger.debug(f"Beginning download from {download_url}")
            download_file(download_url, file_path)
            logger.debug(f"Download completed: {file_path}")

            # Update database
            timestamp = datetime.now().isoformat()
            logger.debug(f"Updating database record for {filename}")
            files_table.upsert({
                "filename": filename,
                "sha": sha,
                "timestamp": timestamp
            }, pk="filename")
            logger.debug(f"Database update completed for {filename}")

            logger.info(f"Successfully processed {filename}")

        logger.info("Download completed successfully")
        logger.debug("Main processing loop completed")

    except Exception as e:
        if logger:
            logger.error(f"An error occurred: {str(e)}")
            logger.debug(f"Exception details: {type(e).__name__}: {str(e)}", exc_info=True)
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
