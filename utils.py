import os

def get_data_dir(app):
    """获取应用私有数据目录"""
    return app.user_data_dir