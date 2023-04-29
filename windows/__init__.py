"""Exports Windows related functionality. Each submodule contains a "library" class, which loads Windows internals and
exports methods that make use of said internals."""
# -- # Imports # ----------------------------------------------------------------------------------------------------- #
# Python
import sys as _sys

# -- # Constants # --------------------------------------------------------------------------------------------------- #
OS_IS_WINDOWS: bool = _sys.platform == 'win32'
