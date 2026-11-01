#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闲鱼 AI 自动回复 - 停止运行"""
import os
import sys
import time
import signal

BASE = os.path.dirname(os.path.abspath(__file__))
LOCK = os.path.join(BASE, ".running.pid")


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def main():
    if not os.path.exists(LOCK):
        print("程序未在运行")
        return
    try:
        pid = int(open(LOCK).read().strip())
    except Exception:
        os.remove(LOCK)
        print("锁文件异常，已清理")
        return

    if not alive(pid):
        os.remove(LOCK)
        print("程序未在运行（已清理残留锁）")
        return

    print(f"正在停止 PID {pid} ...")
    try:
        os.kill(pid, signal.SIGTERM)
        for _ in range(10):
            time.sleep(0.5)
            if not alive(pid):
                break
        else:
            os.kill(pid, signal.SIGKILL)
            print("强制结束")
    except OSError as e:
        print(f"停止失败: {e}")

    try:
        os.remove(LOCK)
    except OSError:
        pass
    print("已停止")


if __name__ == "__main__":
    main()
