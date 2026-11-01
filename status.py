#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闲鱼 AI 自动回复 - 查看状态与最近对话"""
import os
import sys
import sqlite3
import time

BASE = os.path.dirname(os.path.abspath(__file__))
LOCK = os.path.join(BASE, ".running.pid")
LOG = os.path.join(BASE, "logs", "agent.log")
DB = os.path.join(BASE, "data", "chat_history.db")


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def main():
    # 运行状态
    pid = None
    if os.path.exists(LOCK):
        try:
            pid = int(open(LOCK).read().strip())
        except Exception:
            pid = None
    running = pid is not None and alive(pid)

    print("=" * 42)
    print("  闲鱼 AI 自动回复 - 状态")
    print("=" * 42)
    print(f"  运行状态: {'● 在线 (PID %s)' % pid if running else '○ 未运行'}")

    # 配置摘要
    env = os.path.join(BASE, ".env")
    if os.path.exists(env):
        cfg = {}
        for line in open(env, encoding="utf-8"):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
        print(f"  模型:     {cfg.get('MODEL_NAME', '?')}")
        ck = cfg.get("COOKIES_STR", "")
        has_unb = "unb=" in ck
        print(f"  Cookie:   {'✓ 已配置' if has_unb else '✗ 未配置或无效'}")
        print(f"  接管词:   {cfg.get('TOGGLE_KEYWORDS', '。')}")
    else:
        print("  配置:     未初始化，请先运行 python3 setup.py")

    # 日志尾部
    if os.path.exists(LOG):
        print()
        print("最近日志:")
        lines = []
        with open(LOG, encoding="utf-8", errors="ignore") as f:
            for ln in f:
                if "心跳" in ln:
                    continue
                lines.append(ln.rstrip())
        for ln in lines[-8:]:
            print("  " + ln[:110])

    # 商品知识库
    kb_file = os.path.join(BASE, "items.csv")
    if os.path.exists(kb_file):
        try:
            sys.path.insert(0, BASE)
            from knowledge import load_knowledge
            kb = load_knowledge()
            if kb:
                print()
                print(f"商品知识库: {len(kb)} 个商品")
                for iid, info in list(kb.items())[:5]:
                    qa = f" / {len(info['qa'])}条问答" if info["qa"] else ""
                    mp = f" / 最低价{info['min_price']}元" if info["min_price"] else ""
                    print(f"  {iid} {info['name'] or ''}{mp}{qa}")
            else:
                print()
                print("商品知识库: 文件存在但没有有效内容")
        except Exception:
            pass
    else:
        print()
        print("商品知识库: 未配置（可选）")
        print("  想让它回答更准，运行: python3 knowledge.py --init")

    # 对话记录
    if os.path.exists(DB):
        try:
            conn = sqlite3.connect(DB)
            n = conn.execute("select count(*) from messages").fetchone()[0]
            print()
            print(f"累计消息: {n} 条")
            rows = conn.execute(
                "select role, content, timestamp from messages "
                "order by id desc limit 6"
            ).fetchall()
            if rows:
                print("最近对话:")
                for role, content, ts in reversed(rows):
                    who = "买家" if role == "user" else "AI "
                    print(f"  {ts[11:19]} {who}: {content[:40]}")
        except Exception:
            pass
    print()
    print("=" * 42)


if __name__ == "__main__":
    main()
