#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import os
import argparse
import re

from colorama import Fore, Back, Style

from src.converters._IConverter import IConverter
from src.CodebaseConverter import CodebaseFileGetter
from src.utils import convert_filesize, eprint, get_all_process_types, parse_extensions



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
    
    converters_types = get_all_process_types(os.path.join(os.getcwd(), "src", "converters"))
    
    parser.add_argument(
        '-c', '--converter',
        default=converters_types[0],
        help=f"Converter to use. Currently available: {', '.join(converters_types)}"
    )
    
    pre_args = parser.parse_known_args()[0]
    
    if pre_args.converter not in converters_types:
        print("Invalid process_type!")
        print("Available process types:")
        
        for converter_type in converters_types:
            module = importlib.import_module("src.converters." + converter_type)
            print(f" - {converter_type}")
            print(f"    {module.help()}")
        
        return 1
    
    converter = importlib.import_module("src.converters." + pre_args.converter)
    converter.setup_args(parser)
    
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
    getter = CodebaseFileGetter()
    files = getter.convert(extensions, bregex, wregex)
    
    
    cclass: IConverter = converter.get_class()(
        args,
        output_name,
        root_path
    )
    cclass.create(files)
    
    
    return 0


if __name__ == "__main__":
    main()
