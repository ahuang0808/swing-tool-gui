from kivy.app import App
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager

from swing_tool_gui.screens.image import ImageImportScreen
from swing_tool_gui.screens.image import ImageProcessScreen
from swing_tool_gui.utils import find_system_font


class MyApp(App):
    def build(self):
        font_name = find_system_font()
        if font_name:
            LabelBase.register(name="Roboto", fn_regular=font_name)
        self.sm = ScreenManager()
        self.sm.add_widget(ImageImportScreen(name="image_import_screen"))
        self.sm.add_widget(ImageProcessScreen(name="image_process_screen"))
        return self.sm


if __name__ == "__main__":
    MyApp().run()
