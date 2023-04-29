"""Exports the "DialogLib" class, which wraps Common Item Dialog functionalities on Windows."""
# TODO - Review IUnknown pointers types.
# TODO - Reconsider dialog's owner window.
# -- # Imports # ----------------------------------------------------------------------------------------------------- #
# Python
import ctypes as ct
import ctypes.wintypes as wt
import pathlib as pl

# -- # Constants # --------------------------------------------------------------------------------------------------- #
# Parameter attributes for ctypes.
# # Flag 4 is poorly documented, do not use it.
_IN = 1
_OUT = 2


# Identifiers for COM services.
# # From ShObjIdl_core.h.
class _GUID(ct.Structure):
    _fields_ = [
        ("Data1", ct.c_ulong),
        ("Data2", ct.c_ushort),
        ("Data3", ct.c_ushort),
        ("Data4", ct.c_ubyte * 8)
    ]


_IID_CF = _GUID(0x00000001, 0x0000, 0x0000, (0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46))

_CID_FOD = _GUID(0xDC1C5A9C, 0xE88A, 0x4DDE, (0xA5, 0xA1, 0x60, 0xF8, 0x2A, 0x20, 0xAE, 0xF7))
_IID_FOD = _GUID(0xD57C7288, 0xD4AD, 0x4768, (0xBE, 0x02, 0x9D, 0x96, 0x95, 0x32, 0xD9, 0x60))

_CID_SI = _GUID(0x9AC9FBE1, 0xE0A2, 0x4AD6, (0xB4, 0xEE, 0xE2, 0x12, 0x01, 0x3E, 0xA9, 0x17))
_IID_SI = _GUID(0x43826D1E, 0xE718, 0x42EE, (0xBC, 0x55, 0xA1, 0xE2, 0x61, 0xC3, 0x7B, 0xFE))

# Virtual table function indexes for COM interfaces.
# # From ShObjIdl_core.h.
_VTI_CF_CREATE = 3
_VTI_CF_RELEASE = 2

_VTI_FOD_RELEASE = 2
_VTI_FOD_SHOW = 3
_VTI_FOD_SET_OPT = 9
_VTI_FOD_GET_OPT = 10
_VTI_FOD_SET_DIR = 12
_VTI_FOD_TITLE = 17
_VTI_FOD_OK_LABEL = 18
_VTI_FOD_RESULT = 20

_VTI_SI_RELEASE = 2
_VTI_SI_NAME = 5

# Flags and other constants used by Windows functions.
_CI_APARTMENT_THREADED = 0x02
_CI_DISABLE_OLE1DDE = 0x04

_CLS_CTX_INPROC_SERVER = 0x01

_FOS_PICK_FOLDERS = 0x20
_FOS_NO_CHANGE_DIR = 0x08
_FOS_FORCE_FILESYSTEM = 0x40

_SI_GDN_FILESYSTEM_PATH = 0x80058000

# Windows system error codes.
_WE_CANCELLED = 1223


# -- # Exceptions # -------------------------------------------------------------------------------------------------- #
class DialogLibError(OSError):
    """General exception for errors initializing the DialogLib class."""


class DLLNotFoundError(DialogLibError):
    """Raised when a DLL required by the DialogLib class cannot be obtained."""


class FunctionNotFoundError(DialogLibError):
    """Raised when a DLL function required by the DialogLib class cannot be obtained."""


