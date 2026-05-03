import datetime
from pathlib import Path

from core.logger import logger


def _clean_old_files(days_to_keep=1, target_dir="runtime", patterns=("*",), recursive=True):
    """清理目标目录下超过保留天数的文件，仅删除文件，不删除目录。"""
    target_path = Path(target_dir)
    logger.info(f"开始清理旧文件，保留最近 {days_to_keep} 天，目录: {target_path}")

    if not target_path.exists():
        logger.info(f"目录 '{target_path}' 不存在，跳过清理。")
        return

    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
    deleted_count = 0

    for pattern in patterns:
        iterator = target_path.rglob(pattern) if recursive else target_path.glob(pattern)
        for file_path in iterator:
            if not file_path.is_file():
                continue
            try:
                file_mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    file_path.unlink()
                    deleted_count += 1
            except Exception as exc:
                logger.error(f"处理文件失败 {file_path}: {exc}")

    logger.info(f"清理完成，共删除 {deleted_count} 个旧文件。")


def _resolve_runtime_root(path_value):
    """兼容 runtime/logs/dev 与单次运行 report/.../logs 这两种目录布局。"""
    current_path = Path(path_value)

    if current_path.name.lower() in {"dev", "test"} and current_path.parent.name == "logs":
        return current_path.parents[1]
    if current_path.name == "logs":
        return current_path.parent
    return current_path


def clean_old_screenshots(days_to_keep=1, screenshots_dir="runtime/screenshots"):
    """清理截图目录下的旧截图文件。"""
    _clean_old_files(
        days_to_keep=days_to_keep,
        target_dir=screenshots_dir,
        patterns=("*.png",),
        recursive=True,
    )


def clean_old_logs(days_to_keep=1, logs_dir="runtime", patterns=("*",)):
    """清理 runtime 目录下的旧文件。"""
    runtime_root = _resolve_runtime_root(logs_dir)
    _clean_old_files(
        days_to_keep=days_to_keep,
        target_dir=runtime_root, # type: ignore
        patterns=patterns,
        recursive=True,
    )


def clean_old_runtime(days_to_keep=1, runtime_dir="runtime"):
    """清理整个 runtime 目录下超过保留天数的旧文件（含截图、日志、allure 产物）。"""
    _clean_old_files(
        days_to_keep=days_to_keep,
        target_dir=runtime_dir,
        patterns=("*",),
        recursive=True,
    )
