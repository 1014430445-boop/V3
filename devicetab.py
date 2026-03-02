from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.app import App
from datetime import datetime
import os

from processdata import ProcessData


class BatchRow(BoxLayout):
    """单行批次显示"""
    def __init__(self, device_layout, process_type, batch_index, batch_data, **kwargs):
        super().__init__(size_hint_y=None, height=40, spacing=2, **kwargs)
        self.device_layout = device_layout
        self.process_type = process_type
        self.batch_index = batch_index

        process_data = device_layout.process_data[process_type]

        # 序号（全局）
        self.add_widget(Label(text='?', size_hint_x=0.05))
        # 工艺种类
        self.add_widget(Label(text=process_type, size_hint_x=0.12))
        # 批次号
        self.add_widget(Label(text=batch_data['batch_id'], size_hint_x=0.15))
        # 片数
        self.add_widget(Label(text=process_data.format_number(batch_data['value']), size_hint_x=0.08))
        # 累计片数
        self.add_widget(Label(text=process_data.format_number(process_data.total), size_hint_x=0.08))
        # 片数目标±
        target_str = f"{process_data.format_number(process_data.TARGET)}±{process_data.format_number(process_data.TOLERANCE)}"
        self.add_widget(Label(text=target_str, size_hint_x=0.15))
        # 状态
        status = '需换液' if process_data.is_out_of_range() else '正常'
        self.add_widget(Label(text=status, size_hint_x=0.08))
        # 输入模式
        mode = '整数' if process_data.input_mode == 'integer' else '小数'
        self.add_widget(Label(text=mode, size_hint_x=0.08))
        # 操作按钮
        btn = Button(text='操作', size_hint_x=0.1)
        btn.bind(on_press=self.show_menu)
        self.add_widget(btn)

    def show_menu(self, instance):
        # 弹出操作菜单Popup
        self.device_layout.show_batch_menu(self.process_type, self.batch_index)


