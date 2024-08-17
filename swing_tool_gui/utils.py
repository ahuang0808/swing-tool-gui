from PIL import Image


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


def apple_alias_to_posix_path(alias_path):
    """
    Convert apple alias path to POSIX path

    Args:
    alias_path: Path to the file

    Return:
    str: POSIX path to the file
    """
    return alias_path.decode("utf-8").replace(":", "/").lstrip("alias Macintosh HD")  # noqa: B005


def find_system_font():
    """
    Find system default Chinese font

    Args:
    Nonhe

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
