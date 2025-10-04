#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import re

from colorama import Fore, Back, Style

from src.CodebaseConverter import CodebaseConverter
from src.utils import eprint, parse_extensions



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
        print(f"🔍 {Fore.GREEN}Filtering by extensions: {Fore.LIGHTMAGENTA_EX}{', '.join(sorted(extensions))}{Style.RESET_ALL}")
    
    
    regex = re.compile(args.regex_blacklist, re.IGNORECASE) if args.regex_blacklist else None
    
    if regex:
        print(f"🔍 {Fore.GREEN}Filtering by Regex: {Fore.LIGHTCYAN_EX}{args.regex_blacklist}{Style.RESET_ALL}")
    
    # Check if we're in a Git repository
    if not os.path.exists('.git'):
        eprint("❌ Error: current directory is not a Git repository")
        eprint("   Navigate to Git repository root and run the program again")
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
