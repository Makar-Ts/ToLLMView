import argparse
import os
import sys

from pathlib import Path
from typing import List, Set, Optional
from datetime import datetime
from colorama import Fore, Style
from src.converters._IConverter import IConverter

from info import VERSION
from src.utils import convert_filesize, eprint, filler


def help():
	return ""

def get_class():
	return BulkTextConverter

def setup_args(parser: argparse.ArgumentParser):
	parser.add_argument(
		'-mf', '--max-filesize',
		help='Maximum filesize to include (float, e.g.: 1.1mb, 2kb, 1.444gb, etc.)'
	)

class BulkTextConverter(IConverter):
	"""Codebase to bulk text"""

	def __init__(
		self, 
		args: argparse.Namespace,
		output_file: str = "codebase_export.txt", 
		output_dir: str = None, 
	):
		if output_dir is not None:
			self.output_file = output_dir + os.sep + output_file
		else:
			self.output_file = output_file

		self.processed_files = 0
		self.skipped_files = 0
		self.errors = []

		self.max_filesize = convert_filesize(args.max_filesize) if args.max_filesize else 1024 ** 2
		print(f"🔍 {Fore.GREEN}Maximum filesize set to: {Fore.LIGHTCYAN_EX}{self.max_filesize} Bytes{Style.RESET_ALL}")

	def create(self, files):
		try:
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
					next_prefix = prefix + ("	" if is_last else "│   ")
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
					# Check if file is not too large (> 1MB)
					filesize = os.path.getsize(file_path)
					
					if filesize > self.max_filesize:
						self.errors.append(f"File too large (>{self.max_filesize} Bytes): {file_path}")
						return f"[FILE TOO LARGE - CONTENT SKIPPED]\nSize: {filesize} Bytes"
					
					with open(file_path, 'r', encoding=encoding, errors='strict') as f:
						content = f.read()
					
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