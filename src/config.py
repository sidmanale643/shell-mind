import json
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path.home() / ".shellmind"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "agent_mode": False
}

class ConfigManager:
    def __init__(self):
        self.config_path = CONFIG_FILE
        self._ensure_config_dir()
        self.config = self._load_config()

    def _ensure_config_dir(self):
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except OSError as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value
        self.save_config()

    @property
    def agent_mode(self) -> bool:
        return self.get("agent_mode", False)

    @agent_mode.setter
    def agent_mode(self, value: bool):
        self.set("agent_mode", value)
