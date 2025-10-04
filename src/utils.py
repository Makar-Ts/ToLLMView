#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, List, Set

from colorama import Back, Fore, Style


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


def eprint(content: List[Any], **args):
    """
    Print error message
    
    Args:
		content: any data
		**args: same as `print` function
    """
    print(Back.RED, content, Style.RESET_ALL, **args)