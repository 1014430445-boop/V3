import os
import json

class PasswordManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.password_file = os.path.join(data_dir, 'password_config.json')
        self.DEFAULT_PASSWORD = 'admin'
        self.UNDO_PASSWORD = '1'
        self.load_password()

    def load_password(self):
        try:
            if os.path.exists(self.password_file):
                with open(self.password_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_password = data.get('password', self.DEFAULT_PASSWORD)
            else:
                self.current_password = self.DEFAULT_PASSWORD
                self.save_password()
        except:
            self.current_password = self.DEFAULT_PASSWORD

    def save_password(self):
        try:
            with open(self.password_file, 'w', encoding='utf-8') as f:
                json.dump({'password': self.current_password}, f)
        except:
            pass

    def verify_password(self, password, action_type='normal'):
        if action_type == 'undo':
            return password == self.UNDO_PASSWORD
        else:
            return password == self.current_password

    def change_password(self, old_password, new_password):
        if not self.verify_password(old_password):
            return False, '旧密码不正确'
        if not new_password.strip():
            return False, '新密码不能为空'
        self.current_password = new_password
        self.save_password()
        return True, '密码修改成功'