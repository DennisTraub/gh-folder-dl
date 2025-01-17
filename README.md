# GitHub Folder Downloader 

A Python library and CLI tool for downloading files from GitHub repository folders, with recursive support and smart caching. It tracks downloaded files in a SQLite database to avoid re-downloading unchanged files and maintains the original directory structure.

## Installation

### As a Library

```bash
pip install "gh-folder-dl @ git+https://github.com/DennisTraub/gh-folder-dl.git"
```

### With CLI Tool

```bash
pip install "gh-folder-dl[cli] @ git+https://github.com/DennisTraub/gh-folder-dl.git"
```

For development installation:

```bash
git clone https://github.com/DennisTraub/gh-folder-dl.git
cd gh-folder-dl
pip install -e ".[cli]"
```

## Usage

### As a Library

```python
from gh_folder_dl import GitHubDownloader
import asyncio

async def main():
    # Initialize the downloader
    downloader = GitHubDownloader(output_path="./output", debug=True)

    # Download files from a GitHub folder
    files_downloaded = await downloader.download_folder(
        "https://github.com/owner/repository/tree/branch/path/to/folder",
        recursive=True  # Also download subfolders
    )
    print(f"Downloaded {files_downloaded} files")

if __name__ == "__main__":
    asyncio.run(main())
```

### As a CLI Tool

```bash
# Basic usage
ghfolder https://github.com/owner/repository/tree/main/path/to/folder

# Download recursively with custom output directory
ghfolder -r https://github.com/owner/repository/tree/main/path/to/folder -o ./custom-output

# Enable debug logging
ghfolder -r -d https://github.com/owner/repository/tree/main/path/to/folder
```

## Features

- Downloads files from any public GitHub repository folder
- Recursive folder traversal (optional)
- Maintains original directory structure
- Smart caching using SQLite database
- Only downloads files that have changed (based on SHA)
- Detailed logging with debug option
- Available as both a library and CLI tool

## Output Structure

```
output/
├── files/           # Downloaded files with original structure
│   └── subfolder/
├── database/        # SQLite database for file tracking
│   └── files.db
└── logs/            # Execution and error logs
    ├── execution_[timestamp].log
    └── error_[timestamp].log
```

## Development

1. Clone the repository:
   ```bash
   git clone https://github.com/DennisTraub/gh-folder-dl
   cd gh-folder-dl
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[cli]"
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.