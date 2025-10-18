from abc import ABC, abstractmethod
import argparse
from typing import List

class IConverter(ABC):
	"""Interface for file converter"""

	def __init__(
		self,
		args: argparse.Namespace,
		output_file: str = "", 
		output_dir: str = None, 
	):
		"""Initialize converter

		Args:
			output_file (str): Output filename
            output_dir: Directory path where file will be saved
		"""

	@abstractmethod
	def create(self, files: List[str]): 
		"""Generate output

		Args:
			files (List[str]): List of filepaths
		"""
