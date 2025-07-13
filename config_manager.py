import json
import os

class ConfigManager:
    """加载和管理 config.json 文件。"""

    def __init__(self, path="config.json"):
        self.path = path
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.path): return None
        with open(self.path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get(self, key, default=None):
        return self.config.get(key, default) if self.config else default
