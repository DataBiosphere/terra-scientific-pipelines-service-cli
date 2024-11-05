"""
Terralab: A CLI for the Terra Scientific Pipelines Service (Teaspoons).

This package provides a command-line interface to interact with the Teaspoons service,
built on top of an autogenerated thin client.
"""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("terralab-cli")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

__author__ = "Terra Scientific Services"
__email__ = "teaspoons-developers@broadinstitute.org"
