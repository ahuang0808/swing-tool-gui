import os
from io import BytesIO
from pathlib import Path

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Line
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

from swing_tool_gui.utils import (
    AppleScriptExecutor,
    apple_alias_to_posix_path,
    get_image_display_area,
    is_image_file,
)

# Constants
BUTTON_HEIGHT = "40dp"
LABEL_HEIGHT = "30dp"
WIDGET_PADDING = 10
SCROLL_VIEW_HEIGHT = "400dp"
MIN_CROP_SIZE = 10


class ImageImportScreen(Screen):
    """Screen for inputting image files."""

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
        """Handles label click to open file selection dialog."""
        if self.collide_point(*touch.pos):
            self._open_file_selection()

    def _open_file_selection(self):
        """Opens the file selection dialog using AppleScript."""
        script = (
            "osascript -e 'set theFiles to choose file with prompt "
            '"Select files or folder:" of type {"public.folder", "public.item"} '
            "with multiple selections allowed'"
        )
        output = AppleScriptExecutor.run_script(script)
        self._process_selected_files(output)

    def _process_selected_files(self, output):
        """Processes selected files and folders."""
        posix_paths = [
            apple_alias_to_posix_path(alias_path)
            for alias_path in output.strip().split(b", ")
        ]

        if len(posix_paths) == 1 and Path(posix_paths[0]).is_dir():
            posix_paths = list(Path(posix_paths[0]).rglob("*"))

        image_paths = [path for path in posix_paths if is_image_file(path)]
        self.manager.get_screen("image_process_screen").set_input_files(image_paths)
        self.manager.current = "image_process_screen"


