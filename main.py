#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import re

from colorama import Fore, Back, Style

from src.CodebaseConverter import CodebaseConverter
from src.utils import convert_filesize, eprint, parse_extensions



def main():
    """Main program function."""
    parser = argparse.ArgumentParser(
        description="Codebase converter to unified text document for working with neural networks",
        epilog='Example: to-llm-view -r -rb "(^\.)|(^tsconfig)" -rw ".*\.component\..*" -o output.txt -mf 4kb'
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
        help='File extensions to include (comma separated, e.g.: py,js,html). I recommend using --regex-whitelsit instead.'
    )
    
    
    parser.add_argument(
        '-rb', '--regex-blacklist',
        help='Regex for blacklist filename filtering'
    )
    
    parser.add_argument(
        '-rw', '--regex-whitelist',
        help='Regex for whitelist filename filtering'
    )
    
    
    parser.add_argument(
        '-mf', '--max-filesize',
        help='Maximum filesize to include (float, e.g.: 1.1mb, 2kb, 1.444gb, etc.)'
    )
    
    
    args = parser.parse_args()
    
    # Parse extensions
    extensions = parse_extensions(args.whitelist) if args.whitelist else None
    
    if extensions:
        print(f"🔍 {Fore.GREEN}Filtering by extensions: {Fore.LIGHTMAGENTA_EX}{', '.join(sorted(extensions))}{Style.RESET_ALL}")
    
    
    bregex = re.compile(args.regex_blacklist, re.IGNORECASE) if args.regex_blacklist else None
    
    if bregex:
        print(f"🔍 {Fore.GREEN}Filtering by blacklist Regex: {Fore.LIGHTCYAN_EX}{args.regex_blacklist}{Style.RESET_ALL}")
        
    
    wregex = re.compile(args.regex_whitelist, re.IGNORECASE) if args.regex_whitelist else None
    
    if wregex:
        print(f"🔍 {Fore.GREEN}Filtering by whitelist Regex: {Fore.LIGHTCYAN_EX}{args.regex_whitelist}{Style.RESET_ALL}")
    
    
    max_filesize = convert_filesize(args.max_filesize) if args.max_filesize else 1024 ** 2
    print(f"🔍 {Fore.GREEN}Maximum filesize set to: {Fore.LIGHTCYAN_EX}{max_filesize} Bytes{Style.RESET_ALL}")
    
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
    converter = CodebaseConverter(output_name, root_path, max_filesize)
    converter.convert(extensions, bregex, wregex)
    
    return 0


if __name__ == "__main__":
    main()
