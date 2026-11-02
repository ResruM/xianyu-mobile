#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动补发网盘链接

用法：
  python3 resend.py                    列出最近联系过的会话
  python3 resend.py <会话ID>           给指定会话补发货物
  python3 resend.py <会话ID> <商品ID>  指定商品补发

适合自动发货失败，或者买家说没收到时手动补发。
"""
import os
import sys
import json
import sqlite3
import asyncio
import websockets

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

from dotenv import load_dotenv
load_dotenv('.env')

from delivery import load_delivery, build_message, already_sent, mark_sent


def recent_chats(limit=10):
    db = 'data/chat_history.db'
    if not os.path.exists(db):
        return []
    conn = sqlite3.connect(db)
    rows = conn.execute(
        "select chat_id, item_id, max(timestamp) as t from messages "
        "where chat_id is not null group by chat_id order by t desc limit ?",
        (limit,)
    ).fetchall()
    conn.close()
    return rows


def find_buyer_id(chat_id):
    """从历史记录里找买家ID"""
    db = 'data/chat_history.db'
    if not os.path.exists(db):
        return None
    conn = sqlite3.connect(db)
    row = conn.execute(
        "select user_id from messages where chat_id=? and role='user' "
        "order by id desc limit 1", (str(chat_id),)
    ).fetchone()
    conn.close()
    return row[0] if row else None


async def send_one(chat_id, item_id):
    cfg = load_delivery()
    info = cfg.get(str(item_id))
    if not info:
        print(f"✗ 商品 {item_id} 没有配置发货信息")
        print("  检查 delivery.csv")
        return False

    text = build_message(info)
    if not text:
        print(f"✗ 商品 {item_id} 的网盘链接为空")
        return False

    buyer_id = find_buyer_id(chat_id)
    if not buyer_id:
        print(f"✗ 找不到会话 {chat_id} 的买家ID")
        return False

    # 延迟导入，避免循环依赖
    from main import XianyuLive

    print(f"正在连接闲鱼...")
    cookies = os.getenv("COOKIES_STR", "")
    xl = XianyuLive(cookies)

    headers = {
        "Cookie": cookies,
        "Host": "wss-goofish.dingtalk.com",
        "Connection": "Upgrade",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Origin": "https://www.goofish.com",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    async with websockets.connect(xl.base_url, extra_headers=headers) as ws:
        await xl.init(ws)
        await asyncio.sleep(1)
        await xl.send_msg(ws, str(chat_id), str(buyer_id), text)
        print(f"✅ 已发送到会话 {chat_id}")
        print("-" * 40)
        print(text)
        print("-" * 40)

    order_key = f"{item_id}:{chat_id}"
    mark_sent(order_key)
    return True


def main():
    args = sys.argv[1:]

    if not args:
        print("最近联系过的会话：\n")
        rows = recent_chats()
        if not rows:
            print("  没有记录。程序至少收到过一次消息才会有数据。")
            return
        cfg = load_delivery()
        for chat_id, item_id, ts in rows:
            name = cfg.get(str(item_id), {}).get('name', '(未配置发货)')
            print(f"  会话 {chat_id}")
            print(f"      商品 {item_id}  {name}")
            print(f"      时间 {ts}")
            print()
        print("补发命令：python3 resend.py <会话ID>")
        return

    chat_id = args[0]
    item_id = args[1] if len(args) > 1 else None

    if not item_id:
        rows = [r for r in recent_chats(50) if str(r[0]) == str(chat_id)]
        if not rows:
            print(f"✗ 找不到会话 {chat_id}")
            return
        item_id = rows[0][1]
        print(f"使用该会话最近联系的商品: {item_id}")

    asyncio.run(send_one(chat_id, item_id))


if __name__ == "__main__":
    main()