# -- # Classes # ----------------------------------------------------------------------------------------------------- #
class DialogLib:
    """A "library" that loads the required internals and exports dialog-related functionality on Windows.

    I couldn't think of a better name for this.
    """
    # -- # Constructor # --------------------------------------------------------------------------------------------- #
    def __init__(self):
        """Initializes and loads all required DLLs and their functions that are used internally by this class's exported
        methods.

        Raises
        ------
        DLLNotFoundError
            If one of the necessary DLLs couldn't be located.

            This usually means that the OS isn't Windows, or that the Windows version is not supported.

        FunctionNotFoundError
            If one of the required internal functions couldn't be obtained.

            This usually means that the OS's version is not supported.
        """
        # Dialog interface status.
        self._dialog_loaded: bool = False
        self._dialog_class: wt.LPVOID | None = None

        # Get required Windows functions.
        try:
            # Get required DLLs.
            ole32dll = ct.OleDLL('Ole32.dll')
            shell32dll = ct.OleDLL('Shell32.dll')
        except FileNotFoundError as ex:
            raise DLLNotFoundError(f"""Could not obtain the necessary DLL: { ex.filename }.""") from ex

        try:
            # Get necessary functions.
            # # COM functions.
            self._CoInitializeEx = ct.WINFUNCTYPE(ct.HRESULT, wt.LPVOID, wt.DWORD)(
                ('CoInitializeEx', ole32dll),
                ((_IN, 'pvReserved'), (_IN, 'dwCoInit'))
            )
            self._CoGetClassObject = ct.WINFUNCTYPE(ct.HRESULT, _GUID, wt.DWORD, wt.LPVOID, _GUID,
                                                    ct.POINTER(wt.LPVOID))(
                ('CoGetClassObject', ole32dll),
                ((_IN, 'rclsid'), (_IN, 'dwClsContext'), (_IN, 'pvReserved'), (_IN, 'riid'), (_OUT, 'ppv'))
            )
            self._CoUninitialize = ct.WINFUNCTYPE(None)(
                ('CoUninitialize', ole32dll),
                ()
            )

            # # Shell functions.
            self._SHCreateItemFromParsingName = ct.WINFUNCTYPE(ct.HRESULT, wt.LPCWSTR, ct.POINTER(wt.LPVOID), _GUID,
                                                               ct.POINTER(wt.LPVOID))(
                ('SHCreateItemFromParsingName', shell32dll),
                ((_IN, 'pszPath'), (_IN, 'pbc'), (_IN, 'riid'), (_OUT, 'ppv'))
            )

            # # ClassFactory interface functions.
            self._IClassFactory_CreateInstance = ct.WINFUNCTYPE(ct.HRESULT, wt.LPVOID, _GUID, ct.POINTER(wt.LPVOID))(
                _VTI_CF_CREATE, 'CreateInstance',
                ((_IN, 'pUnkOuter'), (_IN, 'riid'), (_OUT, 'ppvObject'))
            )
            self._IClassFactory_Release = ct.WINFUNCTYPE(wt.ULONG)(
                _VTI_CF_RELEASE, 'Release',
                ()
            )

            # # FileOpenDialog interface functions.
            self._IFileOpenDialog_SetTitle = ct.WINFUNCTYPE(ct.HRESULT, wt.LPCWSTR)(
                _VTI_FOD_TITLE, 'SetTitle',
                ((_IN, 'pszTitle'),), ct.pointer(_IID_FOD)
            )
            self._IFileOpenDialog_SetOkButtonLabel = ct.WINFUNCTYPE(ct.HRESULT, wt.LPCWSTR)(
                _VTI_FOD_OK_LABEL, 'SetOkButtonLabel',
                ((_IN, 'pszText'),), ct.pointer(_IID_FOD)
            )
            self._IFileOpenDialog_SetFolder = ct.WINFUNCTYPE(ct.HRESULT, wt.LPVOID)(
                _VTI_FOD_SET_DIR, 'SetFolder',
                ((_IN, 'psi'),), ct.pointer(_IID_FOD)
            )
            self._IFileOpenDialog_GetOptions = ct.WINFUNCTYPE(ct.HRESULT, ct.POINTER(ct.c_ulong))(
                _VTI_FOD_GET_OPT, 'GetOptions',
                ((_OUT, 'pfos'),), ct.pointer(_IID_FOD)
            )
            self._IFileOpenDialog_SetOptions = ct.WINFUNCTYPE(ct.HRESULT, ct.c_ulong)(
                _VTI_FOD_SET_OPT, 'SetOptions',
                ((_IN, 'fos'),), ct.pointer(_IID_FOD)
            )
            self._IFileOpenDialog_Show = ct.WINFUNCTYPE(ct.HRESULT, wt.HWND)(
                _VTI_FOD_SHOW, 'Show',
                ((_IN, 'hwndOwner'),), ct.pointer(_IID_FOD)
            )
            self._IFileOpenDialog_GetResult = ct.WINFUNCTYPE(ct.HRESULT, ct.POINTER(wt.LPVOID))(
                _VTI_FOD_RESULT, 'GetResult',
                ((_OUT, 'ppsi'),), ct.pointer(_IID_FOD)
            )
            self._IFileOpenDialog_Release = ct.WINFUNCTYPE(wt.ULONG)(
                _VTI_FOD_RELEASE, 'Release',
                (), ct.pointer(_IID_FOD)
            )

            # # ShellItem interface functions.
            self._IShellItem_GetDisplayName = ct.WINFUNCTYPE(ct.HRESULT, ct.c_ulong, ct.POINTER(wt.LPWSTR))(
                _VTI_SI_NAME, 'GetDisplayName',
                ((_IN, 'sigdnName'), (_OUT, 'ppszName')), ct.pointer(_IID_SI)
            )
            self._IShellItem_Release = ct.WINFUNCTYPE(wt.ULONG)(
                _VTI_SI_RELEASE, 'Release',
                (), ct.pointer(_IID_SI)
            )
        except AttributeError as ex:
            raise FunctionNotFoundError(f"""Could not obtain the necessary function: { ex.name }.""") from ex

    # -- # Methods # ------------------------------------------------------------------------------------------------- #
    def load(self):
        """Initializes the internal Windows services that this class relies on.

        Remember to unload them before exiting the application.

        Raises
        ------
        ValueError
            If the dialog library instance is already loaded.

        OSError
            If the COM library cannot be initialized or if the Common Item Dialog class object cannot be obtained.

            See the __cause__ attribute for the raw Windows error.
        """
        # Validation.
        if self._dialog_loaded:
            raise ValueError("The dialog library is already loaded.")

        # COM initialization.
        try:
            self._CoInitializeEx(None, _CI_APARTMENT_THREADED | _CI_DISABLE_OLE1DDE)
        except OSError as ex:
            raise OSError("Could not initialize the COM library.") from ex

        # Get dialog class object.
        try:
            self._dialog_class = wt.LPVOID(self._CoGetClassObject(_CID_FOD, _CLS_CTX_INPROC_SERVER, None, _IID_CF))
        except OSError as ex:
            raise OSError("Could not get Common Item Dialog COM class object.") from ex
        else:
            self._dialog_loaded = True

    def unload(self):
        """Closes the internal Windows services that this class's dialog operations rely on.

        This must be called before exiting the application, otherwise said services will continue running, which may
        cause memory leaks and other issues.

        Raises
        ------
        ValueError
            If the class instance is already unloaded.
        """
        # Validation.
        if not self._dialog_loaded:
            raise ValueError("The dialog library is not loaded.")

        # Clear dialog class object.
        self._IClassFactory_Release(self._dialog_class)

        # COM uninitialization.
        self._CoUninitialize()

        self._dialog_class = None
        self._dialog_loaded = False

    def open_folder_dialog(
            self,
            title: str | None = None,
            ok_label: str | None = None,
            default_dir: pl.Path | None = None
    ) -> pl.Path | None:
        """Creates and displays a native open directory dialog under the Common Item Dialog interface in Windows.

        The Common Item Dialog interface has only been supported since Windows Vista. Attempting to use it in older
        Windows versions will fail.

        Parameters
        ----------
        title : str | None = None
            The dialog's title, or None to use a default title.

        ok_label : str | None = None
            The label on the dialog's OK button, or None to use a default label (usually "Open").

        default_dir : Path | None = None
            The directory that the dialog will first show when it's displayed, or None to use a default directory that
            is selected by Windows.

            If a Path is given, it will not be validated. Behavior in these cases is not documented, but Windows should
            sort itself out, likely using the same default folder as if None is passed. It's recommended that this
            parameter is validated before the method is called.

        Returns
        -------
        Path | None
            If the user cancelled the dialog, the return value is None. Otherwise, it's a Path.

            This method does the best it can to ensure the path is a valid and existing directory, but it's recommended
            to validate it still. Windows internally returns Shell Items representing the selected path, and there isn't
            enough documentation to guarantee that the converted path string is compatible with pathlib Paths.

        Raises
        ------
        ValueError
            If the dialog library hasn't been loaded.

        OSError
            If some problem occurs with the internal Windows services calls. There are too many to list.

            The raw Windows error will be in the __cause__.
        """
        # Validation.
        if not self._dialog_loaded:
            raise ValueError("The dialog library must first be loaded in order to use it's exported methods.")

        try:
            dialog = wt.LPVOID(self._IClassFactory_CreateInstance(self._dialog_class, None, _IID_FOD))
        except OSError as ex:
            raise OSError("Could not create dialog instance.") from ex
        else:
            try:
                # Dialog setup.
                if title is not None:
                    try:
                        self._IFileOpenDialog_SetTitle(dialog, title)
                    except OSError as ex:
                        raise OSError("Could not set dialog's title.") from ex

                if ok_label is not None:
                    try:
                        self._IFileOpenDialog_SetOkButtonLabel(dialog, ok_label)
                    except OSError as ex:
                        raise OSError("Could not set dialog's OK button label.") from ex

                if default_dir is not None:
                    try:
                        default_dir = wt.LPVOID(self._SHCreateItemFromParsingName(str(default_dir), None, _IID_SI))
                    except OSError as ex:
                        raise OSError("Could not create the shell item for the dialog's default directory.") from ex
                    else:
                        try:
                            try:
                                self._IFileOpenDialog_SetFolder(dialog, default_dir)
                            except OSError as ex:
                                raise OSError("Could not set dialog's default directory.") from ex
                        finally:
                            self._IShellItem_Release(default_dir)

                try:
                    flags = self._IFileOpenDialog_GetOptions(dialog)
                    flags |= _FOS_PICK_FOLDERS | _FOS_NO_CHANGE_DIR | _FOS_FORCE_FILESYSTEM
                    self._IFileOpenDialog_SetOptions(dialog, flags)
                except OSError as ex:
                    raise OSError("Could not set dialog configuration.") from ex

                # Show dialog.
                try:
                    self._IFileOpenDialog_Show(dialog, None)
                except OSError as ex:
                    if ex.winerror & 0xFFFF == _WE_CANCELLED:
                        # User selected nothing.
                        return None
                    else:
                        # Process exception like normal.
                        raise OSError("Unexpected error while showing dialog.") from ex

                # Retrieve path selected by the user.
                try:
                    shell_item = wt.LPVOID(self._IFileOpenDialog_GetResult(dialog))

                    try:
                        # Parse selected path and return it.
                        return pl.Path(self._IShellItem_GetDisplayName(shell_item, _SI_GDN_FILESYSTEM_PATH))
                    finally:
                        self._IShellItem_Release(shell_item)
                except OSError as ex:
                    raise OSError("Could not retrieve the selected directory.") from ex
            finally:
                self._IFileOpenDialog_Release(dialog)

    # -- # Properties # ---------------------------------------------------------------------------------------------- #
    @property
    def is_loaded(self) -> bool:
        """Whether the dialog functionalities are currently loaded and ready for use or not."""
        return self._dialog_loaded
