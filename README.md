# To LLM View

A Python tool that converts your codebase into a unified text document, optimized for working with Large Language Models (LLMs). Perfect for sharing your project context with AI assistants.

## Features

- **Git Integration**: Automatically discovers files from your Git repository
- **Smart Filtering**: Filter files by extensions or regex patterns
- **Structured Output**: Creates organized text with file trees and metadata
- **Error Handling**: Gracefully handles binary files, encoding issues, and large files
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### From Source
```bash
git clone https://github.com/Makar-Ts/ToLLMView.git
cd ToLLMView
pip install -e .
```

### As Package
The project includes a `setup.py` for package distribution.

## Usage

### Basic Usage
```bash
# From the root of your Git repository
to-llm-view
```

This creates `codebase_export.txt` with your entire codebase.

### Advanced Options

```bash
# Filter by file extensions
to-llm-view -w py,js,html,css

# Custom output file
to-llm-view -o my_project_export.txt

# Save to parent directory
to-llm-view -r

# Exclude files using regex
to-llm-view -rb "(^\.)|(^tsconfig)"

# Include files using regex
to-llm-view -rw ".*\.component\..*"

# Filter by filesize
to-llm-view -mf 2kb

# Combine options
to-llm-view -r -o export.txt -w py,md
to-llm-view -r -rb "^public/" -mf 3.1kb
to-llm-view -r -rb "(^\.)|(^tsconfig)" -rw ".*\.component\..*"
to-llm-view -r -rw ".*\.component\..*" -w ts,js,html
to-llm-view -r -rw "^src/app/@standalone" -mf 1.4mb
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `-o, --output` | Output filename (default: codebase_export.txt) |
| `-r, --root` | Save file in parent directory instead of current folder |
| `-w, --whitelist` | Include only specified file extensions (comma-separated) |
| `-rb, --regex-blacklist` | Exclude files matching regex pattern |
| `-rw, --regex-whitelist` | Include files matching regex pattern |
| `-mf, --max-filesize` | Maximum filesize to include (float, e.g.: 1.1mb, 2kb, 1.444gb, etc., default: 1mb) |

## Output Format

The generated file includes:
- Project metadata and statistics
- Visual file tree structure
- Each file with:
  - File path
  - Size in characters
  - Processing timestamp
  - Full file content

## Requirements

- Python 3.6+
- Git installed and available in PATH
- Read access to your Git repository

## Project Structure

```
ToLLMView/
├── main.py          # Runfile & Arguments process
├── src/
    ├── CodebaseConverter.py    # Converter Logic
    ├── utils.py                # Utility functions
├── setup.py         # Package configuration
├── info.py          # Version information
├── README.md        # This file
└── .gitignore       # Git ignore rules
```

## Development

This is version 0.1.3. The project is actively maintained and welcomes contributions!

### Running from Source
```bash
python main.py [options]
```

---

**Note**: This is an early version (0.1.0) that was largely AI-generated. Use with caution and report any issues!