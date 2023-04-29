# TODO - List dependency versions.
# TODO - Review top comment launch mode thingy.
# TODO - Docstrings.

# -- # Imports # ----------------------------------------------------------------------------------------------------- #
# Python
import argparse as ap  # Python version 3.2
import atexit
import enum
import pathlib as pl  # Python version 3.4
import sys
# Project
import unpacker
import windows.dialog
import windows.terminal

# -- # Constants # --------------------------------------------------------------------------------------------------- #
PROGRAM_NAME = "Fortune Summoners Unpacker"
PROGRAM_VER = "2.0.0"
PROGRAM_URL = "https://github.com/Huzzahd/fortune_summoners_unpacker"
DISCORD_URL = "https://discord.gg/N68c7pt"
PILLOW_URL = "https://pypi.org/project/Pillow/"

# # Text-formatting codes.
_T_RESET = "\x1B[m"

_TF_BOLD = "\x1B[1m"
_TF_UNDER = "\x1B[4m"
_TF_NEG = "\x1B[7m"
_TF_NO_BOLD = "\x1B[22m"
_TF_NO_UNDER = "\x1B[24m"
_TF_NO_NEG = "\x1B[27m"

_TC_BLACK = "\x1B[30m"
_TC_RED = "\x1B[31m"
_TC_GREEN = "\x1B[32m"
_TC_YELLOW = "\x1B[33m"
_TC_BLUE = "\x1B[34m"
_TC_MAGENTA = "\x1B[35m"
_TC_CYAN = "\x1B[36m"
_TC_WHITE = "\x1B[37m"


# -- # Enumerations # ------------------------------------------------------------------------------------------------ #
class Action(enum.IntEnum):
    UNPACK = 1, ".bmp"
    PACK = 2, ".bin"

    # Enum construction with additional fields.
    def __new__(cls, value: int, *_):
        obj = int.__new__(cls, value)
        obj._value_ = value
        return obj

    def __init__(self, _, extension: str) -> None:
        self.extension: str = extension

    # -- # Magic Methods # ------------------------------------------------------------------------------------------- #
    def __str__(self) -> str:
        return self.name.lower().capitalize()


# -- # Functions # --------------------------------------------------------------------------------------------------- #
def make_os_err_msg(error: OSError) -> str:
    """Auxiliary function that creates customized error messages from OS errors."""
    if hasattr(ex, 'winerror'):
        return f"""Windows Error #{ error.winerror } - { error.strerror }."""
    else:
        return f"""System Error #{ error.errno } - { error.strerror }."""


