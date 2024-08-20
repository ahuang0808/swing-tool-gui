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


def get_image_display_area(image_widget):
    """
    Get image display area.

    Args:
    image_widget

    Return:
    tuple: (x, y, width, height)
    """
    # 获取图片纹理的宽高
    texture_width, texture_height = image_widget.texture_size
    # 获取 Image 小部件的宽高
    widget_width, widget_height = image_widget.size

    # 计算图片在 Image 小部件中的缩放比例
    scale_x = widget_width / texture_width
    scale_y = widget_height / texture_height
    scale = min(scale_x, scale_y)

    # 计算图片显示的宽高
    display_width = texture_width * scale
    display_height = texture_height * scale

    # 计算图片实际显示区域的 x 和 y
    display_x = image_widget.center_x - display_width / 2
    display_y = image_widget.center_y - display_height / 2

    return display_x, display_y, display_width, display_height