class ImageProcessScreen(Screen):
    """Screen for processing and displaying images."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_files = []
        self.cropped_images = {}
        self.file_rows = []
        self.layout = BoxLayout(
            orientation="vertical", padding=WIDGET_PADDING, spacing=WIDGET_PADDING
        )
        self.current_image_path = None
        self.add_widget(self.layout)

    def set_input_files(self, input_files):
        """Sets the input files and rebuilds the UI."""
        self.input_files = input_files
        self._build_ui()
        self._update_start_button_state()

    def update_cropped_image(self, image_data):
        """Updates the cropped image in the UI."""
        core_image = CoreImage(image_data, ext="png")
        for index, file_row in enumerate(self.file_rows):
            img_widget = file_row.children[1]
            if img_widget.file_path == self.current_image_path:
                img_widget.texture = core_image.texture
                img_widget.canvas.ask_update()
                self.cropped_images[index] = image_data
                break

    def _build_ui(self):
        """Builds the UI layout for the screen."""
        self.layout.clear_widgets()
        self._add_button_row()
        self.layout.add_widget(self._build_output_dir())
        self.layout.add_widget(self._build_image_rows())

    def _add_button_row(self):
        """Adds the row with Back and Start buttons."""
        button_layout = BoxLayout(size_hint_y=None, height=BUTTON_HEIGHT)
        button_layout.add_widget(self._build_back_button())
        button_layout.add_widget(Label())  # Spacer
        button_layout.add_widget(self._build_start_button())
        self.layout.add_widget(button_layout)

    def _build_back_button(self):
        """Builds the Back button."""
        back_button = Button(
            text="Back", size_hint_x=None, width="80dp", background_color=(0, 0, 0, 0)
        )
        back_button.bind(on_press=self._go_back)
        return back_button

    def _build_start_button(self):
        """Builds the Start button."""
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
        """Builds the output directory selection UI."""
        output_dir_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height="80dp",
            padding=(48, 0, 0, 0),
        )
        save_to_label = Label(
            text="Save to",
            size_hint_y=None,
            height=LABEL_HEIGHT,
            halign="left",
            valign="middle",
        )
        save_to_label.bind(size=save_to_label.setter("text_size"))
        output_dir_layout.add_widget(save_to_label)

        save_layout = BoxLayout(size_hint_y=None, height=BUTTON_HEIGHT)
        self.save_path_input = TextInput(hint_text="Choose a directory", readonly=True)
        self.save_path_input.bind(text=self._update_start_button_state)
        choose_button = Button(text="Browse", size_hint_x=None, width="80dp")
        choose_button.bind(on_press=self._open_file_browser)
        save_layout.add_widget(self.save_path_input)
        save_layout.add_widget(choose_button)

        output_dir_layout.add_widget(save_layout)
        return output_dir_layout

    def _build_image_row(self, file):
        """Builds a single row for displaying an image and its filename."""
        file_row = BoxLayout(size_hint_y=None, height="342dp")
        img = Image(source=file, size_hint_x=0.5, allow_stretch=True, keep_ratio=True)
        img.bind(on_touch_down=self._on_image_click)
        img.file_path = file
        filename = os.path.splitext(os.path.basename(file))[0]
        text_input = TextInput(text=filename, multiline=False, size_hint_x=0.5)
        file_row.add_widget(img)
        file_row.add_widget(text_input)
        return file_row

    def _on_image_click(self, instance, touch):
        """Handles image click to initiate cropping."""
        if instance.collide_point(*touch.pos):
            self.current_image_path = instance.file_path
            self.manager.get_screen("image_crop_screen").display_image(
                self.current_image_path
            )
            self.manager.current = "image_crop_screen"

    def _build_image_rows(self):
        """Builds the layout for displaying all selected images."""
        image_rows_layout = BoxLayout(orientation="vertical", padding=(48, 0, 0, 0))

        files_label = Label(
            text="Files",
            size_hint_y=None,
            height=LABEL_HEIGHT,
            halign="left",
            valign="middle",
        )
        files_label.bind(size=files_label.setter("text_size"))
        image_rows_layout.add_widget(files_label)

        files_grid_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        files_grid_layout.bind(minimum_height=files_grid_layout.setter("height"))

        for file in self.input_files:
            file_row = self._build_image_row(file)
            files_grid_layout.add_widget(file_row)
            self.file_rows.append(file_row)

        scroll_view = ScrollView(size_hint=(1, None), height=SCROLL_VIEW_HEIGHT)
        scroll_view.add_widget(files_grid_layout)
        image_rows_layout.add_widget(scroll_view)
        return image_rows_layout

    def _go_back(self, instance):
        """Navigates back to the image import screen."""
        self.manager.current = "image_import_screen"

    def _open_file_browser(self, instance):
        """Opens a file browser to select the output directory."""
        script = (
            "osascript -e 'set theFolder to choose folder "
            'with prompt "Select Save Directory"\' '
            "-e 'POSIX path of theFolder'"
        )
        selected_path = AppleScriptExecutor.run_script(script)
        self.save_path_input.text = selected_path
        self._update_start_button_state()

    def _update_start_button_state(self, *args):
        """Enables or disables the Start button based on input."""
        self.start_button.disabled = not bool(self.save_path_input.text)

    def _start(self, instance):
        """Starts the image processing."""
        swing_image_builder = SwingImageBuilder()
        for index, input_file in enumerate(self.input_files):
            image = swing_image_builder.build(
                self.cropped_images.get(index, input_file),
                self.file_rows[index].children[0].text,
            )
            image.save(
                Path(self.save_path_input.text.strip())
                / f"{Path(input_file).stem}_new{Path(input_file).suffix}"
            )
        self._show_success_popup()

    def _show_success_popup(self):
        """Displays a success message popup."""
        layout = BoxLayout(
            orientation="vertical", padding=WIDGET_PADDING, spacing=WIDGET_PADDING
        )
        message_label = Label(text="Images built successfully!")
        layout.add_widget(message_label)
        ok_button = Button(text="OK", size_hint_y=None, height=BUTTON_HEIGHT)
        layout.add_widget(ok_button)
        popup = Popup(title="Success", content=layout, size_hint=(0.5, 0.3))
        ok_button.bind(on_press=lambda instance: self._on_success_ok(popup))
        popup.open()

    def _on_success_ok(self, popup):
        """Handles the OK button click in the success popup."""
        popup.dismiss()
        self.manager.current = "image_import_screen"


class CropBox(Widget):
    """Widget representing a resizable and draggable crop box."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (0, 0)
        self.dragging = False
        self.resizing = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.start_drag_y = 0

        with self.canvas:
            Color(1, 0, 0, 1)
            self.rect = Line(width=2)

        self.bind(pos=self.update_position)
        self.bind(size=self.update_position)

    def update_position(self, *args):
        """Updates the position of the crop box."""
        self.rect.rectangle = (self.x, self.y, self.width, self.height)
        self.canvas.ask_update()

    def on_touch_down(self, touch):
        """Handles touch down events for dragging and resizing."""
        if self.collide_point(*touch.pos):
            if touch.button == "left":
                self._start_dragging(touch)
                return True
            elif touch.button == "right":
                self._start_resizing(touch)
                return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        """Handles touch move events for dragging and resizing."""
        if touch.button == "left" and self.dragging:
            self._drag(touch)
            return True
        elif touch.button == "right" and self.resizing:
            self._resize(touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """Handles touch up events to end dragging and resizing."""
        if touch.button == "left" and self.dragging:
            self.dragging = False
            return True
        elif touch.button == "right" and self.resizing:
            self.resizing = False
            return True
        return super().on_touch_up(touch)

    def _start_dragging(self, touch):
        """Starts dragging the crop box."""
        self.dragging = True
        self.drag_offset_x = touch.x - self.x
        self.drag_offset_y = touch.y - self.y

    def _start_resizing(self, touch):
        """Starts resizing the crop box."""
        self.resizing = True
        self.start_drag_y = touch.y

    def _drag(self, touch):
        """Handles the dragging of the crop box."""
        parent = self.parent
        if parent:
            image_widget = parent.image_widget
            display_x, display_y, display_width, display_height = (
                get_image_display_area(image_widget)
            )

            new_x = touch.x - self.drag_offset_x
            new_y = touch.y - self.drag_offset_y

            new_x = min(max(new_x, display_x), display_x + display_width - self.width)
            new_y = min(max(new_y, display_y), display_y + display_height - self.height)

            self.pos = (new_x, new_y)

    def _resize(self, touch):
        """Handles the resizing of the crop box."""
        parent = self.parent
        if parent:
            image_widget = parent.image_widget
            display_x, display_y, display_width, display_height = (
                get_image_display_area(image_widget)
            )

            max_side = min(display_width, display_height)
            drag_distance = touch.y - self.start_drag_y
            scale_factor = 1.01 if drag_distance > 0 else 0.99

            new_width = self.width * scale_factor
            new_height = self.height * scale_factor

            if new_width > max_side or new_height > max_side:
                new_width = min(new_width, max_side)
                new_height = min(new_height, max_side)

            if new_width < MIN_CROP_SIZE or new_height < MIN_CROP_SIZE:
                new_width = max(new_width, MIN_CROP_SIZE)
                new_height = max(new_height, MIN_CROP_SIZE)

            self.size = (new_width, new_height)
            self.pos = (self.center_x - new_width / 2, self.center_y - new_height / 2)

            self.start_drag_y = touch.y
            self.update_position()


class ImageCropScreen(Screen):
    """Screen for cropping images."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        self._add_button_row()

        self.image_widget = Image(size_hint=(1, 1), allow_stretch=True, keep_ratio=True)
        self.layout.add_widget(self.image_widget)

        self.layout.image_widget = self.image_widget
        self.crop_box = CropBox()
        self.layout.add_widget(self.crop_box)

        self.original_image = None

    def _add_button_row(self):
        """Adds the row with Back and Done buttons."""
        button_layout = BoxLayout(
            size_hint_y=None, height=BUTTON_HEIGHT, pos_hint={"top": 1}
        )
        button_layout.add_widget(self._build_back_button())
        button_layout.add_widget(Label())
        button_layout.add_widget(self._build_done_button())
        self.layout.add_widget(button_layout)

    def _build_back_button(self):
        """Builds the Back button."""
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
        """Builds the Done button."""
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

    def display_image(self, image_path):
        """Displays the selected image for cropping."""
        self.image_widget.source = image_path
        self.original_image = PILImage.open(image_path)
        Clock.schedule_once(self._check_texture_loaded, 0.1)

    def _check_texture_loaded(self, *args):
        """Checks if the image texture is loaded and updates the crop box."""
        if self.image_widget.texture:
            self._update_crop_box()
        else:
            Clock.schedule_once(self._check_texture_loaded, 0.1)

    def _update_crop_box(self, *args):
        """Updates the crop box size and position based on the image."""
        image_width, image_height = self.image_widget.texture_size
        widget_width, widget_height = self.image_widget.size

        scale_x = widget_width / image_width
        scale_y = widget_height / image_height
        scale = min(scale_x, scale_y)
        display_width = image_width * scale
        display_height = image_height * scale

        short_side = min(display_width, display_height)

        self.crop_box.size = (short_side, short_side)
        self.crop_box.pos = (
            self.image_widget.center_x - short_side / 2,
            self.image_widget.center_y - short_side / 2,
        )

        self.crop_box.update_position()
        self.layout.do_layout()

    def _crop_image(self, instance):
        """Crops the image based on the crop box and updates the process screen."""
        if self.original_image is None:
            return

        display_x, display_y, display_width, display_height = get_image_display_area(
            self.image_widget
        )

        crop_x = (
            (self.crop_box.x - display_x) / display_width * self.original_image.width
        )
        crop_y = (
            (self.crop_box.y - display_y) / display_height * self.original_image.height
        )
        crop_width = self.crop_box.width / display_width * self.original_image.width
        crop_height = self.crop_box.height / display_height * self.original_image.height
        crop_x = int(crop_x)
        crop_y = int(self.original_image.height - crop_y)
        crop_width = int(crop_width)
        crop_height = int(crop_height)

        crop_x = max(0, crop_x)
        crop_y = max(0, crop_y - crop_height)
        crop_width = min(self.original_image.width - crop_x, crop_width)
        crop_height = min(self.original_image.height - crop_y, crop_height)

        cropped_image = self.original_image.crop(
            (crop_x, crop_y, crop_x + crop_width, crop_y + crop_height)
        )

        image_data = BytesIO()
        cropped_image.save(image_data, format="PNG")
        image_data.seek(0)

        self.manager.get_screen("image_process_screen").update_cropped_image(image_data)
        self._go_back(None)

    def _go_back(self, instance):
        """Navigates back to the image process screen."""
        self.manager.current = "image_process_screen"
