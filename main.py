import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import core.common as common

import pytest

from core.logger import configure_logger
from core.settings import (
    PROJECT_ROOT,
    TEST_RUN_ARTIFACTS_DIR_ENV,
    ensure_runtime_dirs,
    load_settings,
    set_current_env,
)


def _resolve_allure_cli() -> str | None:
    """Locate Allure executable; Windows often only has allure.cmd on PATH."""
    for name in ("allure", "allure.cmd", "allure.bat", "allure.exe"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _run_allure_generate(results_dir, report_dir) -> None:
    """Invoke `allure generate`. On Windows, list-form subprocess often fails (WinError 2)
    for .cmd shims from npm/Scoop; shell + list2cmdline fixes that."""
    allure_bin = _resolve_allure_cli()
    if not allure_bin:
        raise FileNotFoundError("PATH 中未找到 allure / allure.cmd")
    args = [
        allure_bin,
        "generate",
        str(results_dir),
        "-o",
        str(report_dir),
        "--clean",
    ]
    if sys.platform == "win32":
        subprocess.run(subprocess.list2cmdline(args), check=True, shell=True)
    else:
        subprocess.run(args, check=True)


def _allocate_report_run_dir() -> Path:
    """Create report/reportYYYYMMDDHHmm[/ _n] under the project root (design D4)."""
    report_base = PROJECT_ROOT / "report"
    report_base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d%H%M")
    base_name = f"report{stamp}"
    candidate = report_base / base_name
    if not candidate.exists():
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate.resolve()
    n = 1
    while True:
        alt = report_base / f"{base_name}_{n}"
        if not alt.exists():
            alt.mkdir(parents=True, exist_ok=True)
            return alt.resolve()
        n += 1


def run():
    parser = argparse.ArgumentParser(description="运行民事登记自动化测试")
    parser.add_argument(
        "--env",
        default="DEV",
        choices=["DEV", "TEST"],
        help="指定运行环境，默认 DEV",
    )
    args, pytest_args = parser.parse_known_args()

    env_name = set_current_env(args.env)
    run_dir = _allocate_report_run_dir()
    os.environ[TEST_RUN_ARTIFACTS_DIR_ENV] = str(run_dir)
    settings = ensure_runtime_dirs(load_settings(env_name))
    configure_logger(settings.paths.logs_dir)
    common.clean_old_runtime(runtime_dir=str(settings.paths.runtime_root))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = settings.paths.logs_dir / f"test_{timestamp}.log"
    allure_results_dir = settings.paths.allure_results_dir
    allure_report_dir = settings.paths.allure_report_dir

    run_args = [
        f"--env={env_name}",
        f"--alluredir={allure_results_dir}",
        "--clean-alluredir",
        f"--log-file={log_file}",
    ]
    if pytest_args:
        run_args.extend(pytest_args)
    else:
        run_args.extend(["-m", "regression"])

    exit_code = pytest.main([str(argument) for argument in run_args])

    if _resolve_allure_cli() is None:
        print("警告: PATH 中未找到 allure / allure.cmd，跳过 HTML 报告生成。")
    else:
        try:
            print(f"正在生成 {env_name} 环境 Allure 报告...")
            if allure_results_dir.exists():
                allure_report_dir.mkdir(parents=True, exist_ok=True)
                _run_allure_generate(allure_results_dir, allure_report_dir)
                print(f"报告已生成: {allure_report_dir / 'index.html'}")
            else:
                print(f"未找到测试结果目录: {allure_results_dir}，跳过报告生成。")
        except Exception as exc:
            print(f"生成 Allure 报告失败: {exc}")
            if sys.platform == "win32" and getattr(exc, "winerror", None) == 2:
                print(
                    "提示: 若已安装 Allure 仍报错，请确认已安装 JDK/JRE 并在 PATH 中可用；"
                    "npm 安装的 allure-commandline 依赖 java。"
                )

    print(f"环境: {env_name}")
    print(f"本次运行产物目录: {run_dir}")
    print(f"日志文件: {log_file}")
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
