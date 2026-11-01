#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼 AI 自动回复 - 启动器
运行: python3 run.py
特性: 单实例锁 / 崩溃自动重启 / Ctrl+C 优雅退出
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


def main():
    # 检查配置
    if not os.path.exists(os.path.join(BASE, ".env")):
        print("✗ 还没有配置文件")
        print("  请先运行:  python3 setup.py")
        sys.exit(1)

    # 单实例锁
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
        print(f"⚠ 程序退出(code {p.returncode})，5 秒后重启 #{restarts}")
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
