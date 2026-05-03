import os
from pathlib import Path
from typing import Any

import yaml

from core.logger import logger
from core.settings import ensure_runtime_dirs, load_settings


def get_testdata_dir() -> Path:
    settings = ensure_runtime_dirs(load_settings())
    return settings.paths.env_testdata_dir


def get_yaml_path(file_name: str) -> str:
    """
    获取 YAML 文件完整路径。
    绝对路径直接返回；相对路径则基于当前环境 testdata 目录。
    """
    if os.path.isabs(file_name):
        return file_name
    return str(get_testdata_dir() / file_name)


def iter_testdata_files() -> list[Path]:
    """遍历当前环境 testdata 目录下所有 data_*.yaml 文件。"""
    data_dir = get_testdata_dir()
    if not data_dir.exists():
        return []
    return sorted(data_dir.glob("data_*.yaml"))


def read_yaml(file_name: str) -> Any:
    """读取 YAML 文件，返回解析后的数据（字典/列表）。"""
    yaml_file_path = get_yaml_path(file_name)
    try:
        with open(yaml_file_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file) or []
    except FileNotFoundError as exc:
        raise Exception(f"未找到 YAML 文件：{yaml_file_path}") from exc
    except yaml.YAMLError as exc:
        raise Exception(f"YAML 文件语法错误：{yaml_file_path}") from exc


def write_yaml(file_name: str, data: Any) -> None:
    """覆盖写入数据到 YAML 文件（默认在当前环境 testdata 目录下）。"""
    yaml_file_path = get_yaml_path(file_name)
    os.makedirs(os.path.dirname(yaml_file_path), exist_ok=True)

    try:
        with open(yaml_file_path, "w", encoding="utf-8") as file:
            yaml.dump(data, file, allow_unicode=True, default_flow_style=False)
            logger.info(f"Data written to {yaml_file_path}")
    except Exception as exc:
        raise Exception(f"写入 YAML 文件失败 {yaml_file_path}: {exc}") from exc
