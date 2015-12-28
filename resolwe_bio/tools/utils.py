"""
Library of utility functions for writing tools.
"""

import gzip
import io


def gzopen(fname):
    """Open Gzip files using io.BufferedReader."""
    return io.TextIOWrapper(io.BufferedReader(gzip.open(fname)))


def escape_mongokey(key):
    """Escape keys when serializing database entries"""
    return key.replace('$', '\uff04').replace('.', '\uff0e').replace(' ', '_')
