#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Optional
from datetime import datetime
import re
from colorama import Fore, Back, Style

from info import VERSION
from src.utils import eprint, filler


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
            
            print(f"{Fore.LIGHTGREEN_EX}✓ Found {Fore.LIGHTBLUE_EX}{len(files)} {Fore.LIGHTGREEN_EX}files in Git repository{Style.RESET_ALL}")
            return files
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git command error: {e.stderr}"
            eprint(f"✗ {error_msg}")
            raise
            
        except FileNotFoundError:
            error_msg = "Git is not installed or not found in PATH"
            eprint(f"✗ {error_msg}")
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
                
        print(f"{Fore.LIGHTYELLOW_EX}✓ After extension filtering: {Fore.LIGHTMAGENTA_EX}{len(filtered_files)} {Fore.LIGHTYELLOW_EX}files remaining{Style.RESET_ALL}")
        return filtered_files
    
    def filter_files_by_regex(self, files: List[str], bregex: Optional[re.Pattern], wregex: Optional[re.Pattern]) -> List[str]:
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
            if 	(bregex is None or not bregex.match(file_path)) and \
                (wregex is None or wregex.match(file_path)):
                filtered_files.append(file_path)
        
        print(f"{Fore.LIGHTYELLOW_EX}✓ After Regex filtering: {Fore.LIGHTCYAN_EX}{len(filtered_files)} {Fore.LIGHTYELLOW_EX}files remaining{Style.RESET_ALL}")
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
        print(f"📄 Processing {Fore.LIGHTBLUE_EX}{len(files)} {Style.RESET_ALL}files...")
        
        content_parts = []
        separator = "=" * 80
        files_amount = len(files)
        
        for i, file_path in enumerate(files, 1):
            print(f"  {Fore.LIGHTGREEN_EX}Processing ({filler(str(i), len(str(files_amount)), '_')}/{files_amount}): {Fore.LIGHTBLUE_EX}{file_path}{Style.RESET_ALL}")
            
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

    def convert(self, extensions: Optional[Set[str]] = None, bregex: Optional[re.Pattern] = None, wregex: Optional[re.Pattern] = None) -> None:
        """
        Perform full codebase conversion.
        
        Args:
            extensions: Set of extensions to filter by (e.g., {'.py', '.js'})
            bregex: Regex pattern for blacklist filtering
            wregex: Regex pattern for whitelist filtering
        """
        try:
            print(f"🚀 Starting codebase converter...")
            
            # Get file list from Git
            files = self.get_git_files()
            
            # Filter
            if extensions:
                files = self.filter_files_by_extensions(files, extensions)
            
            if bregex is not None or wregex is not None:
                files = self.filter_files_by_regex(files, bregex, wregex)
            
            if not files:
                eprint("⚠️  No files to process after filtering")
                return
            
            # Create file tree
            file_tree = self.create_file_tree(files)
            
            # Process files
            files_content = self.process_files(files)
            
            # Build final document
            print(f"💾 Saving result to file: {Fore.LIGHTCYAN_EX}{self.output_file}{Style.RESET_ALL}")
            
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
            print(f"   {Fore.GREEN}📄 Processed files: {Fore.LIGHTCYAN_EX}{self.processed_files}")
            print(f"   {Fore.RED  }⚠️ Skipped files:   {Fore.LIGHTCYAN_EX}{self.skipped_files}")
            print(f"   {Fore.CYAN }📁 Result saved to: {Fore.LIGHTCYAN_EX}{self.output_file}{Style.RESET_ALL}")
            
            if self.errors:
                eprint(f"   ⚠️  Errors found: {len(self.errors)} (details in file)")
            
        except Exception as e:
            eprint(f"💥 Critical error: {str(e)}")
            sys.exit(1)