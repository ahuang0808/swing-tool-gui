import subprocess

from kivy.uix.widget import Widget
from PIL import Image


class AppleScriptExecutor:
    """A utility class for executing AppleScript commands."""

    @staticmethod
    def run_script(script):
        """Runs the given AppleScript command and returns the output."""
        process = subprocess.Popen(
            script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output, error = process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"AppleScript execution failed: {error.decode('utf-8')}")

        return output


def is_image_file(file_path: str):
    """
    Check if a file is an image.

    Args:
    file_path (str): Path to the file

    Return:
    bool: Is image or not
    """
    try:
        with Image.open(file_path) as img:
            img.verify()
    except (OSError, SyntaxError):
        return False
    else:
        return True


def apple_alias_to_posix_path(alias_path: bytes):
    """
    Convert apple alias path to POSIX path

    Args:
    alias_path(bytes): Apple alias Path to the file

    Return:
    str: POSIX path to the file
    """
    return alias_path.decode("utf-8").replace(":", "/").lstrip("alias Macintosh HD")


def find_system_font():
    """
    Find system default Chinese font

    Args:
    None

    Return:
    str: Path to font file
    """
    import platform

    system = platform.system()
    if system == "Windows":
        return "C:\\Windows\\Fonts\\msyh.ttc"
    if system == "Darwin":
        return "/System/Library/Fonts/STHeiti Light.ttc"
    if system == "Linux":
        return "/usr/share/fonts/truetype/arphic/ukai.ttc"
    return None


def get_image_display_area(image_widget: Widget):
    """
    Get image display area.

    Args:
    image_widget(Widget): Widget of image.

    Return:
    tuple: (x, y, width, height)
    """
    # get size of image texture
    texture_width, texture_height = image_widget.texture_size
    # get size of image widget
    widget_width, widget_height = image_widget.size

    # alculate the scale of image in widget
    scale_x = widget_width / texture_width
    scale_y = widget_height / texture_height
    scale = min(scale_x, scale_y)

    # calculate display image size
    display_width = texture_width * scale
    display_height = texture_height * scale

    # calculate the display position
    display_x = image_widget.center_x - display_width / 2
    display_y = image_widget.center_y - display_height / 2

    return display_x, display_y, display_width, display_height
