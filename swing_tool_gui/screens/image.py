import os
import subprocess
from pathlib import Path

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from swing_tool.modules.image import SwingImageBuilder

from swing_tool_gui.utils import apple_alias_to_posix_path
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

            posix_paths = [
                apple_alias_to_posix_path(alias_path)
                for alias_path in output.strip().split(b", ")
            ]
            # If select folder, get all image path under it.
            if len(posix_paths) == 1 and Path(posix_paths[0]).is_dir():
                posix_paths = list(Path(posix_paths[0]).rglob("*"))

            # Filter out non-image files
            image_paths = [
                image_path for image_path in posix_paths if is_image_file(image_path)
            ]
            self.manager.get_screen("image_process_screen").set_input_files(image_paths)
            self.manager.current = "image_process_screen"


class ImageProcessScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_files = []  # 初始化时的文件列表为空
        self.file_rows = []
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.add_widget(self.layout)

    def set_input_files(self, input_files):
        # 设置 input_files 并重建 UI
        self.input_files = input_files
        self._build_ui()
        self._update_start_button_state()  # 每次重建UI后更新按钮状态

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
            file_row = BoxLayout(
                size_hint_y=None,
                height="342dp",
            )  # change the height to resize the image

            img = Image(
                source=file,
                size_hint_x=0.5,
                allow_stretch=True,
                keep_ratio=True,
            )
            filename = os.path.splitext(os.path.basename(file))[0]  # noqa: PTH122, PTH119
            text_input = TextInput(
                text=filename,
                multiline=False,
                size_hint_x=0.5,
            )  # 文本框占一半宽度

            file_row.add_widget(img)
            file_row.add_widget(text_input)
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
                input_file,
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
