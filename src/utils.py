#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for To LLM View application.

This module provides various helper functions used throughout the application
for file processing, string manipulation, and system operations.
"""

from os import listdir
import os
import re
from typing import Any, List, Optional, Set

from colorama import Back, Fore, Style


def parse_extensions(ext_string: str) -> Set[str]:
	"""
	Parse file extensions string into a set of normalized extensions.
	
	Args:
		ext_string: String with extensions separated by commas (e.g., "py,js,html")
		
	Returns:
		Set[str]: Set of extensions with dots (e.g., {'.py', '.js', '.html'})
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


def eprint(content: Any, **kwargs) -> None:
	"""
	Print error message with colored background.
	
	Args:
		content: Content to print as error
		**kwargs: Additional arguments passed to print function
	"""
	print(Back.RED, content, Style.RESET_ALL, **kwargs)


def filler(cur: str, max_len: int, fill: Optional[str] = " ") -> str:
	"""
	Pad string to specified length with filler characters.
	
	Args:
		cur: Current string to pad
		max_len: Target length for the string
		fill: Character(s) to use for padding
		
	Returns:
		str: Padded string with specified length
	"""
	if len(cur) >= max_len: 
		return cur
	
	if fill is None or len(fill) == 0:
		fill = " "
	
	filler_length = max_len - len(cur)
	filler_string = (fill * filler_length)[:filler_length]
	
	return filler_string + cur


# Filesize unit correlations in bytes
filesize_correlations = {
	'b': 1,
	'kb': 1024,
	'mb': 1024 ** 2,
	'gb': 1024 ** 3,
	'tb': 1024 ** 4
}


def convert_filesize(inp: str) -> int:
	"""
	Convert human-readable filesize string to bytes.
	
	Supports units: b, kb, mb, gb, tb (case-insensitive)
	
	Args:
		inp: Filesize string (e.g., "1.5mb", "2kb", "500")
		
	Returns:
		int: Size in bytes
		
	Examples:
		>>> convert_filesize("1.5mb")
		1572864
		>>> convert_filesize("2kb") 
		2048
		>>> convert_filesize("500")
		500
	"""
	inp = inp.strip().lower()

	# if inp is a plain number
	if re.match(r'^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)$', inp):
		return int(inp)

	if re.match(r'^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)(b|kb|mb|gb|tb)$', inp):
		filesize = re.search(r'(b|kb|mb|gb|tb)$', inp)
		number = re.search(r'^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)', inp)

		if filesize is None or number is None:
			return filesize_correlations['mb']
		
		return round(float(number[0]) * filesize_correlations[filesize[0]])

	return filesize_correlations['mb']


def get_all_process_types(path: str, prefix: str = "") -> List[str]:
	"""
	Recursively discover all available converter types in converters directory.
	
	Args:
		path: Directory path to search for converters
		prefix: Prefix for nested package names
		
	Returns:
		List[str]: List of discovered converter type names
	"""
	processes = []
	
	for part in listdir(path):
		if part[0] == "_":
			continue
		
		if os.path.isfile(os.path.join(path, part)):
			if part.split(".")[-1] == "py":
				processes.append(prefix+part.split(".")[0])
		else:
			processes += get_all_process_types(os.path.join(path, part), prefix+part+".")
	
	return processes