from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
import os

class Notepad(BoxLayout):
    def __init__(self, data_dir, **kwargs):
        super().__init__(orientation='vertical', spacing=2, **kwargs)
        self.data_dir = data_dir
        self.notes_file = os.path.join(data_dir, 'notepad_notes.txt')

        # 标题和按钮
        top = BoxLayout(size_hint_y=0.15)
        top.add_widget(Label(text='写字板', size_hint_x=0.3))
        btn_save = Button(text='保存', size_hint_x=0.2)
        btn_save.bind(on_press=self.save_notes)
        top.add_widget(btn_save)
        btn_clear = Button(text='清空', size_hint_x=0.2)
        btn_clear.bind(on_press=self.clear_notes)
        top.add_widget(btn_clear)
        btn_load = Button(text='加载', size_hint_x=0.3)
        btn_load.bind(on_press=self.load_file)
        top.add_widget(btn_load)
        self.add_widget(top)

        self.text_input = TextInput(text='', multiline=True)
        self.add_widget(self.text_input)

        self.load_notes()

    def load_notes(self):
        try:
            if os.path.exists(self.notes_file):
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    self.text_input.text = f.read()
        except:
            pass

    def save_notes(self, instance):
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                f.write(self.text_input.text)
        except:
            pass

    def clear_notes(self, instance):
        self.text_input.text = ''

    def load_file(self, instance):
        # 简易文件选择器（简化，使用固定路径）
        pass