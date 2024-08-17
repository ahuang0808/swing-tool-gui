from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from screens.image import ImageImportScreen
from screens.image import ImageProcessScreen


class MyApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(ImageImportScreen(name="image_import_screen"))
        self.sm.add_widget(ImageProcessScreen(name="image_process_screen"))
        return self.sm


if __name__ == "__main__":
    MyApp().run()
