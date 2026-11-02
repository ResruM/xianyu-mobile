#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼 AI 自动回复 - 启动器
运行: python3 run.py
特性: 单实例锁 / 崩溃自动重启 / 错误直接显示在屏幕上
"""
import os
import sys
import time
import subprocess
import signal

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

LOCK = os.path.join(BASE, ".running.pid")
LOG = os.path.join(BASE, "logs", "agent.log")

# 常见错误的友好解释（顺序很重要，更具体的放前面）
HINTS = [
    ("No module named 'utils'", "程序文件不完整（utils 目录丢了）。请重新解压安装包"),
    ("No module named 'llm_client'", "程序文件不完整。请重新解压安装包"),
    ("No module named 'prompts'", "程序文件不完整。请重新解压安装包"),
    ("ModuleNotFoundError: No module named 'websockets'", "缺少 websockets。执行: pip install websockets==13.1"),
    ("ModuleNotFoundError: No module named 'loguru'", "缺少 loguru。执行: pip install loguru"),
    ("ModuleNotFoundError: No module named 'dotenv'", "缺少 python-dotenv。执行: pip install python-dotenv"),
    ("ModuleNotFoundError: No module named 'requests'", "缺少 requests。执行: pip install requests"),
    ("ModuleNotFoundError: No module named 'openai'", "程序版本较旧。建议重新下载 v3.4 以上版本"),
    ("ModuleNotFoundError", "缺少依赖。请执行: sh install.sh"),
    ("KeyError: 'unb'", "Cookie 里缺少 unb 字段，说明 Cookie 没复制完整"),
    ("Token获取失败", "Cookie 失效了。请重新抓 Cookie，重新运行 setup.py"),
    ("FAIL_SYS_TOKEN_EMPTY", "Cookie 无效或已过期，需要重新抓"),
    ("Login失败", "Cookie 已失效，请重新抓一次"),
    ("401", "API Key 无效，请检查模型 Key"),
    ("402", "模型账户余额不足"),
    ("SSL", "网络或证书问题。iSH 里可试: apk add ca-certificates"),
    ("Connection", "网络连接问题，请检查网络"),
]


def alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def read_lock():
    try:
        with open(LOCK) as f:
            return int(f.read().strip())
    except Exception:
        return None


def show_last_error():
    """从日志里提取最后的报错，直接打到屏幕上"""
    if not os.path.exists(LOG):
        return
    try:
        with open(LOG, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # 找最后一个 Traceback 或 ERROR
        idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if "Traceback" in lines[i] or "ERROR" in lines[i]:
                idx = i
                break

        if idx < 0:
            tail = [l.rstrip() for l in lines[-6:] if l.strip()]
            if tail:
                print("\n--- 日志末尾 ---")
                for l in tail:
                    print("  " + l[:120])
            return

        err = [l.rstrip() for l in lines[idx: idx + 25] if l.strip()]

        print("\n" + "!" * 42)
        print("  出错了，具体信息如下：")
        print("!" * 42)
        for l in err:
            print("  " + l[:130])
        print()

        # 匹配常见原因
        joined = " ".join(err)
        for key, hint in HINTS:
            if key in joined or key in "".join(lines[-40:]):
                print(f"  👉 可能原因：{hint}")
                break
        else:
            print("  👉 看不出常见原因，把上面的报错截图发给卖家")

        print(f"\n  完整日志：{LOG}")
        print("!" * 42)

    except Exception:
        pass


def main():
    if not os.path.exists(os.path.join(BASE, ".env")):
        print("✗ 还没有配置文件")
        print("  请先运行:  python3 setup.py")
        sys.exit(1)

    old = read_lock()
    if old and alive(old):
        print(f"✗ 已有实例在运行 (PID {old})")
        print("  如需重启，先运行: python3 stop.py")
        sys.exit(1)

    with open(LOCK, "w") as f:
        f.write(str(os.getpid()))

    os.makedirs(os.path.join(BASE, "logs"), exist_ok=True)
    os.makedirs(os.path.join(BASE, "data"), exist_ok=True)

    print("=" * 42)
    print("  闲鱼 AI 自动回复 已启动")
    print("=" * 42)
    print(f"  日志: {LOG}")
    print("  停止: 按 Ctrl+C")
    print()

    stop = {"flag": False}

    def on_signal(signum, frame):
        stop["flag"] = True
        print("\n正在停止...")

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    restarts = 0
    while not stop["flag"]:
        with open(LOG, "a", encoding="utf-8") as lf:
            lf.write(f"\n[启动] {time.strftime('%F %T')} 第 {restarts + 1} 次启动\n")
            lf.flush()
            p = subprocess.Popen(
                [sys.executable, "-u", "main.py"],
                stdout=lf, stderr=subprocess.STDOUT,
            )
        while p.poll() is None:
            if stop["flag"]:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
                break
            time.sleep(1)

        if stop["flag"]:
            break

        restarts += 1
        print(f"\n⚠ 程序退出(code {p.returncode})")

        # 第 1 次崩溃就把错误原因打出来
        if restarts <= 2:
            show_last_error()

        # 连续崩 3 次以上就停下，别无限重启刷屏
        if restarts >= 5:
            print("\n程序已连续退出 5 次，停止重启。")
            print("请按上面的提示修复后重新运行 python3 run.py")
            break

        print("  （5 秒后自动重启，按 Ctrl+C 停止）")
        for _ in range(5):
            if stop["flag"]:
                break
            time.sleep(1)

    try:
        os.remove(LOCK)
    except OSError:
        pass
    print("已停止")


if __name__ == "__main__":
    main()
