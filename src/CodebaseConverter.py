#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Codebase File Getter module.

This module provides functionality to retrieve and filter files from a Git repository
for conversion to a unified text format.
"""

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


class CodebaseFileGetter:
    """
    Main class for retrieving files from Git repository with filtering capabilities.
    
    This class handles Git operations and provides various filtering methods
    to select specific files from the codebase.
    """
        
    def get_git_files(self) -> List[str]:
        """
        Get file list from Git repository.
        
        Uses 'git ls-tree' command to retrieve all files tracked by Git.
        
        Returns:
            List[str]: List of file paths in repository
            
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
            
            
            # Get new files
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                check=True
            )
            
            files.extend([line.strip() for line in result.stdout.split('\n') if line.strip()])
            
            
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
            List[str]: Filtered file list containing only files with specified extensions
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
        Filter filenames by Regex patterns.
        
        Applies both blacklist (exclude) and whitelist (include) regex filters.
        A file is included only if:
        - It doesn't match blacklist regex (if provided) AND
        - It matches whitelist regex (if provided)
        
        Args:
            files: List of file paths
            bregex: Regex pattern for blacklist (exclude) filtering
            wregex: Regex pattern for whitelist (include) filtering
            
        Returns:
            List[str]: Filtered file list
        """
        
        filtered_files = []
        for file_path in files:
            if 	(bregex is None or not bregex.match(file_path)) and \
                (wregex is None or wregex.match(file_path)):
                filtered_files.append(file_path)
        
        print(f"{Fore.LIGHTYELLOW_EX}✓ After Regex filtering: {Fore.LIGHTCYAN_EX}{len(filtered_files)} {Fore.LIGHTYELLOW_EX}files remaining{Style.RESET_ALL}")
        return filtered_files

    def convert(
        self, 
        extensions: Optional[Set[str]] = None, 
        bregex: Optional[re.Pattern] = None, 
        wregex: Optional[re.Pattern] = None
    ) -> List[str]:
        """
        Get list of files to convert with applied filters.
        
        Args:
            extensions: Set of extensions to filter by (e.g., {'.py', '.js'})
            bregex: Regex pattern for blacklist filtering
            wregex: Regex pattern for whitelist filtering
            
        Returns:
            List[str]: Filtered list of file paths
            
        Raises:
            SystemExit: If critical error occurs during processing
        """
        try:
            print(f"🚀 Starting codebase getter...")
            
            # Get file list from Git
            files = self.get_git_files()
            
            # Apply filters
            if extensions:
                files = self.filter_files_by_extensions(files, extensions)
            
            if bregex is not None or wregex is not None:
                files = self.filter_files_by_regex(files, bregex, wregex)
            
            return files
            
        except Exception as e:
            eprint(f"💥 Critical error: {str(e)}")
            sys.exit(1)