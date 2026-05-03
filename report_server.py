"""
自动化测试报告服务
================
独立进程常驻运行，动态列出每次 `python main.py` 生成的 Allure 报告。

用法:
    python report_server.py            # 默认端口 8100
    python report_server.py --port 9000

访问:
    http://localhost:8100              # 报告列表
    http://localhost:8100/latest       # 最新报告（自动跳转）

无需安装额外依赖，仅使用 Python 标准库。
"""

import argparse
import html
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote

# report/ 目录与本文件同级
PROJECT_ROOT = Path(__file__).resolve().parent
REPORT_BASE = PROJECT_ROOT / "report"

# 每次运行产物中 allure 报告的相对路径（与 settings.py 的 allure_report_root 一致）
ALLURE_REPORT_SUBDIR = "allure-report"


# ---------------------------------------------------------------------------
# 报告目录扫描
# ---------------------------------------------------------------------------

def _scan_runs() -> list[dict]:
    """扫描 report/ 下所有包含 allure-report/index.html 的运行目录，按时间倒序。"""
    if not REPORT_BASE.is_dir():
        return []

    runs = []
    for entry in sorted(REPORT_BASE.iterdir(), reverse=True):
        if not entry.is_dir():
            continue
        index = entry / ALLURE_REPORT_SUBDIR / "index.html"
        if not index.exists():
            continue
        # 从目录名解析时间（reportYYYYMMDDHHmm 或 reportYYYYMMDDHHmm_n）
        name = entry.name
        display_time = _parse_display_time(name)
        runs.append({
            "name": name,
            "path": entry,
            "index": index,
            "display_time": display_time,
        })
    return runs


def _parse_display_time(dirname: str) -> str:
    """将 reportYYYYMMDDHHmm[_n] 转为可读时间字符串。"""
    # 去掉前缀 "report"，取前 12 位数字
    raw = dirname.removeprefix("report")
    digits = "".join(c for c in raw if c.isdigit())[:12]
    if len(digits) == 12:
        try:
            dt = datetime.strptime(digits, "%Y%m%d%H%M")
            return dt.strftime("%Y-%m-%d  %H:%M")
        except ValueError:
            pass
    return dirname


# ---------------------------------------------------------------------------
# HTTP 处理器
# ---------------------------------------------------------------------------

class ReportHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):  # 静默访问日志，只保留错误
        if args and str(args[1]) not in ("200", "304"):
            super().log_message(fmt, *args)

    def do_GET(self):
        path = unquote(self.path).rstrip("/") or "/"

        if path == "/" or path == "/index.html":
            self._serve_list()
        elif path == "/latest":
            self._serve_redirect_latest()
        elif path.startswith("/report/"):
            self._serve_static(path)
        else:
            self._send_404()

    # ------------------------------------------------------------------ #

    def _serve_list(self):
        runs = _scan_runs()
        latest_badge = ""
        rows = ""

        for i, run in enumerate(runs):
            badge = " <span style='background:#52c41a;color:#fff;border-radius:3px;padding:1px 7px;font-size:12px;margin-left:8px;'>最新</span>" if i == 0 else ""
            rows += f"""
            <tr>
              <td style="padding:10px 16px;font-family:monospace;font-size:14px;">
                {html.escape(run['display_time'])}{badge}
              </td>
              <td style="padding:10px 16px;">
                <a href="/report/{html.escape(run['name'])}/allure-report/index.html"
                   target="_blank"
                   style="color:#1890ff;text-decoration:none;font-weight:500;">
                  {html.escape(run['name'])}
                </a>
              </td>
            </tr>"""

        if not rows:
            rows = """<tr><td colspan="2" style="padding:32px;text-align:center;color:#999;">
                暂无报告，请先执行 python main.py
                </td></tr>"""

        count = len(runs)
        body = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>自动化测试报告</title>
  <meta http-equiv="refresh" content="30">
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5; }}
    .header {{ background: #001529; color: #fff; padding: 20px 32px; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 600; }}
    .header p  {{ margin: 4px 0 0; font-size: 13px; color: #aaa; }}
    .card {{ background: #fff; margin: 24px 32px; border-radius: 6px;
             box-shadow: 0 1px 4px rgba(0,0,0,.1); overflow: hidden; }}
    .card-title {{ padding: 14px 16px; font-size: 15px; font-weight: 600;
                   border-bottom: 1px solid #f0f0f0; background: #fafafa; }}
    table {{ width: 100%; border-collapse: collapse; }}
    tr:hover td {{ background: #e6f7ff; }}
    .latest-btn {{ display:inline-block; margin: 16px 32px 24px;
                   padding: 8px 22px; background: #1890ff; color: #fff;
                   border-radius: 4px; text-decoration: none; font-size: 14px; }}
    .latest-btn:hover {{ background: #096dd9; }}
    .refresh-note {{ color: #999; font-size: 12px; margin: 0 32px 24px; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>自动化测试报告</h1>
    <p>Sauce demo Shopping System · 共 {count} 次运行记录</p>
  </div>
  {'<a class="latest-btn" href="/latest" target="_blank">📊 查看最新报告</a>' if runs else ''}
  <div class="card">
    <div class="card-title">运行历史</div>
    <table>
      <thead>
        <tr style="background:#fafafa;font-size:13px;color:#888;">
          <th style="padding:8px 16px;text-align:left;font-weight:normal;">运行时间</th>
          <th style="padding:8px 16px;text-align:left;font-weight:normal;">报告目录</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <p class="refresh-note">页面每 30 秒自动刷新</p>
</body>
</html>"""

        self._send_html(body)

    def _serve_redirect_latest(self):
        runs = _scan_runs()
        if not runs:
            self._send_html("<h3>暂无报告，请先执行 python main.py</h3>", status=404)
            return
        latest = runs[0]
        target = f"/report/{latest['name']}/allure-report/index.html"
        self.send_response(302)
        self.send_header("Location", target)
        self.end_headers()

    def _serve_static(self, url_path: str):
        """将 /report/<run_name>/... 映射到磁盘文件。"""
        # url_path 形如 /report/report202604161030/allure-report/index.html
        rel = url_path.removeprefix("/report/")          # report202604161030/allure-report/...
        disk_path = REPORT_BASE / rel

        if not disk_path.exists():
            self._send_404()
            return

        if disk_path.is_dir():
            index = disk_path / "index.html"
            if index.exists():
                disk_path = index
            else:
                self._send_404()
                return

        mime = _guess_mime(disk_path.suffix)
        try:
            data = disk_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(data)
        except OSError:
            self._send_404()

    # ------------------------------------------------------------------ #

    def _send_html(self, body: str, status: int = 200):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_404(self):
        self._send_html("<h3>404 Not Found</h3>", status=404)


# ---------------------------------------------------------------------------
# MIME 类型
# ---------------------------------------------------------------------------

_MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".htm":  "text/html; charset=utf-8",
    ".css":  "text/css",
    ".js":   "application/javascript",
    ".json": "application/json",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon",
    ".woff": "font/woff",
    ".woff2":"font/woff2",
    ".ttf":  "font/ttf",
    ".map":  "application/json",
    ".xml":  "application/xml",
    ".txt":  "text/plain; charset=utf-8",
}

def _guess_mime(suffix: str) -> str:
    return _MIME_MAP.get(suffix.lower(), "application/octet-stream")


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="自动化测试报告服务")
    parser.add_argument("--port", type=int, default=8100, help="监听端口，默认 8100")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址，默认 0.0.0.0（所有网卡）")
    args = parser.parse_args()

    print(f"自动化测试报告服务启动")
    print(f"  报告目录: {REPORT_BASE}")
    print(f"  访问地址: http://localhost:{args.port}")
    print(f"  远程访问: http://<本机IP>:{args.port}")
    print(f"  Ctrl+C 停止")

    server = HTTPServer((args.host, args.port), ReportHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")


if __name__ == "__main__":
    main()