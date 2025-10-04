#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from pathlib import Path
from typing import AnyStr, List, Set, Optional
import argparse
from datetime import datetime
import re

from info import VERSION


class CodebaseConverter:
    """Main class for converting codebase to text format."""
    
    def __init__(self, output_file: str = "codebase_export.txt", output_dir: str = None):
        """
        Initialize converter.
        
        Args:
            output_file: Output filename
            output_dir: Directory path where file will be saved
        """
        
        if output_dir is not None:
            self.output_file = output_dir + os.sep + output_file
        else:
            self.output_file = output_file
        
        self.processed_files = 0
        self.skipped_files = 0
        self.errors = []
        
    def get_git_files(self) -> List[str]:
        """
        Get file list from Git repository.
        
        Returns:
            List of file paths in repository
            
        Raises:
            subprocess.CalledProcessError: If git command fails
            FileNotFoundError: If git is not installed
        """
        try:
            # Execute git ls-tree to get file list
            result = subprocess.run(
                ["git", "ls-tree", "-r", "HEAD", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Split output by lines and remove empty lines
            files = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            print(f"✓ Found {len(files)} files in Git repository")
            return files
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git command error: {e.stderr}"
            print(f"✗ {error_msg}")
            raise
            
        except FileNotFoundError:
            error_msg = "Git is not installed or not found in PATH"
            print(f"✗ {error_msg}")
            raise

    def filter_files_by_extensions(self, files: List[str], extensions: Set[str]) -> List[str]:
        """
        Filter files by extensions.
        
        Args:
            files: List of file paths
            extensions: Set of extensions to filter by (e.g., {'.py', '.js'})
            
        Returns:
            Filtered file list
        """
        if not extensions:
            return files
            
        filtered_files = []
        for file_path in files:
            file_ext = Path(file_path).suffix.lower()
            if file_ext in extensions:
                filtered_files.append(file_path)
                
        print(f"✓ After extension filtering: {len(filtered_files)} files remaining")
        return filtered_files
    
    def filter_files_by_regex(self, files: List[str], regex: re.Pattern) -> List[str]:
        """
        Filter filenames by Regex.
        
        Args:
            files: List of file paths
            regex: Regex pattern
            
        Returns:
            Filtered file list
        """
        
        filtered_files = []
        for file_path in files:
            if not regex.match(file_path):
                filtered_files.append(file_path)
        
        print(f"✓ After Regex filtering: {len(filtered_files)} files remaining")
        return filtered_files

    def create_file_tree(self, files: List[str]) -> str:
        """
        Create file tree in readable format.
        
        Args:
            files: List of file paths
            
        Returns:
            String representation of file tree
        """
        print("📁 Creating file tree...")
        
        tree_lines = ["PROJECT STRUCTURE:", "=" * 50, ""]
        
        # Sort files for nice display
        sorted_files = sorted(files)
        
        # Group files by directories
        dirs = {}
        for file_path in sorted_files:
            path_parts = Path(file_path).parts
            
            # Process each nesting level
            current_dict = dirs
            for part in path_parts[:-1]:  # All parts except filename
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]
            
            # Add file
            filename = path_parts[-1]
            current_dict[filename] = None
        
        # Build tree recursively
        def build_tree(d: dict, prefix: str = "") -> List[str]:
            lines = []
            items = sorted(d.items())
            
            for i, (name, subdirs) in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                lines.append(f"{prefix}{current_prefix}{name}")
                
                if subdirs is not None:  # This is a directory
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    lines.extend(build_tree(subdirs, next_prefix))
                    
            return lines
        
        tree_lines.extend(build_tree(dirs))
        tree_lines.extend(["", "=" * 50, "", ""])
        
        return "\n".join(tree_lines)

    def read_file_safely(self, file_path: str) -> Optional[str]:
        """
        Safely read file with error handling.
        
        Args:
            file_path: File path
            
        Returns:
            File content or None in case of error
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                self.errors.append(f"File doesn't exist: {file_path}")
                return None
            
            # Try to read as text file with different encodings
            encodings = ['utf-8', 'cp1251', 'latin1', 'ascii']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                        content = f.read()
                        
                    # Check if file is not too large (> 1MB)
                    if len(content) > 1024 * 1024:
                        self.errors.append(f"File too large (>1MB): {file_path}")
                        return f"[FILE TOO LARGE - CONTENT SKIPPED]\nSize: {len(content)} characters"
                    
                    return content
                    
                except UnicodeDecodeError:
                    continue
                except UnicodeError:
                    continue
            
            # If couldn't read with any encoding - probably binary file
            self.errors.append(f"Binary file or unsupported encoding: {file_path}")
            return "[BINARY FILE OR UNSUPPORTED ENCODING]"
            
        except PermissionError:
            self.errors.append(f"No access rights to file: {file_path}")
            return "[NO FILE ACCESS RIGHTS]"
            
        except Exception as e:
            self.errors.append(f"Unexpected error reading {file_path}: {str(e)}")
            return f"[FILE READING ERROR: {str(e)}]"

    def process_files(self, files: List[str]) -> str:
        """
        Process file list and create unified text document.
        
        Args:
            files: List of file paths
            
        Returns:
            Content of all files in unified format
        """
        print(f"📄 Processing {len(files)} files...")
        
        content_parts = []
        separator = "=" * 80
        
        for i, file_path in enumerate(files, 1):
            print(f"  Processing ({i}/{len(files)}): {file_path}")
            
            # Read file content
            file_content = self.read_file_safely(file_path)
            
            if file_content is None:
                self.skipped_files += 1
                
                continue
            
            # Create file info block
            file_block = [
                separator,
                f"FILE: {file_path}",
                f"SIZE: {len(file_content)} characters",
                f"PROCESSED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                separator,
                "",
                file_content,
                "",
                ""
            ]
            
            content_parts.extend(file_block)
            self.processed_files += 1
        
        return "\n".join(content_parts)

    def create_header(self) -> str:
        """
        Create document header with meta information.
        
        Returns:
            Document header
        """
        current_dir = os.getcwd()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        header = f"""
Directory: {current_dir}
Creation date: {timestamp}
Created by: To LLM View {VERSION}

STATISTICS:
- Processed files: {self.processed_files}
- Skipped files: {self.skipped_files}
- Processing errors: {len(self.errors)}

{'=' * 80}

"""
        return header

    def create_footer(self) -> str:
        """
        Create document footer with error information.
        
        Returns:
            Document footer
        """
        footer_parts = [
            "=" * 80,
            "PROCESSING COMPLETE",
            "=" * 80,
            "",
            f"Total processed files: {self.processed_files}",
            f"Skipped files: {self.skipped_files}",
            f"Total errors: {len(self.errors)}",
            ""
        ]
        
        if self.errors:
            footer_parts.extend([
                "ERROR DETAILS:",
                "-" * 40,
                ""
            ])
            
            for error in self.errors:
                footer_parts.append(f"• {error}")
            
            footer_parts.append("")
        
        footer_parts.extend([
            f"Export completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80
        ])
        
        return "\n".join(footer_parts)

    def convert(self, extensions: Optional[Set[str]] = None, regex: Optional[re.Pattern] = None) -> None:
        """
        Perform full codebase conversion.
        
        Args:
            extensions: Set of extensions to filter by (e.g., {'.py', '.js'})
            regex: Regex pattern for filtering
        """
        try:
            print("🚀 Starting codebase converter...")
            
            # Get file list from Git
            files = self.get_git_files()
            
            # Filter
            if extensions:
                files = self.filter_files_by_extensions(files, extensions)
            
            if regex:
                files = self.filter_files_by_regex(files, regex)
            
            if not files:
                print("⚠️  No files to process after filtering")
                return
            
            # Create file tree
            file_tree = self.create_file_tree(files)
            
            # Process files
            files_content = self.process_files(files)
            
            # Build final document
            print(f"💾 Saving result to file: {self.output_file}")
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # Write header (after processing to include statistics)
                f.write(self.create_header())
                
                # Write file tree
                f.write(file_tree)
                
                # Write file contents
                f.write(files_content)
                
                # Write footer
                f.write(self.create_footer())
            
            print(f"✅ Conversion completed successfully!")
            print(f"   📄 Processed files: {self.processed_files}")
            print(f"   ⚠️  Skipped files: {self.skipped_files}")
            print(f"   📁 Result saved to: {self.output_file}")
            
            if self.errors:
                print(f"   ⚠️  Errors found: {len(self.errors)} (details in file)")
            
        except Exception as e:
            print(f"💥 Critical error: {str(e)}")
            sys.exit(1)


def parse_extensions(ext_string: str) -> Set[str]:
    """
    Parse file extensions string.
    
    Args:
        ext_string: String with extensions separated by commas (e.g., "py,js,html")
        
    Returns:
        Set of extensions with dots
    """
    if not ext_string:
        return set()
    
    extensions = set()
    for ext in ext_string.split(','):
        ext = ext.strip()
        if ext and not ext.startswith('.'):
            ext = '.' + ext
        if ext:
            extensions.add(ext.lower())
    
    return extensions


def main():
    """Main program function."""
    parser = argparse.ArgumentParser(
        description="Codebase converter to unified text document for working with neural networks",
        epilog="Example: python codebase_converter.py -o my_codebase.txt -w py,js,html"
    )
    
    parser.add_argument(
        '-o', '--output',
        default='codebase_export.txt',
        help='Output filename (default: codebase_export.txt)'
    )
    
    parser.add_argument(
        '-r', '--root',
        action='store_true',
        help='Create output file at the same level as current folder, not inside it'
    )
    
    parser.add_argument(
        '-w', '--whitelist',
        help='File extensions to include (comma separated, e.g.: py,js,html)'
    )
    
    parser.add_argument(
        '-rb', '--regex-blacklist',
        help='Regex for filename filtering'
    )
    
    args = parser.parse_args()
    
    # Parse extensions
    extensions = parse_extensions(args.whitelist) if args.whitelist else None
    
    if extensions:
        print(f"🔍 Filtering by extensions: {', '.join(sorted(extensions))}")
    
    
    regex = re.compile(args.regex_blacklist, re.IGNORECASE) if args.regex_blacklist else None
    
    if regex:
        print(f"🔍 Filtering by Regex: {args.regex_blacklist}")
    
    # Check if we're in a Git repository
    if not os.path.exists('.git'):
        print("❌ Error: current directory is not a Git repository")
        print("   Navigate to Git repository root and run the program again")
        return 1
    
    output_name = args.output
    root_path = None
    if args.root:
        p = os.getcwd()
        root_path = p[:p.rfind(os.sep)]
        
        output_name = p[p.rfind(os.sep)+len(os.sep):]+"."+output_name
    
    # Create and run converter
    converter = CodebaseConverter(output_name, root_path)
    converter.convert(extensions, regex)
    
    return 0


if __name__ == "__main__":
    main()