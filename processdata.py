import os
import json
import datetime

class ProcessData:
    def __init__(self, device_id, process_type, input_mode, data_dir):
        self.device_id = device_id
        self.process_type = process_type
        self.input_mode = input_mode
        self.data_dir = data_dir

        self.DATA_FILE = os.path.join(data_dir, f'counter_data_{device_id}_{process_type}.json')

        self.DEFAULT_TARGET = 3000.0
        self.DEFAULT_TOLERANCE = 500.0
        self.DEFAULT_HOUR_TARGET = 168

        self.batches = []          # [{'batch_id': str, 'value': float}]
        self.operation_stack = []

        self.over_target_upper = False
        self.below_target_lower = False
        self.hour_over_target = False
        self.TARGET = self.DEFAULT_TARGET
        self.TOLERANCE = self.DEFAULT_TOLERANCE
        self.HOUR_TARGET = self.DEFAULT_HOUR_TARGET
        self.last_liquid_change_datetime = None
        self.current_hour_count = 0
        self.has_decimal = False
        self.liquid_change_reminded = False
        self.liquid_change_blocked = False

        self.load_data()
        self._update_total_from_batches()
        self.update_hour_count()
        self.check_target_limits()

    @property
    def LOWER_LIMIT(self):
        return max(0, self.TARGET - self.TOLERANCE)

    @property
    def UPPER_LIMIT(self):
        return self.TARGET + self.TOLERANCE

    @property
    def total(self):
        return sum(b['value'] for b in self.batches)

    def load_data(self):
        try:
            if os.path.exists(self.DATA_FILE):
                with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.batches = data.get('batches', [])
                self.TARGET = float(data.get('target', self.DEFAULT_TARGET))
                self.TOLERANCE = float(data.get('tolerance', self.DEFAULT_TOLERANCE))
                self.HOUR_TARGET = int(data.get('hour_target', self.DEFAULT_HOUR_TARGET))
                self.last_liquid_change_datetime = data.get('last_liquid_change_datetime')
                self.input_mode = data.get('input_mode', self.input_mode)
                self.liquid_change_reminded = data.get('liquid_change_reminded', False)
                self.liquid_change_blocked = data.get('liquid_change_blocked', False)
                self.has_decimal = any(b['value'] != int(b['value']) for b in self.batches)
        except:
            self.batches = []

    def save_data(self):
        try:
            data = {
                'batches': self.batches,
                'target': self.TARGET,
                'tolerance': self.TOLERANCE,
                'hour_target': self.HOUR_TARGET,
                'last_liquid_change_datetime': self.last_liquid_change_datetime,
                'input_mode': self.input_mode,
                'device_id': self.device_id,
                'process_type': self.process_type,
                'liquid_change_reminded': self.liquid_change_reminded,
                'liquid_change_blocked': self.liquid_change_blocked
            }
            with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass

    def update_hour_count(self):
        if self.last_liquid_change_datetime:
            try:
                last_dt = datetime.datetime.strptime(self.last_liquid_change_datetime, '%Y-%m-%d %H:%M:%S')
                now = datetime.datetime.now()
                total_seconds = (now - last_dt).total_seconds()
                self.current_hour_count = total_seconds / 3600
            except:
                self.current_hour_count = 0
        else:
            self.current_hour_count = 0
        return self.current_hour_count

    def format_number(self, num):
        if self.has_decimal or (isinstance(num, float) and num != int(num)):
            return f'{num:.2f}'
        return str(int(num))

    def format_hours(self, hours):
        try:
            total_seconds = int(hours * 3600)
            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            if h > 0:
                return f'{h}小时{m}分{s}秒'
            elif m > 0:
                return f'{m}分{s}秒'
            else:
                return f'{s}秒'
        except:
            return str(hours)

    def add_batch(self, batch_id, value):
        if value != int(value):
            self.has_decimal = True
        self.operation_stack.append({
            'type': 'add_batch',
            'batch': {'batch_id': batch_id, 'value': value},
            'previous_total': self.total
        })
        self.batches.append({'batch_id': batch_id, 'value': value})
        self.check_target_limits()
        return self.total

    def undo_last_action(self):
        if not self.operation_stack:
            return None
        last = self.operation_stack.pop()
        if last['type'] == 'add_batch':
            self.batches.pop()
        elif last['type'] == 'reset':
            self.batches = last['previous_batches']
        elif last['type'] == 'set_target_tolerance':
            self.TARGET = last['previous_target']
            self.TOLERANCE = last['previous_tolerance']
        elif last['type'] == 'set_hour_target':
            self.HOUR_TARGET = last['previous_hour_target']
        self._update_total_from_batches()
        self.check_target_limits()
        return last

    def check_decimal_status(self):
        self.has_decimal = any(b['value'] != int(b['value']) for b in self.batches)

    def _update_total_from_batches(self):
        self.has_decimal = any(b['value'] != int(b['value']) for b in self.batches)

    def reset_total(self, add_sample=True):
        self.operation_stack.append({
            'type': 'reset',
            'previous_batches': self.batches.copy()
        })
        self.batches = []
        self.has_decimal = False
        if add_sample:
            self.batches.append({'batch_id': '样片', 'value': 1.0})
        self.last_liquid_change_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.liquid_change_reminded = False
        self.liquid_change_blocked = False
        self.update_hour_count()
        self.check_target_limits()
        return self.total

    def set_target_and_tolerance(self, new_target, new_tolerance):
        self.operation_stack.append({
            'type': 'set_target_tolerance',
            'previous_target': self.TARGET,
            'previous_tolerance': self.TOLERANCE,
            'new_target': new_target,
            'new_tolerance': new_tolerance
        })
        self.TARGET = new_target
        self.TOLERANCE = new_tolerance
        self.check_target_limits()
        return self.TARGET, self.TOLERANCE

    def set_hour_target(self, new_hour_target):
        self.operation_stack.append({
            'type': 'set_hour_target',
            'previous_hour_target': self.HOUR_TARGET,
            'new_hour_target': new_hour_target
        })
        self.HOUR_TARGET = new_hour_target
        self.check_target_limits()
        return self.HOUR_TARGET

    def reset_hour_count(self):
        self.last_liquid_change_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.update_hour_count()
        self.save_data()

    def check_target_limits(self):
        self.over_target_upper = self.total > self.UPPER_LIMIT
        self.below_target_lower = self.total >= self.LOWER_LIMIT and self.total < self.TARGET
        self.update_hour_count()
        self.hour_over_target = self.current_hour_count >= self.HOUR_TARGET
        if self.over_target_upper or self.hour_over_target:
            self.liquid_change_blocked = True
        return (self.over_target_upper, self.below_target_lower, self.hour_over_target)

    def check_liquid_change_reminder(self):
        messages = []
        if self.over_target_upper:
            messages.append(f'片数已达上限 ({self.format_number(self.UPPER_LIMIT)})')
        if self.hour_over_target:
            h = self.format_hours(self.current_hour_count)
            t = self.format_hours(self.HOUR_TARGET)
            messages.append(f'时间已达目标 ({h}/{t})')
        if self.over_target_upper or self.hour_over_target:
            return '强制', '请立即换液！\n' + '\n'.join(messages)
        if self.total >= self.LOWER_LIMIT and self.total < self.TARGET:
            if not self.liquid_change_reminded:
                self.liquid_change_reminded = True
                self.save_data()
            return '提醒', f'片数: {self.format_number(self.total)}/{self.format_number(self.TARGET)}'
        self.liquid_change_reminded = False
        return None, None

    def is_out_of_range(self):
        return self.over_target_upper or self.below_target_lower or self.hour_over_target

    def can_undo(self):
        return len(self.operation_stack) > 0