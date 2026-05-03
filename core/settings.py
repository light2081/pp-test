import configparser
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_ENV = "DEV"
SUPPORTED_ENVS = ("DEV", "TEST")

TEST_RUN_ARTIFACTS_DIR_ENV = "TEST_RUN_ARTIFACTS_DIR"


def _run_artifacts_cache_key() -> str:
    raw = os.getenv(TEST_RUN_ARTIFACTS_DIR_ENV, "").strip()
    if not raw:
        return ""
    path = Path(raw).expanduser()
    try:
        return str(path.resolve(strict=False))
    except OSError:
        return str(path)


@dataclass(frozen=True)
class SystemConfig:
    url: str
    username: str
    password: str
    expected_username: str


@dataclass(frozen=True)
class RuntimeConfig:
    browser: str
    headless: bool
    timeout_ms: int
    upload_file: Path


@dataclass(frozen=True)
class PathConfig:
    project_root: Path
    config_dir: Path
    runtime_root: Path
    shared_testdata_dir: Path
    env_testdata_dir: Path
    logs_dir: Path
    screenshots_dir: Path
    allure_results_dir: Path
    allure_report_dir: Path


@dataclass(frozen=True)
class AppConfig:
    env: str
    runtime: RuntimeConfig
    paths: PathConfig
    systems: dict = field(default_factory=dict)  # {"fo": SystemConfig, "bo": SystemConfig, ...}

    # 向后兼容属性：允许现有代码继续使用 settings.fo / settings.bo
    @property
    def fo(self) -> SystemConfig:
        return self.systems["fo"]

    @property
    def bo(self) -> SystemConfig:
        return self.systems["bo"]

    def get_system(self, name: str) -> SystemConfig:
        """按名称获取系统配置，新项目推荐使用此方法。"""
        if name not in self.systems:
            raise KeyError(f"未找到系统配置 [{name}]，已配置的系统: {list(self.systems.keys())}")
        return self.systems[name]


def resolve_env_name(env_name: str | None = None) -> str:
    value = (env_name or os.getenv("TEST_ENV") or DEFAULT_ENV).strip().upper()
    if value not in SUPPORTED_ENVS:
        raise ValueError(
            f"不支持的环境: {value}，当前仅支持: {', '.join(SUPPORTED_ENVS)}"
        )
    return value


def set_current_env(env_name: str | None = None) -> str:
    resolved = resolve_env_name(env_name)
    os.environ["TEST_ENV"] = resolved
    return resolved


def _resolve_project_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (PROJECT_ROOT / candidate).resolve()


def _get_required(parser: configparser.ConfigParser, section: str, option: str) -> str:
    value = parser.get(section, option, fallback="").strip()
    if not value:
        raise ValueError(f"配置缺失: [{section}] {option}")
    return value


def _get_bool(parser: configparser.ConfigParser, section: str, option: str, fallback: bool) -> bool:
    if parser.has_option(section, option):
        return parser.getboolean(section, option)
    return fallback


def _get_int(parser: configparser.ConfigParser, section: str, option: str, fallback: int) -> int:
    if parser.has_option(section, option):
        return parser.getint(section, option)
    return fallback


def _read_parser(env_name: str) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    env_file = CONFIG_DIR / f"{env_name.lower()}.ini"
    if not env_file.exists():
        raise FileNotFoundError(f"未找到环境配置文件: {env_file}")
    parser.read([CONFIG_DIR / "base.ini", env_file], encoding="utf-8")
    return parser


def _parse_systems(parser: configparser.ConfigParser) -> dict:
    """
    读取所有 [system.<name>] section，构建 systems 字典。
    同时兼容旧式 [fo] / [bo] section（直接命名无 system. 前缀）。
    """
    systems = {}

    # 新式：[system.fo]、[system.bo]、[system.admin] 等
    for section in parser.sections():
        if section.startswith("system."):
            name = section[len("system."):]
            systems[name] = SystemConfig(
                url=_get_required(parser, section, "url"),
                username=_get_required(parser, section, "username"),
                password=_get_required(parser, section, "password"),
                expected_username=_get_required(parser, section, "expected_username"),
            )

    # 旧式兼容：[fo] / [bo] 直接命名（CRMS 现有配置）
    for name in ("fo", "bo"):
        if name not in systems and parser.has_section(name):
            systems[name] = SystemConfig(
                url=_get_required(parser, name, "url"),
                username=_get_required(parser, name, "username"),
                password=_get_required(parser, name, "password"),
                expected_username=_get_required(parser, name, "expected_username"),
            )

    return systems


@lru_cache(maxsize=None)
def _load_settings_cached(env_name: str, run_artifacts_key: str) -> AppConfig:
    parser = _read_parser(env_name)

    testdata_root = parser.get("paths", "testdata_root", fallback="testdata").strip()
    runtime_root = parser.get("paths", "runtime_root", fallback="runtime").strip()
    logs_root = parser.get("paths", "logs_root", fallback="logs").strip()
    screenshots_root = parser.get("paths", "screenshots_root", fallback="screenshots").strip()
    allure_results_root = parser.get("paths", "allure_results_root", fallback="allure-results").strip()
    allure_report_root = parser.get("paths", "allure_report_root", fallback="allure-report").strip()

    shared_testdata_dir = _resolve_project_path(testdata_root)
    runtime_root_dir = _resolve_project_path(runtime_root)
    env_suffix = env_name.lower()
    if run_artifacts_key:
        run_root = Path(run_artifacts_key)
        paths = PathConfig(
            project_root=PROJECT_ROOT,
            config_dir=CONFIG_DIR,
            runtime_root=run_root,
            shared_testdata_dir=shared_testdata_dir,
            env_testdata_dir=shared_testdata_dir / env_suffix,
            logs_dir=run_root / logs_root,
            screenshots_dir=run_root / screenshots_root,
            allure_results_dir=run_root / allure_results_root,
            allure_report_dir=run_root / allure_report_root,
        )
    else:
        paths = PathConfig(
            project_root=PROJECT_ROOT,
            config_dir=CONFIG_DIR,
            runtime_root=runtime_root_dir,
            shared_testdata_dir=shared_testdata_dir,
            env_testdata_dir=shared_testdata_dir / env_suffix,
            logs_dir=runtime_root_dir / logs_root / env_suffix,
            screenshots_dir=runtime_root_dir / screenshots_root / env_suffix,
            allure_results_dir=runtime_root_dir / allure_results_root / env_suffix,
            allure_report_dir=runtime_root_dir / allure_report_root / env_suffix,
        )

    runtime = RuntimeConfig(
        browser=parser.get("runtime", "browser", fallback="chromium").strip(),
        headless=_get_bool(parser, "runtime", "headless", False),
        timeout_ms=_get_int(parser, "runtime", "timeout_ms", 30000),
        upload_file=_resolve_project_path(
            parser.get("runtime", "upload_file", fallback="testdata/id_back.jpg").strip()
        ),
    )

    systems = _parse_systems(parser)

    return AppConfig(
        env=env_name,
        runtime=runtime,
        paths=paths,
        systems=systems,
    )


def load_settings(env_name: str | None = None) -> AppConfig:
    return _load_settings_cached(resolve_env_name(env_name), _run_artifacts_cache_key())


def ensure_runtime_dirs(settings: AppConfig | None = None) -> AppConfig:
    settings = settings or load_settings()
    settings.paths.shared_testdata_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.env_testdata_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.screenshots_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.allure_results_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.allure_report_dir.mkdir(parents=True, exist_ok=True)
    return settings
