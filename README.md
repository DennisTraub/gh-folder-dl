# GitHub File Downloader

A Python library and CLI tool for downloading files from GitHub repository folders. It tracks downloaded files in a SQLite database and only downloads files that have changed.

## Installation

### As a Library

```bash
pip install git+https://github.com/username/github-file-downloader.git
```

### With CLI Tool

```bash
pip install "git+https://github.com/username/github-file-downloader.git#egg=gh-file-downloader[cli]"
```

## Usage

### As a Library

```python
from gh_file_downloader import GitHubDownloader

# Initialize the downloader
downloader = GitHubDownloader(output_path="./output", debug=True)

# Download files from a GitHub folder
files_downloaded = downloader.download_folder(
    "https://github.com/aws/aws-sdk-js-v3/tree/main/codegen/sdk-codegen/aws-models"
)
print(f"Downloaded {files_downloaded} files")
```

### As a CLI Tool

```bash
# Basic usage
ghget https://github.com/aws/aws-sdk-js-v3/tree/main/codegen/sdk-codegen/aws-models

# Specify output directory
ghget https://github.com/aws/aws-sdk-js-v3/tree/main/codegen/sdk-codegen/aws-models -o ./custom-output

# Enable debug logging
ghget https://github.com/aws/aws-sdk-js-v3/tree/main/codegen/sdk-codegen/aws-models -d
```

## Features

- Downloads files from any public GitHub repository folder
- Tracks downloaded files in a SQLite database
- Only downloads files that have changed (based on SHA)
- Supports debug logging
- Can be used as a library or CLI tool

## Project Structure

```
github-file-downloader/
├── src/
│   └── gh_file_downloader/
│       ├── __init__.py      # Package initialization and version
│       ├── downloader.py    # Core library code
│       └── cli.py          # CLI application
├── tests/                   # Test files
├── pyproject.toml          # Project metadata and dependencies
├── LICENSE                 # MIT License
└── README.md              # This file
```

## Development

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[cli]"
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.