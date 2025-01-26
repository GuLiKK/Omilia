import os
import yaml

def load_config_yml(filepath: str = os.path.join(os.getcwd(), "config", "config.yaml")) -> None: #config_example.yaml
    """
    Читает YAML-файл и ставит ключи как переменные окружения.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Config file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for key, val in data.items():
        os.environ[key] = str(val)