# -- # Script # ------------------------------------------------------------------------------------------------------ #
if __name__ == '__main__':
    # -- # Preparation # --------------------------------------------------------------------------------------------- #
    # Do not print anything until the startup message has been displayed.
    print_queue: list[str] = list()

    # Command-line parser setup.
    arg_parser = ap.ArgumentParser(
        prog=PROGRAM_NAME,
        description=(
            "Performs various operations on image resource files from the game"
            "「Fortune Summoners - Secret of the Elemental Stone」"
        ),
        epilog="For more information please see the readme file.",
        add_help=False,
        allow_abbrev=False
    )

    arg_parser.add_argument(
        'input-paths', nargs='*',
        help="Files and/or folders whose files will be processed."
    )
    arg_parser.add_argument(
        '-o', '--output-dir', nargs='?',
        help="Directory in which the output files will be saved."
    )
    arg_parser.add_argument(
        '-a', '--action', nargs='?',
        help="How to process the input files."
    )
    arg_parser.add_argument(
        '-i', '--interactive', action='store_true',
        help="[Windows-only] Allows parameters to be passed during execution via graphic interfaces."
    )
    arg_parser.add_argument(
        '-x', '--overwrite', action='store_true',
        help="Overwrite existing files when saving output files."
    )
    arg_parser.add_argument(
        '-s', '--skip', action='store_true',
        help="Skip the confirmation prompt before file processing begins."
    )
    arg_parser.add_argument(
        '-d', '--debug', action='store_true',
        help="Display additional debug information when available."
    )
    arg_parser.add_argument(
        '-c', '--colors', action='store_true',
        help="[Windows-only] Enables colored output on the terminal."
    ),
    arg_parser.add_argument(
        '-h', '--help', action='help',
        help="Displays information on how to use this program."
    )
    arg_parser.add_argument(
        '-v', '--version', action='version',
        version=f"""{ PROGRAM_NAME } v{ PROGRAM_VER }""",
        help="Displays version info about the program."
    )

    # Parse command-line parameters.
    # # I don't like how argparse will raise indistinguishable errors, but it's too much work for now.
    # # Some things can go wrong if parameters are passed a certain way and I have no control over them.
    args = vars(arg_parser.parse_args())

    # # Simple arguments that require no validation.
    opt_debug: bool = args['debug']
    opt_overwrite: bool = args['overwrite']
    opt_skip: bool = args['skip']

    # # Enable colors.
    opt_colors: bool = args['colors']
    ansi_enabled: bool = False

    # # # Define colored output printing mechanism.
    def a(text: str) -> str:
        """Shortcut to display or hide text based on ANSI Virtual Terminal Sequences being enabled."""
        return text if ansi_enabled else ""

    if opt_colors:
        try:
            terminal_lib = windows.terminal.TerminalLib()
        except Exception as ex:
            if windows.OS_IS_WINDOWS:
                print_queue.append(
                    "Colors mode is not supported on non-Windows operating systems."
                )
            else:
                print_queue.append(
                    "Colors mode is not supported on non-Windows operating systems."
                )

            if opt_debug:
                print_queue.append(
                    str(ex)
                )

                if ex.__cause__ is not None:
                    print_queue.append(
                        str(ex.__cause__)
                    )
        else:
            try:
                terminal_lib.enable_ansi_terminal()
            except Exception as ex:
                print_queue.append(
                    "Could not enable colors mode on this terminal."
                )

                if opt_debug:
                    print_queue.append(
                        str(ex)
                    )

                    if ex.__cause__ is not None:
                        print_queue.append(
                            str(ex.__cause__)
                        )
            else:
                ansi_enabled = True

                print_queue.append(" ".join((
                    "Colors enabled!   ",
                    a(_TF_BOLD) + "Bold" + a(_T_RESET),
                    a(_TF_UNDER) + "Underlined" + a(_T_RESET),
                    a(_TF_NEG) + "Negative" + a(_T_RESET),
                    a(_TC_WHITE) + "White" + a(_T_RESET),
                    a(_TC_RED) + "Red" + a(_T_RESET),
                    a(_TC_GREEN) + "Green" + a(_T_RESET),
                    a(_TC_BLUE) + "Blue" + a(_T_RESET),
                    a(_TC_CYAN) + "Cyan" + a(_T_RESET),
                    a(_TC_YELLOW) + "Yellow" + a(_T_RESET),
                    a(_TC_MAGENTA) + "Magenta" + a(_T_RESET),
                    a(_TC_BLACK) + "Black" + a(_T_RESET)
                )))

    # # Enable interactive mode.
    opt_interactive: bool = args['interactive']
    dialog_lib: windows.dialog.DialogLib | None = None

    if opt_interactive:
        try:
            dialog_lib = windows.dialog.DialogLib()
        except windows.dialog.DialogLibError as ex:
            if windows.OS_IS_WINDOWS:
                print_queue.append(
                    a(_TC_RED) + "Interactive mode is not supported on non-Windows operating systems." + a(_T_RESET)
                )
            else:
                print_queue.append(
                    a(_TC_RED) + "Your Windows's version does not support interactive mode." + a(_T_RESET)
                )

            if opt_debug:
                print_queue.append(
                    a(_TC_MAGENTA) + str(ex) + a(_T_RESET)
                )

                if ex.__cause__ is not None:
                    print_queue.append(
                        a(_TC_MAGENTA) + str(ex.__cause__) + a(_T_RESET)
                    )
        else:
            try:
                dialog_lib.load()
            except OSError as ex:
                print_queue.append(
                    a(_TC_RED) + "Failed to initialize services required for dialog functionalities." + a(_T_RESET)
                )

                if opt_debug:
                    print_queue.append(
                        a(_TC_MAGENTA) + str(ex) + a(_T_RESET)
                    )

                    if ex.__cause__ is not None:
                        print_queue.append(
                            a(_TC_MAGENTA) + str(ex.__cause__) + a(_T_RESET)
                        )
            else:
                # Debug information.
                if opt_debug:
                    print_queue.append(
                        a(_TC_MAGENTA) + "Dialog library loaded." + a(_T_RESET)
                    )

                # Register callback to clean up COM stuff when program finishes.
                def _dlg_cleanup():
                    try:
                        dialog_lib.unload()
                    except ValueError:
                        if opt_debug:
                            print(
                                a(_TC_MAGENTA) + "Dialog library already unloaded." + a(_T_RESET)
                            )
                    else:
                        if opt_debug:
                            print(
                                a(_TC_MAGENTA) + "Dialog library unloaded." + a(_T_RESET)
                            )

                    print(end="\n")

                atexit.register(_dlg_cleanup)

    # -- # Main # ---------------------------------------------------------------------------------------------------- #
    # Intro.
    print(
        a(_TF_BOLD) + PROGRAM_NAME + a(_T_RESET),
        (
            f"""Version { a(_TF_BOLD) + PROGRAM_VER + a(_TF_NO_BOLD) }"""
            ", designed for SotES v1.2 - english Steam release."
        ), (
            f"""Running on Python { ".".join(str(_) for _ in sys.version_info[:3]) } """
            f"""{ a(_TC_MAGENTA) + "(" + sys.prefix + ")" + a(_T_RESET) }"""
        ),
        sep="\n"
    )

    print(end="\n")

    # Check for pre-processing errors.
    # # Print all queued messages.
    if len(print_queue) > 0:
        print("\n".join(print_queue))
        print(end="\n")

    # # Exit if interactive mode failed to start.
    if opt_interactive and dialog_lib is None:
        exit(1)

    # Process main arguments.
    # # Action (unpack/pack).
    action: Action

    if args['action'] is not None:
        # Received action.
        action_str = args['action']

        # # Validate received value.
        try:
            action = Action(int(action_str))
        except ValueError:
            print(
                a(_TC_RED) + f"""Invalid action received: "{action_str}".""" + a(_T_RESET)
            )
            exit(1)
    elif opt_interactive:
        # Interactive mode, no action received. Ask user.
        print(
            "What would you like to do?",
            f"""{ Action.UNPACK.value } - Unpack SotES packed resource files into bitmaps.""",
            f"""{ Action.PACK.value } - Pack bitmaps into SotES image resources files.""",
            sep="\n"
        )

        while True:
            action_str = input("==> ")

            try:
                action = Action(int(action_str))
            except ValueError:
                print(
                    a(_TC_YELLOW) + "Invalid choice." + a(_T_RESET)
                )
            else:
                break

        print(end="\n")
    else:
        # Failed to receive the action.
        print(
            a(_TC_RED) + "No action received." + a(_T_RESET),
            a(_TC_MAGENTA) + "This parameter is required when not in interactive mode." + a(_T_RESET),
            sep="\n"
        )
        exit(2)

    if action == Action.PACK:
        # Pillow required.
        if not unpacker.PIL_AVAILABLE:
            pil_str = a(_TF_UNDER) + PILLOW_URL + a(_TF_NO_UNDER)

            print(
                a(_TC_MAGENTA) + f"""Packing requires the Pillow image library: { pil_str }""" + a(_T_RESET)
            )
            exit(1)

    # # Input paths.
    input_paths: list[pl.Path]

    if len(args['input-paths']) > 0:
        # Received input paths.
        input_paths = list(pl.Path(_) for _ in args['input-paths'])
    elif opt_interactive:
        # Interactive mode, no paths received. Let user choose.
        print(
            "Waiting for user to select input directory..."
        )
        print(end="\n")

        # Get CWD.
        try:
            dlg_default_dir = pl.Path.cwd()
        except OSError:
            dlg_default_dir = None

        # Display folder select dialog.
        try:
            dialog_choice = dialog_lib.open_folder_dialog(
                title="Choose a folder containing your input files.",
                ok_label="Select",
                default_dir=dlg_default_dir
            )
        except OSError as ex:
            print(
                a(_TC_RED) + "Unexpected failure when selecting directory." + a(_T_RESET)
            )

            if opt_debug:
                print(
                    a(_TC_MAGENTA) + str(ex) + a(_T_RESET)
                )

                if ex.__cause__ is not None:
                    print(
                        a(_TC_MAGENTA) + str(ex.__cause__) + a(_T_RESET)
                    )

            exit(1)

        # Process choice.
        if dialog_choice is not None:
            input_paths = [dialog_choice]
        else:
            print(
                a(_TC_YELLOW) + "User cancelled directory selection." + a(_T_RESET)
            )
            exit(1)
    else:
        # Failed to receive any input paths.
        print(
            a(_TC_RED) + "No input paths received." + a(_T_RESET),
            a(_TC_MAGENTA) + "This parameter is required when not in interactive mode." + a(_T_RESET),
            sep="\n"
        )
        exit(2)

    # # # Validate received paths.
    input_files: list[pl.Path] = list()
    seen_files: set[pl.Path] = set()
    input_errors: dict[str, set[pl.Path]] = dict()

    for input_path in input_paths:
        try:
            input_path = input_path.resolve()

            if input_path.is_file():
                # No duplicates.
                if input_path not in seen_files:
                    seen_files.add(input_path)
                    input_files.append(input_path)
            elif input_path.is_dir():
                # Look for all files in the directory.
                for sub_path in input_path.iterdir():
                    try:
                        if sub_path.is_file():
                            sub_path = sub_path.resolve()

                            # No duplicates.
                            if sub_path not in seen_files:
                                seen_files.add(sub_path)
                                input_files.append(sub_path)
                    except OSError as ex:
                        if hasattr(ex, 'winerror'):
                            error_msg = f"""Windows Error #{ex.winerror} - {ex.strerror}:"""
                        else:
                            error_msg = f"""System Error #{ex.errno} - {ex.strerror}:"""

                        input_errors.setdefault(error_msg, set()).add(sub_path)
            else:
                if input_path.exists():
                    error_msg = "Error - Input path is not a file or directory:"
                else:
                    error_msg = "Error - Input path is invalid or does not exist:"

                input_errors.setdefault(error_msg, set()).add(input_path)
        except OSError as ex:
            if hasattr(ex, 'winerror'):
                error_msg = f"""Windows Error #{ex.winerror} - {ex.strerror}:"""
            else:
                error_msg = f"""System Error #{ex.errno} - {ex.strerror}:"""

            input_errors.setdefault(error_msg, set()).add(input_path)

    # # # Display received paths.
    # # # # Always build bulk messages. Printing with *args is very slow.
    if opt_debug and len(input_files) > 0:
        print(
            f"""Received the following {len(input_files)} files to process:""",
            "\n".join(
                f"""> {a(_TC_CYAN) + str(input_file) + a(_T_RESET)}"""
                for input_file in input_files
            ),
            sep="\n"
        )

    if len(input_errors) > 0:
        for error_msg, error_paths in sorted(input_errors.items()):
            print(
                a(_TC_YELLOW) + error_msg + a(_T_RESET),
                "\n".join(
                    f"""> {a(_TC_RED) + str(error_path) + a(_T_RESET)}"""
                    for error_path in sorted(error_paths)
                ),
                sep="\n"
            )

    # # # Display results.
    num_files = len(input_files)
    num_errors = sum(len(_) for _ in input_errors.values())

    if num_files > 0:
        files_msg = a(_TC_CYAN) + f"""{num_files} file(s)""" + a(_T_RESET)
    else:
        files_msg = a(_TC_RED) + "zero files" + a(_T_RESET)

    if num_errors > 0:
        errors_msg = a(_TC_YELLOW) + f"""{num_errors} error(s)""" + a(_T_RESET)
    else:
        errors_msg = "zero errors"

    print(
        f"""Received {files_msg} for processing, with {errors_msg}."""
    )

    # # # Check if any valid paths remained.
    if len(input_files) == 0:
        print(
            a(_TC_RED) + "No valid files received." + a(_T_RESET)
        )
        exit(1)

    print(end="\n")

    # # Output directory.
    output_dir: pl.Path | None

    if args['output_dir'] is not None:
        # Received output directory.
        if args['output_dir'] == "*":
            output_dir = None
        else:
            output_dir = pl.Path(args['output_dir'])
    elif opt_interactive:
        # No output directory passed to CLI, let user choose.
        print(
            "Waiting for user to select output directory..."
        )
        print(end="\n")

        # Get CWD.
        try:
            dlg_default_dir = pl.Path.cwd()
        except OSError:
            dlg_default_dir = None

        # Display folder select dialog.
        try:
            dialog_choice = dialog_lib.open_folder_dialog(
                title="Choose a folder to save output files in.",
                ok_label="Select",
                default_dir=dlg_default_dir
            )
        except Exception as ex:
            print(
                a(_TC_RED) + "Unexpected failure when selecting directory." + a(_T_RESET)
            )

            if opt_debug:
                print(
                    a(_TC_MAGENTA) + str(ex) + a(_T_RESET)
                )

                if ex.__cause__ is not None:
                    print(
                        a(_TC_MAGENTA) + str(ex.__cause__) + a(_T_RESET)
                    )

            exit(1)

        # Process choice.
        if dialog_choice is not None:
            output_dir = dialog_choice
        else:
            print(
                a(_TC_YELLOW) + "User cancelled directory selection." + a(_T_RESET)
            )
            exit(1)
    else:
        # Failed to get output directory.
        print(
            a(_TC_RED) + "No output directory received." + a(_T_RESET),
            a(_TC_MAGENTA) + "This parameter is required when not in interactive mode." + a(_T_RESET),
            sep="\n"
        )
        exit(2)

    # # # Validate received path.
    if output_dir is not None:
        try:
            output_dir = output_dir.resolve()

            if output_dir.is_dir():
                print(
                    "Received the following output directory to save processed files in:",
                    f"""> {a(_TC_BLUE) + str(output_dir) + a(_T_RESET)}""",
                    sep="\n"
                )
            else:
                if output_dir.exists():
                    error_msg = "The given output path is not a directory:"
                else:
                    error_msg = "The given output directory is invalid or does not exist:"

                print(
                    a(_TC_RED) + error_msg,
                    f"""> {str(output_dir)}""" + a(_T_RESET),
                    sep="\n"
                )
                exit(1)
        except OSError as ex:
            if hasattr(ex, 'winerror'):
                error_msg = f"""Windows Error #{ex.winerror} - {ex.strerror}."""
            else:
                error_msg = f"""System Error #{ex.errno} - {ex.strerror}."""

            print(
                a(_TC_RED) + "Failed to obtain the output directory due to the following:",
                error_msg,
                f"""> {str(output_dir)}""" + a(_T_RESET),
                sep="\n"
            )
            exit(1)

    print(end="\n")

    # Pre-parsing step.
    print("Queueing files...")
    print(end="\n")

    # # Generate all output file paths.
    file_queue: list[tuple[pl.Path, pl.Path]] = list()
    seen_output_files: set[pl.Path] = set()
    queue_errors: dict[str, set[pl.Path]] = dict()

    for input_file in input_files:
        if output_dir is None:
            # Save output file next to their original file.
            output_file = input_file.with_suffix(action.extension)
        else:
            # Save output file in the output directory.
            output_file = (output_dir / input_file.name).with_suffix(action.extension)

        if output_file in seen_output_files:
            error_msg = "Error - A file with the same destination is already queued."
            queue_errors.setdefault(error_msg, set()).add(input_file)
            continue

        if not opt_overwrite:
            try:
                if output_file.exists():
                    error_msg = "Error - A file already exists at this file's destination."
                    queue_errors.setdefault(error_msg, set()).add(input_file)
                    continue
            except OSError:
                error_msg = "Error - Could not validate this file's destination."
                queue_errors.setdefault(error_msg, set()).add(input_file)
                continue

        file_queue.append((input_file, output_file))
        seen_output_files.add(output_file)

    # # Display queued files.
    if opt_debug and len(file_queue) > 0:
        print(
            f"""Queued the following {len(file_queue)} files:""",
            "\n".join(
                (
                    f"""> {a(_TC_BLUE) + str(input_file) + a(_T_RESET)}"""
                    f"""\n  --> {a(_TC_CYAN) + str(output_file) + a(_T_RESET)}"""
                )
                for (input_file, output_file) in file_queue
            ),
            sep="\n"
        )
        print(end="\n")

    if len(queue_errors) > 0:
        for error_msg, error_paths in sorted(queue_errors.items()):
            print(
                a(_TC_YELLOW) + error_msg + a(_T_RESET),
                "\n".join(
                    f"""> {a(_TC_RED) + str(error_path) + a(_T_RESET)}"""
                    for error_path in sorted(error_paths)
                ),
                sep="\n"
            )
        print(end="\n")

    # # Check if any valid files remained in the queue.
    num_files = len(file_queue)
    num_errors = sum(len(_) for _ in queue_errors.values())

    if num_files == 0:
        print(
            a(_TC_RED) + f"""Could not queue any files, had {num_errors} queueing errors.""" + a(_T_RESET)
        )
        exit(1)

    # # Display queue summary.
    print(
        f"""{a(_TC_CYAN) + str(num_files) + a(_T_RESET)} files successfully queued.""",
        f"""{a(_TC_YELLOW) + str(num_errors) + a(_T_RESET)} files had errors and could not be queued."""
        if num_errors > 0 else
        a(_TC_BLUE) + "No errors queueing files." + a(_T_RESET),
        f"""Action: {str(action.name).lower()}.""",
        f"""Overwrite existing files: {a(_TC_YELLOW) + "YES" + a(_T_RESET)}"""
        if opt_overwrite else
        "Overwrite existing files: NO.",
        sep="\n"
    )

    print(end="\n")

    # # Confirm process start.
    if not opt_skip:
        print("Press Enter to start:")
        _ = input("==> ")
    else:
        print("Starting...")

    print(end="\n")

    # Main process.
    parsed_files: set[tuple[pl.Path, pl.Path]] = set()
    parse_errors: dict[str, set[tuple[pl.Path, pl.Path]]] = dict()

    # # Print-only stuff.
    last_update = -1

    for input_index, (input_file, output_file) in enumerate(file_queue):
        try:
            if opt_overwrite or not output_file.exists():
                try:
                    output_file.write_bytes(
                        unpacker.unpack(resource_data=input_file.read_bytes())
                        if action == Action.UNPACK else
                        unpacker.pack(bitmap_data=input_file.read_bytes())
                    )
                except unpacker.UnpackerError as ex:
                    error_msg = f"""Un/Packer Error - {str(ex)}:"""
                    parse_errors.setdefault(error_msg, set()).add((input_file, output_file))
                else:
                    parsed_files.add((input_file, output_file))
            else:
                error_msg = "Error - A file already exists at the target location:"
                parse_errors.setdefault(error_msg, set()).add((input_file, output_file))
        except OSError as ex:
            if hasattr(ex, 'winerror'):
                error_msg = f"""Windows Error #{ex.winerror} - {ex.strerror}:"""
            else:
                error_msg = f"""System Error #{ex.errno} - {ex.strerror}:"""

            parse_errors.setdefault(error_msg, set()).add((input_file, output_file))

        # Print status.
        progress = 30 * input_index // (len(file_queue) - 1)
        if progress > last_update:
            last_update = progress
            print(f"""\rProgress: [{("#" * progress).ljust(30, " ")}]""", sep="", end="")

    print(end="\n\n")

    # Finish.
    # # Print successfully processed files.
    if len(parsed_files) > 0:
        print(
            f"""Successfully saved the following {len(parsed_files)} files:""",
            "\n".join(
                f"""> {a(_TC_GREEN) + str(output_file) + a(_T_RESET)}"""
                for _, output_file in sorted(parsed_files)
            ),
            sep="\n"
        )
        print(end="\n")

    if len(parse_errors) > 0:
        for error_msg, error_files in sorted(parse_errors.items()):
            print(
                a(_TC_RED) + error_msg + a(_T_RESET),
                "\n".join(
                    (
                        f"""> {a(_TC_RED) + str(input_file) + a(_T_RESET)}"""
                        f"""\n  --> {a(_TC_RED) + str(output_file) + a(_T_RESET)}"""
                    )
                    for input_file, output_file in sorted(error_files)
                ),
                sep="\n"
            )
        print(end="\n")

    # # Print summary.
    num_successes = len(parsed_files)
    num_errors = sum(len(_) for _ in parse_errors.values())

    print(
        f"""Successfully parsed {a(_TC_GREEN) + str(num_successes) + " files" + a(_T_RESET)}."""
        if num_successes > 0 else
        a(_TC_RED) + "Failed to parse any files." + a(_T_RESET),
        f"""Failed to parse {a(_TC_RED) + str(num_errors) + " files" + a(_T_RESET)}."""
        if num_errors > 0 else
        a(_TC_GREEN) + "No errors while parsing!" + a(_T_RESET),
        (
            f"""{a(_TF_BOLD)}Project page: {a(_TF_UNDER)}"""
            f"""https://github.com/Huzzahd/fortune_summoners_unpacker{a(_T_RESET)}"""
        ),
        (
            f"""{a(_TF_BOLD)}Visit the fan-made Fortune Summoners Discord!"""
            f""" {a(_TF_NEG)}https://discord.gg/N68c7pt{a(_T_RESET)}"""
        ),
        sep="\n"
    )

    if not opt_skip:
        print("Press Enter to exit:")
        input("==> ")

    print(end="\n")

    exit(0)
