import os
import subprocess
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
    apple_alias_to_posix_path,
    get_image_display_area,
    is_image_file,
)


class ImageImportScreen(Screen):
    """
    Class for inputting image files.
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
            command = (
                "osascript -e 'set theFiles to choose file with prompt "
                '"Select files or folder:" of type {"public.folder", "public.item"} '
                "with multiple selections allowed'"
            )
            process = subprocess.Popen(
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
        self.input_files = []  # Empty file list during initialization
        self.cropped_images = {}
        self.file_rows = []
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.current_image_path = (
            None  # Used to save the path of the currently processed image
        )
        self.add_widget(self.layout)

    def set_input_files(self, input_files):
        # Set input_files and rebuild the UI
        self.input_files = input_files
        self._build_ui()
        # Update the button state after rebuilding the UI
        self._update_start_button_state()

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

        # Add Back and Start button row
        button_layout = BoxLayout(size_hint_y=None, height="40dp")
        button_layout.add_widget(self._build_back_button())
        button_layout.add_widget(Label())  # Add space
        button_layout.add_widget(self._build_start_button())
        self.layout.add_widget(button_layout)

        # Add Save to and path selection row
        self.layout.add_widget(self._build_output_dir())

        # Add Files and file rows
        self.layout.add_widget(self._build_image_rows())

    def _build_back_button(self):
        # Back button
        back_button = Button(
            text="Back",
            size_hint_x=None,
            width="80dp",
            background_color=(0, 0, 0, 0),
        )
        back_button.bind(on_press=self._go_back)
        return back_button

    def _build_start_button(self):
        # Start button
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
        # Save to string and the TextInput and browse button in the row below it
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
        save_to_label.bind(
            size=save_to_label.setter("text_size")
        )  # Enable text alignment
        output_dir_layout.add_widget(save_to_label)

        save_layout = BoxLayout(size_hint_y=None, height="40dp")
        self.save_path_input = TextInput(hint_text="Choose a directory", readonly=True)
        self.save_path_input.bind(
            text=self._update_start_button_state,
        )  # Bind to text change event
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
        img.bind(on_touch_down=self._on_image_click)  # Bind click event
        img.file_path = file  # Store the file path in the img object
        filename = os.path.splitext(os.path.basename(file))[0]
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
            self.current_image_path = (
                image_path  # Save the path of the currently processed image
            )
            self.manager.get_screen("image_crop_screen").display_image(image_path)
            self.manager.current = "image_crop_screen"

    def _build_image_rows(self):
        # Files string and the file rows below it
        image_rows_layout = BoxLayout(orientation="vertical", padding=(48, 0, 0, 0))

        files_label = Label(
            text="Files",
            size_hint_y=None,
            height="30dp",
            halign="left",
            valign="middle",
        )
        files_label.bind(size=files_label.setter("text_size"))  # Enable text alignment
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
        )  # Limit the height of the ScrollView
        scroll_view.add_widget(files_grid_layout)

        image_rows_layout.add_widget(scroll_view)

        return image_rows_layout

    def _go_back(self, instance):
        self.manager.current = "image_import_screen"

    def _open_file_browser(self, instance):
        command = (
            "osascript -e 'set theFolder to choose folder "
            'with prompt "Select Save Directory"\' '
            "-e 'POSIX path of theFolder'"
        )
        process = subprocess.Popen(
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

        self._update_start_button_state()  # Update Start button state

    def _update_start_button_state(self, *args):
        # Check if save_path_input is empty
        if self.save_path_input.text:
            self.start_button.disabled = False

        else:
            self.start_button.disabled = True

    def _start(self, instance):
        swing_image_builder = SwingImageBuilder()
        for index, input_file in enumerate(self.input_files):
            # Get the corresponding text input object
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
        # Create the content of the popup window
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Create a label to display the success message
        message_label = Label(text="Images built successfully!")
        layout.add_widget(message_label)

        # Create the OK button
        ok_button = Button(text="OK", size_hint_y=None, height="40dp")
        layout.add_widget(ok_button)

        # Create the popup window
        popup = Popup(title="Success", content=layout, size_hint=(0.5, 0.3))

        # Bind the OK button event
        ok_button.bind(on_press=lambda instance: self._on_success_ok(popup))

        # Show the popup window
        popup.open()

    def _on_success_ok(self, popup):
        # Close the popup window
        popup.dismiss()
        # Return to image_import_screen
        self.manager.current = "image_import_screen"


class CropBox(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (0, 0)
        self.dragging = False  # Used to mark whether it is being dragged
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

                # Get the actual display area of the image
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

        # Add the button row
        button_layout = BoxLayout(size_hint_y=None, height="40dp", pos_hint={"top": 1})
        button_layout.add_widget(self._build_back_button())
        button_layout.add_widget(Label())  # Add space
        button_layout.add_widget(self._build_done_button())
        self.layout.add_widget(button_layout)

        # Add Image Widget to display the image
        self.image_widget = Image(size_hint=(1, 1), allow_stretch=True, keep_ratio=True)
        self.layout.add_widget(self.image_widget)

        # Set image_widget as a property of layout to access it in CropBox
        self.layout.image_widget = self.image_widget

        # Add the cropping box (make sure it is added after Image)
        self.crop_box = CropBox()
        self.layout.add_widget(self.crop_box)

        self.original_image = None  # Save the original image as a Pillow object

    def display_image(self, image_path):
        # Set the path of the image
        self.image_widget.source = image_path

        # Load the image as a Pillow Image for cropping
        self.original_image = PILImage.open(image_path)

        # Use Clock.schedule_once to ensure the image and layout
        # are fully loaded before updating the crop box
        Clock.schedule_once(self._check_texture_loaded, 0.1)

    def _check_texture_loaded(self, *args):
        if self.image_widget.texture:
            self._update_crop_box()
        else:
            # If the texture is not yet loaded, check again later
            Clock.schedule_once(self._check_texture_loaded, 0.1)

    def _on_image_loaded(self, instance, *args):
        # Ensure that layout updates are performed after the image is fully loaded,
        # call update method immediately
        if instance.texture:
            self._update_crop_box()

    def _update_crop_box(self, *args):
        # When the image is fully loaded, set the size and position of the crop box
        image_width, image_height = self.image_widget.texture_size
        widget_width, widget_height = self.image_widget.size

        # Determine the scaling ratio and position of the image within the widget
        scale_x = widget_width / image_width
        scale_y = widget_height / image_height
        scale = min(scale_x, scale_y)
        display_width = image_width * scale
        display_height = image_height * scale

        short_side = min(display_width, display_height)

        # Set the size and position of the crop box
        self.crop_box.size = (short_side, short_side)
        self.crop_box.pos = (
            (self.image_widget.center_x - short_side / 2),
            (self.image_widget.center_y - short_side / 2),
        )

        self.crop_box.update_position()
        self.layout.do_layout()  # Force layout update

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

        # Get the relative position of the crop box on the image
        display_x, display_y, display_width, display_height = get_image_display_area(
            self.image_widget,
        )

        # Ensure the latest crop box coordinates are used
        # when getting the position and size
        crop_x = (
            (self.crop_box.x - display_x) / display_width * self.original_image.width
        )
        crop_y = (
            (self.crop_box.y - display_y) / display_height * self.original_image.height
        )  # Note that the top attribute of the crop box is used
        crop_width = self.crop_box.width / display_width * self.original_image.width
        crop_height = self.crop_box.height / display_height * self.original_image.height

        # Convert coordinates to integers for cropping
        crop_x = int(crop_x)
        crop_y = int(
            self.original_image.height - crop_y,
        )  # Adjust crop_y coordinate; origin is at the bottom of the image
        crop_width = int(crop_width)
        crop_height = int(crop_height)

        # Ensure the cropping area is within the image boundaries
        crop_x = max(0, crop_x)
        crop_y = max(0, crop_y - crop_height)
        crop_width = min(self.original_image.width - crop_x, crop_width)
        crop_height = min(self.original_image.height - crop_y, crop_height)

        # Perform the crop
        cropped_image = self.original_image.crop(
            (
                crop_x,
                crop_y,
                crop_x + crop_width,
                crop_y + crop_height,
            ),
        )

        # Save the cropped image to memory
        image_data = BytesIO()
        cropped_image.save(image_data, format="PNG")
        image_data.seek(0)  # Go back to the start of the buffer

        # Update the image row in `ImageProcessScreen`
        self.manager.get_screen("image_process_screen").update_cropped_image(image_data)

        # Return to `ImageProcessScreen`
        self._go_back(None)

    def _go_back(self, instance):
        self.manager.current = "image_process_screen"
