#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main entry point for To LLM View application.

This module handles command line arguments, initializes the appropriate converter,
and coordinates the codebase conversion process.
"""

import importlib
import os
import argparse
from pathlib import Path
import re
import sys

from colorama import Fore, Back, Style

import src.converters._IConverter as IConverter
from src.CodebaseConverter import CodebaseFileGetter
from src.utils import convert_filesize, eprint, get_all_process_types, parse_extensions

def main():
    """
    Main program function.
    
    Handles command line argument parsing, converter selection, and execution
    of the codebase conversion process.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    
    parser = argparse.ArgumentParser(
        description="Codebase converter to unified text document for working with neural networks",
        epilog='Example: to-llm-view -r -rb "(^\.)|(^tsconfig)" -rw ".*\.component\..*" -o output.txt -mf 4kb',
        add_help=False,
    )
    
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help="Show help message"
    )
    
    parser.add_argument(
        '-o', '--output',
        default='codebase_export',
        help='Output filename (default: codebase_export)'
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
    
    converters_types = get_all_process_types(os.path.join(Path(__file__).parent, "converters"))
    
    parser.add_argument(
        '-c', '--converter',
        default="txt.bulk" if "txt.bulk" in converters_types else converters_types[0],
        help=f"Converter to use. Currently available: {', '.join(converters_types)}"
    )
    
    pre_args = parser.parse_known_args()[0]
    
    if not pre_args.help and pre_args.converter not in converters_types:
        print("Invalid process_type!")
        print("Available process types:")
        
        for converter_type in converters_types:
            module = importlib.import_module("src.converters." + converter_type)
            print(f" - {converter_type}")
            print(f"    {module.help()}")
        
        return 1
        
    if pre_args.converter in converters_types:
        converter: IConverter = importlib.import_module("src.converters." + pre_args.converter)
        converter.setup_args(parser)
    
    args = parser.parse_args()
    
    if args.help:
        parser.print_help()
        
        return 0
    
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
    
    
    # Check if we're in a Git repository
    if not os.path.exists('.git'):
        eprint("❌ Error: current directory is not a Git repository")
        eprint("   Navigate to Git repository root and run the program again")
        return 1
    
    output_name = args.output + "." + converter.file_extention()
    root_path = None
    if args.root:
        p = os.getcwd()
        root_path = p[:p.rfind(os.sep)]
        
        output_name = p[p.rfind(os.sep)+len(os.sep):]+"."+output_name
    
    # Create and run converter
    getter = CodebaseFileGetter()
    files = getter.convert(extensions, bregex, wregex)
    
    
    cclass: IConverter.IConverter = converter.get_class()(
        args,
        output_name,
        root_path
    )
    cclass.create(files)
    
    
    return 0


if __name__ == "__main__":
    main()
