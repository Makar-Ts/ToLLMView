"""
Converter Interface Module.

This module defines the abstract base class for all converter implementations
used in the To LLM View application.
"""

from abc import ABC, abstractmethod
import argparse
from typing import List


class IConverter(ABC):
	"""
	Interface for file converters.
	
	All converter implementations must inherit from this class and implement
	the abstract methods defined here.
	"""

	@abstractmethod	
	def __init__(
		self,
		args: argparse.Namespace,
		output_file: str = "", 
		output_dir: str = None, 
	):
		"""
		Initialize converter with configuration.

		Args:
			args: Command line arguments namespace
			output_file: Output filename
			output_dir: Directory path where file will be saved
		"""
		self.args = args
		self.output_file = output_file
		self.output_dir = output_dir

	@abstractmethod
	def create(self, files: List[str]) -> None:
		"""
		Generate output document from file list.

		Args:
			files: List of filepaths to process
		"""


@abstractmethod
def help() -> str:
	"""
	Get help information for this converter.
	
	Returns:
		str: Help description
	"""
	return ""

@abstractmethod
def get_class() -> IConverter:
	"""
	Get the converter class.
	
	Returns:
		type: The converter class
	"""

@abstractmethod
def setup_args(parser: argparse.ArgumentParser) -> None:
	"""
	Setup command line arguments specific to this converter.
	
	Args:
		parser: Argument parser to add arguments to
	"""

@abstractmethod
def file_extention() -> str:
	"""Get output file's extention

	Returns:
		str: output file's extention
	"""
	return "txt"