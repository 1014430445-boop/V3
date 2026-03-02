import os
import json
import csv

class LogManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.log_file = os.path.join(data_dir, 'combined_logs.json')
        self.history_file = os.path.join(data_dir, 'history_logs.json')
        self.log_entries = []
        self.load_logs()

    def load_logs(self):
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.log_entries = json.load(f)
            else:
                self.log_entries = []
        except:
            self.log_entries = []

    def save_logs(self):
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.log_entries, f, indent=2, ensure_ascii=False)
        except:
            pass

    def add_log_entry(self, entry):
        self.log_entries.append(entry)
        if len(self.log_entries) > 1000:
            # 归档
            self.save_history_logs(self.log_entries[:100])
            self.log_entries = self.log_entries[-900:]
        self.save_logs()

    def save_history_logs(self, old_logs):
        try:
            existing = []
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            existing.extend(old_logs)
            if len(existing) > 5000:
                existing = existing[-5000:]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
        except:
            pass

    def export_to_csv(self, file_path, logs):
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['时间', '设备号', '工艺类型', '批次号', '片数', '累计片数'])
                for row in logs:
                    timestamp = row.get('timestamp', '')
                    device_id = row.get('device_id', '')
                    process_type = row.get('process_type', '')
                    value = row.get('value', '')
                    total = row.get('total', '')
                    if ':' in str(value):
                        batch_id, pieces = str(value).split(':', 1)
                    else:
                        batch_id, pieces = value, ''
                    # 格式化累计
                    try:
                        tf = float(total)
                        total_formatted = str(int(tf)) if tf == int(tf) else f'{tf:.2f}'
                    except:
                        total_formatted = str(total)
                    writer.writerow([timestamp, device_id, process_type, batch_id, pieces, total_formatted])
        except Exception as e:
            print(f'导出失败: {e}')