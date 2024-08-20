import os
import subprocess
from io import BytesIO
from pathlib import Path

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color
from kivy.graphics import Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from PIL import Image as PILImage
from swing_tool.modules.image import SwingImageBuilder

from swing_tool_gui.utils import apple_alias_to_posix_path
from swing_tool_gui.utils import get_image_display_area
from swing_tool_gui.utils import is_image_file


class ImageImportScreen(Screen):
    """
    Class for inputing image files.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical")
        self.label = Label(
            text="Click to select files.",
            font_size="20sp",
            halign="center",
            valign="middle",
        )
        self.label.bind(on_touch_down=self._on_label_click)
        self.layout.add_widget(self.label)
        self.add_widget(self.layout)

    def _on_label_click(self, instance, touch):
        """
        What happens when clicking the window.
        """
        if self.collide_point(*touch.pos):
            command = """osascript -e 'set theFiles to choose file with prompt "Select files or folder:" of type {"public.folder", "public.item"} with multiple selections allowed'"""  # noqa: E501
            process = subprocess.Popen(  # noqa: S602
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            output, error = process.communicate()
            # If error
            if process.returncode != 0:
                pass

            if output:
                posix_paths = [
                    apple_alias_to_posix_path(alias_path)
                    for alias_path in output.strip().split(b", ")
                ]
                # If select folder, get all image path under it.
                if len(posix_paths) == 1 and Path(posix_paths[0]).is_dir():
                    posix_paths = list(Path(posix_paths[0]).rglob("*"))

                # Filter out non-image files
                image_paths = [
                    image_path
                    for image_path in posix_paths
                    if is_image_file(image_path)
                ]
                self.manager.get_screen("image_process_screen").set_input_files(
                    image_paths,
                )
                self.manager.current = "image_process_screen"


class ImageProcessScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_files = []  # 初始化时的文件列表为空
        self.cropped_images = {}
        self.file_rows = []
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.current_image_path = None  # 用于保存当前正在处理的图像路径
        self.add_widget(self.layout)

    def set_input_files(self, input_files):
        # 设置 input_files 并重建 UI
        self.input_files = input_files
        self._build_ui()
        self._update_start_button_state()  # 每次重建UI后更新按钮状态

    def update_cropped_image(self, image_data):
        core_image = CoreImage(image_data, ext="png")
        for index, file_row in enumerate(self.file_rows):
            img_widget = file_row.children[1]
            if img_widget.file_path == self.current_image_path:
                img_widget.texture = core_image.texture
                img_widget.canvas.ask_update()
                self.cropped_images[index] = image_data
                break

    def _build_ui(self):
        self.layout.clear_widgets()

        # 添加 Back 和 Start 按钮行
        button_layout = BoxLayout(size_hint_y=None, height="40dp")
        button_layout.add_widget(self._build_back_button())
        button_layout.add_widget(Label())  # Add space
        button_layout.add_widget(self._build_start_button())
        self.layout.add_widget(button_layout)

        # 添加 Save to 和路径选择行
        self.layout.add_widget(self._build_output_dir())

        # 添加 Files 和文件行
        self.layout.add_widget(self._build_image_rows())

    def _build_back_button(self):
        # Back 按钮
        back_button = Button(
            text="Back",
            size_hint_x=None,
            width="80dp",
            background_color=(0, 0, 0, 0),
        )
        back_button.bind(on_press=self._go_back)
        return back_button

    def _build_start_button(self):
        # Start 按钮
        self.start_button = Button(
            text="Start",
            size_hint_x=None,
            width="80dp",
            background_color=(1, 1, 1, 1),
            color=(0, 0, 0, 1),
        )
        self.start_button.bind(on_press=self._start)
        return self.start_button

    def _build_output_dir(self):
        # Save to 字符串和下面一行的 TextInput 和选择目录按钮
        output_dir_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height="80dp",
            padding=(48, 0, 0, 0),
        )

        save_to_label = Label(
            text="Save to",
            size_hint_y=None,
            height="30dp",
            halign="left",
            valign="middle",
        )
        save_to_label.bind(size=save_to_label.setter("text_size"))  # 使文本对齐有效
        output_dir_layout.add_widget(save_to_label)

        save_layout = BoxLayout(size_hint_y=None, height="40dp")
        self.save_path_input = TextInput(hint_text="Choose a directory", readonly=True)
        self.save_path_input.bind(
            text=self._update_start_button_state,
        )  # 绑定到文本变化事件
        choose_button = Button(text="Browse", size_hint_x=None, width="80dp")
        choose_button.bind(on_press=self._open_file_browser)
        save_layout.add_widget(self.save_path_input)
        save_layout.add_widget(choose_button)

        output_dir_layout.add_widget(save_layout)

        return output_dir_layout

    def _build_image_row(self, file):
        file_row = BoxLayout(
            size_hint_y=None,
            height="342dp",
        )

        img = Image(
            source=file,
            size_hint_x=0.5,
            allow_stretch=True,
            keep_ratio=True,
        )
        img.bind(on_touch_down=self._on_image_click)  # 绑定点击事件
        img.file_path = file  # 将文件路径存储在 img 对象中
        filename = os.path.splitext(os.path.basename(file))[0]  # noqa: PTH122, PTH119
        text_input = TextInput(
            text=filename,
            multiline=False,
            size_hint_x=0.5,
        )

        file_row.add_widget(img)
        file_row.add_widget(text_input)

        return file_row

    def _on_image_click(self, instance, touch):
        if instance.collide_point(*touch.pos):
            image_path = instance.file_path
            self.current_image_path = image_path  # 保存当前正在处理的图像路径
            self.manager.get_screen("image_crop_screen").display_image(image_path)
            self.manager.current = "image_crop_screen"

    def _build_image_rows(self):
        # Files 字符串和下面的文件行
        image_rows_layout = BoxLayout(orientation="vertical", padding=(48, 0, 0, 0))

        files_label = Label(
            text="Files",
            size_hint_y=None,
            height="30dp",
            halign="left",
            valign="middle",
        )
        files_label.bind(size=files_label.setter("text_size"))  # 使文本对齐有效
        image_rows_layout.add_widget(files_label)

        files_grid_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        files_grid_layout.bind(minimum_height=files_grid_layout.setter("height"))

        for file in self.input_files:
            file_row = self._build_image_row(file)
            files_grid_layout.add_widget(file_row)
            self.file_rows.append(file_row)

        scroll_view = ScrollView(
            size_hint=(1, None),
            height="400dp",
        )  # 限制 ScrollView 的高度
        scroll_view.add_widget(files_grid_layout)

        image_rows_layout.add_widget(scroll_view)

        return image_rows_layout

    def _go_back(self, instance):
        self.manager.current = "image_import_screen"

    def _open_file_browser(self, instance):
        command = """
        osascript -e 'set theFolder to choose folder with prompt "Select Save Directory"' -e 'POSIX path of theFolder'
        """  # noqa: E501
        process = subprocess.Popen(  # noqa: S602
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output, error = process.communicate()

        if process.returncode == 0:
            selected_path = output.decode("utf-8").strip()
            self.save_path_input.text = selected_path
        else:
            # raise error
            pass

        self._update_start_button_state()  # 更新 Start 按钮状态

    def _update_start_button_state(self, *args):
        # 检查 save_path_input 是否为空
        if self.save_path_input.text:
            self.start_button.disabled = False
        else:
            self.start_button.disabled = True

    def _start(self, instance):
        swing_image_builder = SwingImageBuilder()
        for index, input_file in enumerate(self.input_files):
            # 获取对应的文本框对象
            image = swing_image_builder.build(
                self.cropped_images.get(index, input_file),
                self.file_rows[index].children[0].text,
            )

            image.save(
                Path(self.save_path_input.text)
                / f"{Path(input_file).stem}_new{Path(input_file).suffix}",
            )
        self._show_success_popup()

    def _show_success_popup(self):
        # 创建弹出窗口的内容
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # 创建标签显示成功消息
        message_label = Label(text="Images built successfully!")
        layout.add_widget(message_label)

        # 创建 OK 按钮
        ok_button = Button(text="OK", size_hint_y=None, height="40dp")
        layout.add_widget(ok_button)

        # 创建弹出窗口
        popup = Popup(title="Success", content=layout, size_hint=(0.5, 0.3))

        # 绑定 OK 按钮的事件
        ok_button.bind(on_press=lambda instance: self._on_success_ok(popup))

        # 显示弹出窗口
        popup.open()

    def _on_success_ok(self, popup):
        # 关闭弹出窗口
        popup.dismiss()
        # 返回到 image_import_screen
        self.manager.current = "image_import_screen"


class CropBox(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (0, 0)
        self.dragging = False  # 用于标记是否在拖拽中
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        with self.canvas:
            Color(1, 0, 0, 1)  # Red color for the box border
            self.rect = Line(width=2)

        self.bind(pos=self.update_position)
        self.bind(size=self.update_position)

    def update_position(self, *args):
        self.rect.rectangle = (self.x, self.y, self.width, self.height)
        self.canvas.ask_update()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dragging = True
            self.drag_offset_x = touch.x - self.x
            self.drag_offset_y = touch.y - self.y
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.dragging:
            parent = self.parent
            if parent:
                image_widget = parent.image_widget

                # 获取图片的实际显示区域
                display_x, display_y, display_width, display_height = (
                    get_image_display_area(image_widget)
                )

                # Convert touch position relative to the image_widget
                new_x = touch.x - self.drag_offset_x
                new_y = touch.y - self.drag_offset_y

                # Limit new_x and new_y within the image bounds
                new_x = min(
                    max(new_x, display_x),
                    display_x + display_width - self.width,
                )
                new_y = min(
                    max(new_y, display_y),
                    display_y + display_height - self.height,
                )

                self.pos = (new_x, new_y)
                return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.dragging:
            self.dragging = False
            return True
        return super().on_touch_up(touch)


class ImageCropScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        # 添加按钮行
        button_layout = BoxLayout(size_hint_y=None, height="40dp", pos_hint={"top": 1})
        button_layout.add_widget(self._build_back_button())
        button_layout.add_widget(Label())  # Add space
        button_layout.add_widget(self._build_done_button())
        self.layout.add_widget(button_layout)

        # 添加 Image Widget 用于显示图片
        self.image_widget = Image(size_hint=(1, 1), allow_stretch=True, keep_ratio=True)
        self.layout.add_widget(self.image_widget)

        # 将 image_widget 设置为 layout 的属性, 以便在 CropBox 中访问
        self.layout.image_widget = self.image_widget

        # 添加裁剪框 (确保添加顺序是在 Image 之后)
        self.crop_box = CropBox()
        self.layout.add_widget(self.crop_box)

        self.original_image = None  # 保存原始图片的 Pillow 对象

    def display_image(self, image_path):
        # 设置图片的路径
        self.image_widget.source = image_path

        # 加载图片为 Pillow Image 以便裁剪时使用
        self.original_image = PILImage.open(image_path)

        # 使用 Clock.schedule_once 确保图片和布局完全加载后再更新裁剪框
        Clock.schedule_once(self._check_texture_loaded, 0.1)

    def _check_texture_loaded(self, *args):
        if self.image_widget.texture:
            self._update_crop_box()
        else:
            # 如果纹理尚未加载, 稍后再次检查
            Clock.schedule_once(self._check_texture_loaded, 0.1)

    def _on_image_loaded(self, instance, *args):
        # 确保在图片加载完成后执行布局更新, 立即调用更新方法
        if instance.texture:
            self._update_crop_box()

    def _update_crop_box(self, *args):
        # 当图片加载完成后, 设置裁剪框的尺寸和位置
        image_width, image_height = self.image_widget.texture_size
        widget_width, widget_height = self.image_widget.size

        # 确定图片在widget中的缩放比例和位置
        scale_x = widget_width / image_width
        scale_y = widget_height / image_height
        scale = min(scale_x, scale_y)
        display_width = image_width * scale
        display_height = image_height * scale

        short_side = min(display_width, display_height)

        # 设置裁剪框的大小和位置
        self.crop_box.size = (short_side, short_side)
        self.crop_box.pos = (
            (self.image_widget.center_x - short_side / 2),
            (self.image_widget.center_y - short_side / 2),
        )

        self.crop_box.update_position()
        self.layout.do_layout()  # 强制布局更新

    def _build_back_button(self):
        back_button = Button(
            text="Back",
            size_hint_x=None,
            width="80dp",
            background_color=(0, 0, 0, 0),
            pos_hint={"x": 0, "top": 1},
        )
        back_button.bind(on_press=self._go_back)
        return back_button

    def _build_done_button(self):
        done_button = Button(
            text="Done",
            size_hint_x=None,
            width="80dp",
            background_color=(1, 1, 1, 1),
            color=(0, 0, 0, 1),
            pos_hint={"right": 1, "top": 1},
        )
        done_button.bind(on_press=self._crop_image)
        return done_button

    def _crop_image(self, instance):
        if self.original_image is None:
            return

        # 获取裁剪框在图片上的相对位置
        display_x, display_y, display_width, display_height = get_image_display_area(
            self.image_widget,
        )

        # 确保在获取位置和尺寸时使用最新的裁剪框坐标
        crop_x = (
            (self.crop_box.x - display_x) / display_width * self.original_image.width
        )
        crop_y = (
            (self.crop_box.y - display_y) / display_height * self.original_image.height
        )  # 注意使用裁剪框的 top 属性
        crop_width = self.crop_box.width / display_width * self.original_image.width
        crop_height = self.crop_box.height / display_height * self.original_image.height

        # 将坐标转换为整数以便裁剪
        crop_x = int(crop_x)
        crop_y = int(
            self.original_image.height - crop_y,
        )  # 修正 crop_y 坐标 原点从图片底部开始
        crop_width = int(crop_width)
        crop_height = int(crop_height)

        # 确保裁剪区域在图片范围内
        crop_x = max(0, crop_x)
        crop_y = max(0, crop_y - crop_height)
        crop_width = min(self.original_image.width - crop_x, crop_width)
        crop_height = min(self.original_image.height - crop_y, crop_height)

        # 进行裁剪
        cropped_image = self.original_image.crop(
            (
                crop_x,
                crop_y,
                crop_x + crop_width,
                crop_y + crop_height,
            ),
        )

        # 将裁剪后的图像保存到内存中
        image_data = BytesIO()
        cropped_image.save(image_data, format="PNG")
        image_data.seek(0)  # 回到缓冲区的开始

        # 更新 `ImageProcessScreen` 的图像行
        self.manager.get_screen("image_process_screen").update_cropped_image(image_data)

        # 返回到 `ImageProcessScreen`
        self._go_back(None)

    def _go_back(self, instance):
        self.manager.current = "image_process_screen"
