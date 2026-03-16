#!/usr/bin/env python
"""Debug script to run tests with proper setup."""

import os
import sys
import pytest

if __name__ == "__main__":
    # Add project root to path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Run tests
    sys.exit(pytest.main([
        "tests/",
        "-v",
        "--capture=no",
        "--asyncio-mode=auto"
    ]))