class DeviceLayout(BoxLayout):
    def __init__(self, device_id, app, **kwargs):
        super().__init__(orientation='vertical', spacing=5, padding=5, **kwargs)
        self.device_id = device_id
        self.app = app
        self.process_data = {}          # {process_type: ProcessData}
        self.batch_rows = []             # 用于保存所有BatchRow实例（简化刷新）

        # 扫描输入
        self.scan_input = TextInput(hint_text='扫描批次号', multiline=False, size_hint_y=0.08)
        self.scan_input.bind(on_text_validate=self.on_scan)
        self.add_widget(self.scan_input)

        # 批次列表标题栏（固定）
        header = BoxLayout(size_hint_y=0.08, height=30)
        headers = ['序号', '工艺', '批次号', '片数', '累计', '目标±', '状态', '模式', '操作']
        widths = [0.05, 0.12, 0.15, 0.08, 0.08, 0.15, 0.08, 0.08, 0.1]
        for h, w in zip(headers, widths):
            header.add_widget(Label(text=h, size_hint_x=w, bold=True))
        self.add_widget(header)

        # 可滚动的列表区域
        self.scroll = ScrollView(size_hint_y=0.7)
        self.list_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

        # 底部按钮栏
        btn_bar = BoxLayout(size_hint_y=0.1, spacing=5)
        btn_add_process = Button(text='+添加工艺')
        btn_add_process.bind(on_press=self.add_process)
        btn_bar.add_widget(btn_add_process)
        btn_clear_all = Button(text='清空所有')
        btn_clear_all.bind(on_press=self.clear_all_processes)
        btn_bar.add_widget(btn_clear_all)
        btn_delete_device = Button(text='删除设备')
        btn_delete_device.bind(on_press=self.delete_device)
        btn_bar.add_widget(btn_delete_device)
        self.add_widget(btn_bar)

        # 加载已有工艺
        self.load_existing_processes()

    def load_existing_processes(self):
        # 扫描数据文件
        import json
        for fname in os.listdir(self.app.data_dir):
            if fname.startswith(f'counter_data_{self.device_id}_') and fname.endswith('.json'):
                parts = fname.replace('counter_data_', '').replace('.json', '').split('_')
                if len(parts) >= 2:
                    process_type = '_'.join(parts[1:])
                    try:
                        with open(os.path.join(self.app.data_dir, fname), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        input_mode = data.get('input_mode', 'integer')
                        pd = ProcessData(self.device_id, process_type, input_mode, self.app.data_dir)
                        pd.batches = data.get('batches', [])
                        pd.TARGET = data.get('target', pd.DEFAULT_TARGET)
                        pd.TOLERANCE = data.get('tolerance', pd.DEFAULT_TOLERANCE)
                        pd.HOUR_TARGET = data.get('hour_target', pd.DEFAULT_HOUR_TARGET)
                        pd.last_liquid_change_datetime = data.get('last_liquid_change_datetime')
                        pd.liquid_change_reminded = data.get('liquid_change_reminded', False)
                        pd.liquid_change_blocked = data.get('liquid_change_blocked', False)
                        pd.has_decimal = any(b['value'] != int(b['value']) for b in pd.batches)
                        pd.update_hour_count()
                        pd.check_target_limits()
                        self.process_data[process_type] = pd
                    except Exception as e:
                        print(f'加载工艺 {process_type} 失败: {e}')
        self.refresh_table()

    def refresh_table(self):
        # 清空列表布局
        self.list_layout.clear_widgets()
        self.batch_rows.clear()
        # 为每个工艺的每个批次添加行
        for process_type, pd in self.process_data.items():
            for idx, batch in enumerate(pd.batches):
                row = BatchRow(self, process_type, idx, batch)
                self.list_layout.add_widget(row)
                self.batch_rows.append(row)
        # 更新序号（简单实现：重新赋值）
        for i, row in enumerate(self.batch_rows, 1):
            # 由于我们无法直接修改行内的Label，这里简化：重新构建所有行
            # 更优雅的做法是自定义Row控件并暴露序号属性，此处略
            pass

    def add_process(self, instance):
        # 弹出添加工艺对话框
        # 需要密码验证，这里简化，假设密码验证已通过
        def show_add_dialog():
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            p_name = TextInput(hint_text='工艺种类', multiline=False)
            content.add_widget(p_name)
            # 输入模式选择
            mode_box = BoxLayout(size_hint_y=0.3)
            mode_int = Button(text='整数', state='down' if self.app.integer_mode else 'normal')
            mode_dec = Button(text='小数')
            # ... 处理切换
            content.add_widget(mode_box)
            batch_id = TextInput(hint_text='初始批次号', text=f'批次_{datetime.now().strftime("%Y%m%d%H%M%S")}')
            content.add_widget(batch_id)
            value_input = TextInput(hint_text='初始片数', multiline=False)
            content.add_widget(value_input)
            btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
            btn_ok = Button(text='确定')
            btn_cancel = Button(text='取消')
            btn_layout.add_widget(btn_ok)
            btn_layout.add_widget(btn_cancel)
            content.add_widget(btn_layout)

            popup = Popup(title='添加工艺', content=content, size_hint=(0.7, 0.6))
            def on_ok(*args):
                process_type = p_name.text.strip()
                if not process_type or process_type in self.process_data:
                    return
                batch = batch_id.text.strip()
                val_str = value_input.text.strip()
                try:
                    val = float(val_str)
                    # 这里应验证范围，简化
                except:
                    return
                # 创建工艺
                pd = ProcessData(self.device_id, process_type, 'integer', self.app.data_dir)
                pd.add_batch(batch, val)
                pd.save_data()
                self.process_data[process_type] = pd
                self.refresh_table()
                popup.dismiss()
            btn_ok.bind(on_press=on_ok)
            btn_cancel.bind(on_press=popup.dismiss)
            popup.open()

        # 密码验证
        from main import PasswordPopup
        PasswordPopup('密码验证', lambda s: show_add_dialog() if s else None).open()

    def on_scan(self, instance):
        batch_id = instance.text.strip()
        instance.text = ''
        # 简化的处理：如果有待处理换液，需特殊处理；此处默认选取第一个工艺
        if not self.process_data:
            return
        # 取第一个工艺
        process_type = next(iter(self.process_data.keys()))
        pd = self.process_data[process_type]
        # 检查换液
        if pd.liquid_change_blocked:
            # 弹出换液确认
            self.show_liquid_change_dialog(process_type, batch_id)
        else:
            # 直接输入片数
            self.prompt_for_pieces(process_type, batch_id)

    def show_liquid_change_dialog(self, process_type, batch_id):
        pd = self.process_data[process_type]
        msg = ''
        if pd.over_target_upper:
            msg += f'片数已达上限({pd.format_number(pd.UPPER_LIMIT)})\n'
        if pd.hour_over_target:
            msg += f'时间已达目标({pd.format_hours(pd.current_hour_count)}/{pd.format_hours(pd.HOUR_TARGET)})\n'
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=f'工艺 {process_type} 需要换液！\n{msg}是否已完成换液？'))
        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        btn_yes = Button(text='是（清空并导出日志）')
        btn_no = Button(text='否（取消添加）')
        btn_layout.add_widget(btn_yes)
        btn_layout.add_widget(btn_no)
        content.add_widget(btn_layout)
        popup = Popup(title='换液确认', content=content, size_hint=(0.7, 0.4))
        def on_yes(*args):
            # 导出日志（当前批次的日志）
            logs = self.get_current_batch_logs(process_type)
            if logs:
                # 导出到私有目录
                export_path = os.path.join(self.app.data_dir, f'换液日志_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
                self.app.log_manager.export_to_csv(export_path, logs)
            # 重置
            pd.reset_total(add_sample=True)
            pd.save_data()
            self.refresh_table()
            popup.dismiss()
            # 提示重新输入批次
            self.scan_input.text = batch_id
            self.scan_input.focus = True
        btn_yes.bind(on_press=on_yes)
        btn_no.bind(on_press=popup.dismiss)
        popup.open()

    def get_current_batch_logs(self, process_type):
        # 简化：返回当前工艺的所有批次（作为日志）
        pd = self.process_data[process_type]
        logs = []
        for batch in pd.batches:
            logs.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'device_id': self.device_id,
                'process_type': process_type,
                'action': '扫码添加',
                'value': f"{batch['batch_id']}:{batch['value']}",
                'total': pd.total,
                'hour_count': pd.current_hour_count,
                'target': pd.TARGET,
                'tolerance': pd.TOLERANCE,
                'hour_target': pd.HOUR_TARGET,
                'input_mode': pd.input_mode
            })
        return logs

    def prompt_for_pieces(self, process_type, batch_id):
        pd = self.process_data[process_type]
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=f'工艺: {process_type}\n批次: {batch_id}\n当前累计: {pd.format_number(pd.total)}'))
        pieces_input = TextInput(hint_text='输入片数', multiline=False)
        content.add_widget(pieces_input)
        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        btn_ok = Button(text='确定')
        btn_cancel = Button(text='取消')
        btn_layout.add_widget(btn_ok)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)
        popup = Popup(title='输入片数', content=content, size_hint=(0.6, 0.4))
        def on_ok(*args):
            try:
                val = float(pieces_input.text)
                # 这里应检查范围，简化
                pd.add_batch(batch_id, val)
                pd.save_data()
                self.refresh_table()
                self.app.log_manager.add_log_entry({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'device_id': self.device_id,
                    'process_type': process_type,
                    'action': '扫码添加',
                    'value': f'{batch_id}:{val}',
                    'total': pd.total,
                    'hour_count': pd.current_hour_count,
                    'target': pd.TARGET,
                    'tolerance': pd.TOLERANCE,
                    'hour_target': pd.HOUR_TARGET,
                    'input_mode': pd.input_mode
                })
                popup.dismiss()
                # 检查换液提醒
                typ, msg = pd.check_liquid_change_reminder()
                if typ:
                    self.show_reminder(typ, msg)
            except:
                pass
        btn_ok.bind(on_press=on_ok)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def show_reminder(self, typ, msg):
        popup = Popup(title=typ + '提醒', content=Label(text=msg), size_hint=(0.6, 0.3))
        popup.open()

    def clear_all_processes(self, instance):
        # 密码验证后清空所有工艺的批次
        pass

    def delete_device(self, instance):
        # 密码验证后删除设备
        from main import PasswordPopup
        PasswordPopup('删除设备', lambda s: self.app.delete_device(self.device_id) if s else None).open()

    def show_batch_menu(self, process_type, batch_index):
        # 弹出工艺操作菜单（添加、撤销、重置、设置目标等）
        pd = self.process_data[process_type]
        content = BoxLayout(orientation='vertical', spacing=5, padding=10)
        btn_add = Button(text='添加批次', size_hint_y=None, height=40)
        btn_undo = Button(text='撤销', size_hint_y=None, height=40)
        btn_reset = Button(text='重置', size_hint_y=None, height=40)
        btn_set_target = Button(text='设置片数目标±', size_hint_y=None, height=40)
        btn_set_hour = Button(text='设置时间目标', size_hint_y=None, height=40)
        btn_delete = Button(text='删除工艺', size_hint_y=None, height=40)
        btn_cancel = Button(text='取消', size_hint_y=None, height=40)

        def on_add(*args):
            popup.dismiss()
            # 弹出添加批次对话框（类似prompt_for_pieces但需要批次号）
            pass

        def on_undo(*args):
            # 需要撤销专用密码
            from main import PasswordPopup
            def do_undo(s):
                if s:
                    pd.undo_last_action()
                    pd.save_data()
                    self.refresh_table()
            PasswordPopup('撤销密码', do_undo, action_type='undo').open()
            popup.dismiss()

        def on_reset(*args):
            from main import PasswordPopup
            def do_reset(s):
                if s:
                    pd.reset_total(add_sample=True)
                    pd.save_data()
                    self.refresh_table()
            PasswordPopup('重置密码', do_reset).open()
            popup.dismiss()

        def on_set_target(*args):
            from main import PasswordPopup
            def do_set(s):
                if s:
                    # 显示设置对话框
                    self.show_set_target_dialog(process_type)
            PasswordPopup('设置密码', do_set).open()
            popup.dismiss()

        def on_set_hour(*args):
            from main import PasswordPopup
            def do_set(s):
                if s:
                    self.show_set_hour_dialog(process_type)
            PasswordPopup('设置密码', do_set).open()
            popup.dismiss()

        def on_delete(*args):
            from main import PasswordPopup
            def do_del(s):
                if s:
                    del self.process_data[process_type]
                    # 删除数据文件
                    fname = os.path.join(self.app.data_dir, f'counter_data_{self.device_id}_{process_type}.json')
                    if os.path.exists(fname):
                        os.remove(fname)
                    self.refresh_table()
            PasswordPopup('删除密码', do_del).open()
            popup.dismiss()

        btn_add.bind(on_press=on_add)
        btn_undo.bind(on_press=on_undo)
        btn_reset.bind(on_press=on_reset)
        btn_set_target.bind(on_press=on_set_target)
        btn_set_hour.bind(on_press=on_set_hour)
        btn_delete.bind(on_press=on_delete)
        btn_cancel.bind(on_press=lambda x: popup.dismiss())

        content.add_widget(btn_add)
        content.add_widget(btn_undo)
        content.add_widget(btn_reset)
        content.add_widget(btn_set_target)
        content.add_widget(btn_set_hour)
        content.add_widget(btn_delete)
        content.add_widget(btn_cancel)

        popup = Popup(title='操作菜单', content=content, size_hint=(0.5, 0.7))
        popup.open()

    def show_set_target_dialog(self, process_type):
        # 设置片数目标±对话框
        pd = self.process_data[process_type]
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=f'当前: {pd.TARGET} ± {pd.TOLERANCE}'))
        t_input = TextInput(hint_text='目标片数', multiline=False)
        tol_input = TextInput(hint_text='±片数', multiline=False)
        content.add_widget(t_input)
        content.add_widget(tol_input)
        btn_ok = Button(text='确定')
        btn_cancel = Button(text='取消')
        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        btn_layout.add_widget(btn_ok)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)
        popup = Popup(title='设置片数目标±', content=content, size_hint=(0.6, 0.5))
        def on_ok(*args):
            try:
                new_t = float(t_input.text)
                new_tol = float(tol_input.text)
                pd.set_target_and_tolerance(new_t, new_tol)
                pd.save_data()
                self.refresh_table()
                popup.dismiss()
            except:
                pass
        btn_ok.bind(on_press=on_ok)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def show_set_hour_dialog(self, process_type):
        # 设置时间目标
        pd = self.process_data[process_type]
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=f'当前: {pd.HOUR_TARGET} 小时'))
        h_input = TextInput(hint_text='目标小时数', multiline=False)
        content.add_widget(h_input)
        btn_ok = Button(text='确定')
        btn_cancel = Button(text='取消')
        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        btn_layout.add_widget(btn_ok)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)
        popup = Popup(title='设置时间目标', content=content, size_hint=(0.6, 0.4))
        def on_ok(*args):
            try:
                new_h = int(h_input.text)
                pd.set_hour_target(new_h)
                pd.save_data()
                self.refresh_table()
                popup.dismiss()
            except:
                pass
        btn_ok.bind(on_press=on_ok)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def update_hour_counts(self):
        # 更新时间累计
        for pd in self.process_data.values():
            pd.update_hour_count()
        # 可刷新表格（比如改变状态颜色），简化不实现
        pass