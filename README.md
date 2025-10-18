# To LLM View

A Python tool that converts your codebase into unified text or JSON documents, optimized for working with Large Language Models (LLMs). Perfect for sharing your project context with AI assistants.

## Features

- **Git Integration**: Automatically discovers files from your Git repository
- **Smart Filtering**: Filter files by extensions or regex patterns
- **Multiple Output Formats**: Choose from text (bulk, slim) or JSON formats
- **Structured Output**: Creates organized documents with file trees and metadata
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

This creates `codebase_export.txt` with your entire codebase using the default bulk text converter.

### Advanced Options

```bash
# Filter by file extensions
to-llm-view -w py,js,html,css

# Custom output file
to-llm-view -o my_project_export

# Save to parent directory
to-llm-view -r

# Exclude files using regex
to-llm-view -rb "(^\.)|(^tsconfig)"

# Include files using regex
to-llm-view -rw ".*\.component\..*"

# Filter by filesize
to-llm-view -mf 2kb

# Choose output format
to-llm-view -c txt.slim          # Compact text format
to-llm-view -c txt.bulk          # Detailed text format (default)
to-llm-view -c json.basic        # JSON format

# Combine options
to-llm-view -r -o export -w py,md -c txt.slim
to-llm-view -r -rb "^public/" -mf 3.1kb
to-llm-view -r -rb "(^\.)|(^tsconfig)" -rw ".*\.component\..*"
to-llm-view -r -rw ".*\.component\..*" -w ts,js,html
to-llm-view -r -rw "^src/app/@standalone" -mf 1.4mb
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `-o, --output` | Output filename (default: codebase_export) |
| `-r, --root` | Save file in parent directory instead of current folder |
| `-w, --whitelist` | Include only specified file extensions (comma-separated) |
| `-rb, --regex-blacklist` | Exclude files matching regex pattern |
| `-rw, --regex-whitelist` | Include files matching regex pattern |
| `-mf, --max-filesize` | Maximum filesize to include (float, e.g.: 1.1mb, 2kb, 1.444gb, etc., default: 1mb) |
| `-c, --converter` | Output format converter (txt.bulk, txt.slim, json.basic) |

## Output Formats

### Text - Bulk (`txt.bulk`)
- Detailed file structure with traditional tree format
- Comprehensive file headers with timestamps
- Full error reporting and statistics
- Best for detailed analysis and debugging

### Text - Slim (`txt.slim`) 
- Compact, minimal file structure
- Clean, consistent formatting
- Essential metadata only
- Optimized for LLM consumption

### JSON (`json.basic`)
- Machine-readable JSON format
- Structured file tree and content
- Easy parsing and processing
- Ideal for automated workflows

## Requirements

- Python 3.6+
- Git installed and available in PATH
- Read access to your Git repository

## Project Structure

```
ToLLMView/
├── main.py                 # CLI entry point & argument processing
├── src/
│   ├── CodebaseConverter.py    # Core file retrieval logic
│   ├── utils.py                # Utility functions
│   └── converters/
│       ├── _IConverter.py      # Converter interface
│       ├── txt/
│       │   ├── bulk.py         # Bulk text converter
│       │   └── slim.py         # Slim text converter
│       └── json/
│           └── basic.py        # JSON converter
├── setup.py         # Package configuration
├── info.py          # Version information
├── README.md        # This file
└── .gitignore       # Git ignore rules
```

## Development

This is version 0.2.2. The project is actively maintained and welcomes contributions!

### Running from Source
```bash
python main.py [options]
```

### Adding New Converters
Create new converter classes in `src/converters/` that implement the `IConverter` interface.

---

**Note**: This tool helps prepare your codebase for LLM analysis. Always review the output for sensitive information before sharing.