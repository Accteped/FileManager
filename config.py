from pathlib import Path
import json
import sys
import copy

if getattr(sys,'frozen',False):
    BASE = Path(sys.executable).parent
else:
    BASE = Path(__file__).parent
RULES_FILE = BASE / "rules.json"
DEFAULT_DATA = {
    "active": "按类型",
    "profiles": {
        "按类型": {
            "mode": "type",
            "type_rules": {
                "文本文件": [".txt", ".md"],
                "图片": [".jpg", ".png"],
                "文档": [".pdf", ".xlsx", ".ppt", ".pptx", ".doc", ".docx"],
                "视频&音频": [".mp4", ".avi", ".mov", ".mp3", ".wav", ".flac"],
                "压缩文件": [".zip", ".rar", ".7z"],
                "代码文件": [".py", ".js", ".html", ".css", ".c", ".cpp", ".php"],
            },
        },
        "按日期": {"mode": "date", "date_format": "%Y-%m-%d"},
        "按大小": {"mode": "size", "size_small": 1024, "size_large": 10485760},
    },
}

def _default():
    return copy.deepcopy(DEFAULT_DATA)

def get_active_profile(data):
    profiles = data.get("profiles", {})
    name = data.get("active", "")
    if name in profiles:
        return profiles[name]
    #找不到就默认返回第一个
    if profiles:
        return next(iter(profiles.values()))
    return {}

def get_profile(data):
    profiles = data.get("profiles", {})
    return profiles

def load():#load并处理异常情况
    default = dict(_default())
    if not RULES_FILE.exists():
        with open(RULES_FILE, 'w', encoding="UTF-8") as f:
            json.dump(default, f, ensure_ascii = False, indent = 2)
        return default
    else:
        try:
            with open(RULES_FILE, 'r', encoding="UTF-8") as f:
                data = json.load(f)
                if "profiles" not in data or "active" not in data:
                    data = default
                return data
        except (json.JSONDecodeError,OSError) as e:
            print(f"解读json失败")
            return dict(default)
    
def save_rules(rules):
    try:
        with open(
            RULES_FILE, 'w', encoding="UTF-8") as f:
            json.dump(rules, f, ensure_ascii = False, indent = 2)
        return True
    except Exception as e:
        print(f"保存规则失败: {e}") 
        return False


data = load()
profile = get_profile(data)
active_profile_name = get_active_profile(data)