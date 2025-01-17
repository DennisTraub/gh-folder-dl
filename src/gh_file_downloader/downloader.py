import requests
import sqlite_utils
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


class GitHubDownloader:
    """Downloads files from GitHub repository folders with SHA tracking."""

    def __init__(self, output_path="./output", debug=False):
        """Initialize the downloader with output path and debug setting."""
        self.output_path = Path(output_path)
        self.files_dir = self.output_path / "files"
        self.db_dir = self.output_path / "database"
        self.logger = self._setup_logging(debug)
        self.db = None
        self.files_table = None

    def _setup_logging(self, debug=False):
        """Set up logging configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logs_dir = self.output_path / "logs"
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
        logger = logging.getLogger(__name__)
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

    def _init_database(self):
        """Initialize SQLite database."""
        self.db = sqlite_utils.Database(self.db_dir / "files.db")
        if "files" not in self.db.tables:
            self.logger.debug("Creating new files table in database")
            self.db["files"].create({
                "filename": str,
                "relative_path": str,  # Added to store relative path
                "sha": str,
                "timestamp": str
            }, pk=("filename", "relative_path"))  # Composite primary key
            self.logger.debug("Files table created successfully")
        else:
            self.logger.debug("Files table already exists in database")

        self.files_table = self.db["files"]

    def _parse_github_url(self, url):
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

    def _get_folder_contents(self, owner, repo, branch, path):
        """Fetch contents of a GitHub repository folder."""
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        self.logger.debug(f"Fetching contents from: {api_url}")
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()

    def _download_file(self, url, output_path):
        """Download a file from GitHub."""
        response = requests.get(url)
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.content)

    def _process_item(self, item, owner, repo, branch, base_path, relative_path=""):
        """Process a single item (file or directory) from GitHub."""
        if item["type"] == "file":
            filename = item["name"]
            sha = item["sha"]
            download_url = item["download_url"]

            # Combine relative path with filename for database lookup
            full_relative_path = str(Path(relative_path) / filename)
            file_path = self.files_dir / full_relative_path

            self.logger.debug(f"Processing file: {full_relative_path}")

            try:
                existing_record = self.files_table.get({"filename": filename, "relative_path": relative_path})
                self.logger.debug(f"Found existing record for {full_relative_path}")
                if existing_record["sha"] == sha:
                    self.logger.info(f"File {full_relative_path} already exists with same SHA, skipping...")
                    return 0
                self.logger.debug(f"SHA mismatch for {full_relative_path}, will download")
            except sqlite_utils.db.NotFoundError:
                self.logger.debug(f"No existing record found for {full_relative_path}")

            # Download file
            self.logger.info(f"Downloading {full_relative_path}...")
            self._download_file(download_url, file_path)

            # Update database
            timestamp = datetime.now().isoformat()
            self.files_table.upsert({
                "filename": filename,
                "relative_path": relative_path,
                "sha": sha,
                "timestamp": timestamp
            }, pk=("filename", "relative_path"))

            self.logger.debug(f"Successfully processed {full_relative_path}")
            return 1

        return 0

    async def _process_folder(self, owner, repo, branch, path, relative_path=""):
        """Process a folder and its contents, optionally recursively."""
        contents = self._get_folder_contents(owner, repo, branch, path)
        files_downloaded = 0

        for item in contents:
            if item["type"] == "file":
                files_downloaded += self._process_item(item, owner, repo, branch, path, relative_path)
            elif item["type"] == "dir":
                self.logger.debug(f"Found directory: {item['name']}")
                new_path = f"{path}/{item['name']}"
                new_relative_path = str(Path(relative_path) / item['name'])
                files_downloaded += await self._process_folder(owner, repo, branch, new_path, new_relative_path)

        return files_downloaded

    async def download_folder(self, github_url, recursive=False):
        """
        Download files from a GitHub repository folder.

        Args:
            github_url (str): URL to a folder in a GitHub repository
            recursive (bool): Whether to download files from subfolders recursively

        Returns:
            int: Number of files downloaded
        """
        try:
            # Create directory structure
            self.logger.debug("Setting up directory structure...")
            self.files_dir.mkdir(parents=True, exist_ok=True)
            self.db_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug("Directory structure created successfully")

            # Initialize database
            self.logger.debug("Initializing database")
            self._init_database()

            # Parse GitHub URL
            self.logger.debug(f"Parsing GitHub URL: {github_url}")
            owner, repo, branch, path = self._parse_github_url(github_url)
            self.logger.info(f"Processing repository: {owner}/{repo}, branch: {branch}, path: {path}")

            files_downloaded = await self._process_folder(owner, repo, branch, path)

            self.logger.info(f"Download completed successfully. Downloaded {files_downloaded} files.")
            return files_downloaded

        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}")
            self.logger.debug("Exception details:", exc_info=True)
            raise
