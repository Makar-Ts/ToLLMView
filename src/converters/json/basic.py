"""
Bulk Text Converter Module.

This module provides functionality to convert a codebase into a single
bulk text file with structured formatting for LLM consumption.
"""

import argparse
import json
import os
import sys

from pathlib import Path
from typing import List, Set, Optional
from datetime import datetime
from colorama import Fore, Style
from src.converters._IConverter import IConverter

from src.info import VERSION
from src.utils import convert_filesize, eprint, filler


def help() -> str:
    return "Converts codebase to a single json file."


def get_class() -> type:
    return SlimTextConverter


def setup_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '-mf', '--max-filesize',
        help='Maximum filesize to include (float, e.g.: 1.1mb, 2kb, 1.444gb, etc.)'
    )

    # parser.add_argument(
    #     '-hr', '--human-readable',
    #     help='Is json must be human readable'
    # )


def file_extention() -> str:
    return "json"


class SlimTextConverter(IConverter):
    """
    Codebase to json converter.
    
    Converts multiple code files into a single structured json
    with file trees, metadata, and formatted content.
    """

    def __init__(
        self, 
        args: argparse.Namespace,
        output_file: str = "codebase_export.json", 
        output_dir: str = None, 
    ):
        """
        Initialize json converter.
        
        Args:
            args: Command line arguments
            output_file: Output filename
            output_dir: Output directory path
        """
        
        if output_dir is not None:
            self.output_file = output_dir + os.sep + output_file
        else:
            self.output_file = output_file

        self.processed_files = 0
        self.skipped_files = 0
        self.errors = []

        self.max_filesize = convert_filesize(args.max_filesize) if args.max_filesize else 1024 ** 2
        print(f"{Fore.GREEN}🔍 | max filesize (B) |{Style.RESET_ALL}")
        print(f"{Fore.LIGHTCYAN_EX}🔍 | {self.max_filesize: 16}{Style.RESET_ALL} |")

    def create(self, files: List[str]) -> None:
        """
        Create json output from file list.
        
        Args:
            files: List of file paths to process
            
        Raises:
            SystemExit: If critical error occurs during file creation
        """
        try:
            # Create file tree
            file_tree = self.create_file_tree(files)
            
            # Process files
            files_content = self.process_files(files)
            
            # Build final document
            print(f"💾 | {Fore.LIGHTCYAN_EX}{self.output_file}{Style.RESET_ALL}")
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "header": self.create_header(),
                    "tree": file_tree,
                    "files": files_content,
                    "footer": self.create_footer()
                }, f, indent=None)
            
            print(f"{Fore.LIGHTBLUE_EX}✅ | processed | skipped |{Style.RESET_ALL}")
            print(f"   | {Fore.GREEN}{self.processed_files: 9} | {Fore.RED}{self.skipped_files: 7} |{Style.RESET_ALL}")
            print(f"📁 | {Fore.LIGHTCYAN_EX}{self.output_file}{Style.RESET_ALL}\n")
            
            if self.errors:
                eprint("⚠️ | errors")
                eprint(f"⚠️ | {len(self.errors)} (details in file)")
            
        except Exception as e:
            eprint(f"💥 Critical error: {str(e)}")
            sys.exit(1)
    
    def create_file_tree(self, files: List[str]) -> dict:
        """
        Create file tree in readable format.
        
        Args:
            files: List of file paths
            
        Returns:
            String representation of file tree
        """
        print("📁 | file tree gen...")

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
        def build_tree(d: dict) -> list:
            lines = []
            items = sorted(d.items())
            
            for i, (name, subdirs) in enumerate(items):
                if subdirs is not None: 
                    lines.append({ 
                        "dir": name,
                        "files": build_tree(subdirs),
                    })
                else:
                    lines.append(name)
                    
            return lines

        return build_tree(dirs)

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
                    # Check if file is not too large (> 1MB)
                    filesize = os.path.getsize(file_path)
                    
                    if filesize > self.max_filesize:
                        self.errors.append(f"File too large (>{self.max_filesize} Bytes): {file_path}")
                        return f"[TOO LARGE {filesize} B, SKIP]"
                    
                    with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                        content = f.read()
                    
                    return content
                    
                except UnicodeDecodeError:
                    continue
                except UnicodeError:
                    continue
            
            # If couldn't read with any encoding - probably binary file
            self.errors.append(f"Binary file or unsupported encoding: {file_path}")
            return "[UNSUPPORTED ENCODING]"
            
        except PermissionError:
            self.errors.append(f"No access rights to file: {file_path}")
            return "[NO ACCESS]"
            
        except Exception as e:
            self.errors.append(f"Unexpected error reading {file_path}: {str(e)}")
            return f"[READING ERROR: {str(e)}]"

    def process_files(self, files: List[str]) -> dict:
        """
        Process file list and create unified text document.
        
        Args:
            files: List of file paths
            
        Returns:
            Content of all files in unified format
        """
        print(f"   | {Fore.LIGHTBLUE_EX}files{Style.RESET_ALL} |")
        print(f"   | {Fore.LIGHTGREEN_EX}{len(files): 5}{Style.RESET_ALL} |")
        
        output = {}
        files_amount = len(files)
        
        for i, file_path in enumerate(files, 1):
            print(f"{Fore.LIGHTGREEN_EX}📄 | {filler(str(i), len(str(files_amount)), ' ')}/{files_amount} | {Fore.LIGHTBLUE_EX}{file_path}{Style.RESET_ALL}")
            
            # Read file content
            file_content = self.read_file_safely(file_path)
            
            if file_content is None:
                self.skipped_files += 1
                
                continue

            output[file_path] = {
                "path": file_path,
                "len": len(file_content),
                "content": file_content,
            }

            self.processed_files += 1
        
        return output

    def create_header(self) -> dict:
        """
        Create document header with meta information.
        
        Returns:
            Document header
        """
        current_dir = os.getcwd()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            "by": f"To LLM View {VERSION}",
            "dir": current_dir,
            "date": timestamp,
            "info": {
                "processed": self.processed_files,
                "skipped": self.skipped_files,
                "errors": len(self.errors)
            }
        }

    def create_footer(self) -> dict:
        """
        Create document footer with error information.
        
        Returns:
            Document footer
        """
        output = {}
        
        if self.errors:
            output["errors"] = []
            
            for error in self.errors:
                output["errors"].append(error)
        
        return output
