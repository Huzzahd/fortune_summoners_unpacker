"""Exports the "TerminalLib" class, which wraps terminal-related functionalities on Windows."""
# TODO - Review last-error stuff.
# -- # Imports # ----------------------------------------------------------------------------------------------------- #
# Python
import ctypes as ct
import ctypes.wintypes as wt

# -- # Constants # --------------------------------------------------------------------------------------------------- #
# Parameter attributes for ctypes.
# # Flag 4 is poorly documented, do not use it.
_IN = 1
_OUT = 2

# Flags and other constants used by internal functions.
_STD_OUTPUT_HANDLE_CODE = wt.DWORD(-11)

_OUT_ENABLE_PROCESSING = 0x01
_OUT_ENABLE_VT_PROCESSING = 0x04


# -- # Exceptions # -------------------------------------------------------------------------------------------------- #
class TerminalLibError(OSError):
    """General exception class for errors in this module."""


class DLLNotFoundError(TerminalLibError):
    """Raised when a necessary DLL cannot be obtained."""


class FunctionNotFoundError(TerminalLibError):
    """Raised when a DLL's necessary function cannot be obtained."""


# -- # Classes # ----------------------------------------------------------------------------------------------------- #
class TerminalLib:
    """A "library" that loads the required internals and exports Windows terminal-related functionality.

    I couldn't find a better name for this.
    """
    # -- # Constructors # -------------------------------------------------------------------------------------------- #
    def __init__(self):
        """Initializes class and loads all DLLs and their functions required by methods exported by this class.

        Raises
        ------
        DLLNotFoundError
            If one of the necessary DLLs couldn't be located.

            This usually means that the OS isn't Windows, or that the Windows version is not supported.

        FunctionNotFoundError
            If one of the required internal functions couldn't be obtained.

            This usually means that the OS's version is not supported.
        """
        # Get required Windows functions.
        try:
            # Get necessary DLLs.
            kernel32dll = ct.WinDLL(name='Kernel32.dll', use_last_error=True)
        except FileNotFoundError as ex:
            raise DLLNotFoundError(f"""Could not obtain the necessary DLL: "{ ex.filename }".""") from ex

        try:
            # Obtain necessary functions.
            self._GetStdHandle = ct.WINFUNCTYPE(wt.HANDLE, wt.DWORD, use_last_error=True)(
                ('GetStdHandle', kernel32dll),
                ((_IN, 'nStdHandle'),)
            )
            self._GetConsoleMode = ct.WINFUNCTYPE(wt.BOOL, wt.HANDLE, wt.LPDWORD, use_last_error=True)(
                ('GetConsoleMode', kernel32dll),
                ((_IN, 'hConsoleHandle'), (_OUT, 'lpMode'))
            )
            self._SetConsoleMode = ct.WINFUNCTYPE(wt.BOOL, wt.HANDLE, wt.DWORD, use_last_error=True)(
                ('SetConsoleMode', kernel32dll),
                ((_IN, 'hConsoleHandle'), (_IN, 'dwMode'))
            )
        except AttributeError as ex:
            raise FunctionNotFoundError(f"""Could not obtain the necessary function: "{ ex.name }".""") from ex

    # -- # Methods # ------------------------------------------------------------------------------------------------- #
    def enable_ansi_terminal(self):
        """Enables Virtual Terminal processing in Windows computers, allowing for ANSI escape sequences to be parsed
        when printing to the standard output.

        Raises
        ------
        RuntimeError
            If the application does not have a standard output.

        OSError
            If the function fails due to an issue with the internal Windows's calls, such as the OS's Windows version
            not supporting terminal handling or Virtual Terminals, if the application's terminal does not support
            Virtual Terminal processing or for some other unexpected reason.

            Inspect the exception's __cause__ for more information.
        """
        console = self._GetStdHandle(_STD_OUTPUT_HANDLE_CODE)
        if ct.GetLastError() != 0:
            raise OSError("Could not retrieve handle to standard output.") from ct.WinError()

        if console == 0:
            raise RuntimeError("Application does not have a standard output.")

        console_mode = self._GetConsoleMode(console)
        if ct.GetLastError() != 0:
            raise OSError("Could not get standard output mode information.") from ct.WinError()

        console_mode |= _OUT_ENABLE_PROCESSING | _OUT_ENABLE_VT_PROCESSING

        self._SetConsoleMode(console, console_mode)
        if ct.GetLastError() != 0:
            raise OSError("Could not set standard output mode information.") from ct.WinError()
