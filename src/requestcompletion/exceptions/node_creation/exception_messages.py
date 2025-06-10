import yaml
import os

_yaml_path = os.path.join(os.path.dirname(__file__), "exception_messages.yaml")
with open(_yaml_path, "r", encoding="utf-8") as f:
    _messages = yaml.safe_load(f)

def get_message(key):
    return _messages[key]

def get_notes(key):
    return _messages[key]
