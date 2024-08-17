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
