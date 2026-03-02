from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
import os

from passwordmanager import PasswordManager
from logmanager import LogManager
from devicetab import DeviceLayout
from notepad import Notepad
from utils import get_data_dir


class PasswordPopup(Popup):
    def __init__(self, title, callback, action_type='normal', **kwargs):
        super().__init__(title=title, **kwargs)
        self.callback = callback
        self.action_type = action_type
        self.size_hint = (0.7, 0.4)
        self.auto_dismiss = False

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.pwd_input = TextInput(password=True, multiline=False, size_hint_y=0.3)
        layout.add_widget(self.pwd_input)

        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        btn_ok = Button(text='确定', on_press=self.verify)
        btn_cancel = Button(text='取消', on_press=self.dismiss)
        btn_layout.add_widget(btn_ok)
        btn_layout.add_widget(btn_cancel)
        layout.add_widget(btn_layout)

        self.add_widget(layout)

    def verify(self, *args):
        app = App.get_running_app()
        if app.password_manager.verify_password(self.pwd_input.text, self.action_type):
            self.dismiss()
            self.callback(True)
        else:
            # 简单错误提示
            self.pwd_input.text = ''
            self.pwd_input.hint_text = '密码错误'
            self.pwd_input.hint_text_color = (1,0,0,1)


class MainApp(App):
    def build(self):
        self.data_dir = get_data_dir(self)
        self.password_manager = PasswordManager(self.data_dir)
        self.log_manager = LogManager(self.data_dir)

        # 主布局
        root = BoxLayout(orientation='vertical', padding=5, spacing=5)

        # 顶部工具栏
        top_bar = BoxLayout(size_hint_y=0.1, spacing=5)
        self.scan_device_input = TextInput(hint_text='扫描设备号', multiline=False,
                                           size_hint_x=0.3)
        self.scan_device_input.bind(on_text_validate=self.on_scan_device)
        top_bar.add_widget(self.scan_device_input)

        btn_add_device = Button(text='+添加设备', size_hint_x=0.15)
        btn_add_device.bind(on_press=self.add_device)
        top_bar.add_widget(btn_add_device)

        btn_change_pwd = Button(text='修改密码', size_hint_x=0.15)
        btn_change_pwd.bind(on_press=self.change_password)
        top_bar.add_widget(btn_change_pwd)

        # 拉伸占位
        top_bar.add_widget(Widget(size_hint_x=1))

        root.add_widget(top_bar)

        # 中间：设备选项卡
        self.tab_panel = TabbedPanel(do_default_tab=False)
        root.add_widget(self.tab_panel)

        # 底部：统计+写字板
        bottom = BoxLayout(size_hint_y=0.3, spacing=5)
        left_stats = BoxLayout(orientation='vertical', size_hint_x=0.3)
        self.stats_label = Label(text='设备数量: 0\n工艺数量: 0', halign='left',
                                  valign='top', size_hint_y=1)
        left_stats.add_widget(self.stats_label)
        bottom.add_widget(left_stats)

        right_notepad = Notepad(self.data_dir)
        bottom.add_widget(right_notepad)

        root.add_widget(bottom)

        # 加载已有设备
        self.load_existing_devices()
        if not self.device_tabs:
            # 默认创建两个设备示例
            Clock.schedule_once(lambda dt: self.add_device(None, initial=True), 0)

        # 每秒更新时间累计
        Clock.schedule_interval(self.update_all_hour_counts, 1)

        return root

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.device_tabs = {}          # {device_id: device_layout}

    def get_data_dir(self):
        return self.data_dir

    def load_existing_devices(self):
        import json
        for fname in os.listdir(self.data_dir):
            if fname.startswith('counter_data_') and fname.endswith('.json'):
                # 格式: counter_data_{device_id}_{process_type}.json
                parts = fname.replace('counter_data_', '').replace('.json', '').split('_')
                if len(parts) >= 2:
                    device_id = parts[0]
                    if device_id not in self.device_tabs:
                        self.create_device_tab(device_id)

    def create_device_tab(self, device_id):
        header = TabbedPanelHeader(text=f'设备: {device_id}')
        device_layout = DeviceLayout(device_id, self)
        header.content = device_layout
        self.tab_panel.add_widget(header)
        self.device_tabs[device_id] = device_layout
        self.update_stats()

    def add_device(self, instance, initial=False):
        if not initial:
            # 需要密码验证
            def on_pwd_success(success):
                if success:
                    self._show_add_device_dialog()
            PasswordPopup('输入密码', on_pwd_success).open()
        else:
            self._show_add_device_dialog(initial=True)

    def _show_add_device_dialog(self, initial=False):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        p_input = TextInput(hint_text='输入设备号', multiline=False)
        content.add_widget(p_input)
        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        btn_ok = Button(text='确定')
        btn_cancel = Button(text='取消')
        btn_layout.add_widget(btn_ok)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)

        popup = Popup(title='添加设备', content=content, size_hint=(0.5, 0.3))
        def on_ok(*args):
            device_id = p_input.text.strip()
            if not device_id:
                return
            if device_id in self.device_tabs:
                # 设备已存在
                return
            self.create_device_tab(device_id)
            self.log_manager.add_log_entry({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'device_id': device_id,
                'process_type': '系统',
                'action': '添加设备',
                'value': '',
                'total': 0.0,
                'hour_count': 0,
                'target': 0.0,
                'tolerance': 0.0,
                'hour_target': 0,
                'input_mode': ''
            })
            popup.dismiss()
        btn_ok.bind(on_press=on_ok)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def delete_device(self, device_id):
        # 删除设备选项卡
        for tab in self.tab_panel.tab_list:
            if tab.content == self.device_tabs.get(device_id):
                self.tab_panel.remove_widget(tab)
                break
        del self.device_tabs[device_id]
        # 删除对应的数据文件
        for fname in os.listdir(self.data_dir):
            if fname.startswith(f'counter_data_{device_id}_'):
                os.remove(os.path.join(self.data_dir, fname))
        self.update_stats()

    def on_scan_device(self, instance):
        device_id = instance.text.strip()
        instance.text = ''
        if device_id in self.device_tabs:
            # 切换到对应选项卡
            for tab in self.tab_panel.tab_list:
                if tab.content == self.device_tabs[device_id]:
                    self.tab_panel.switch_to(tab)
                    break
        else:
            # 设备不存在，询问是否添加
            pass

    def change_password(self, instance):
        # 修改密码逻辑（类似原版）
        pass

    def update_stats(self):
        process_count = sum(len(tab.process_data) for tab in self.device_tabs.values())
        self.stats_label.text = f'设备数量: {len(self.device_tabs)}\n工艺数量: {process_count}'

    def update_all_hour_counts(self, dt):
        # 更新所有工艺的小时累计，并刷新表格显示
        for device_layout in self.device_tabs.values():
            device_layout.update_hour_counts()


if __name__ == '__main__':
    from kivy.uix.widget import Widget
    from datetime import datetime
    MainApp().run()