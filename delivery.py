#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动发货
买家付款后，自动把网盘链接发到聊天里。

配置文件：delivery.csv（和本脚本同目录）
格式：
  商品ID,商品名,网盘链接,提取码

使用：
  1. 在 main.py 里已经接入（付款消息触发）
  2. 也可手动测试：python3 delivery.py --test 商品ID
"""
import os
import csv
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "delivery.csv")
SENT_LOG = os.path.join(BASE, "data", "delivered.txt")

FIELDS = ["商品ID", "商品名", "网盘链接", "提取码"]


def load_delivery():
    """读取发货配置，返回 {商品ID: {link, code, name}}"""
    if not os.path.exists(CSV_PATH):
        return {}
    result = {}
    try:
        with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                item_id = (row.get("商品ID") or "").strip()
                if not item_id or item_id.startswith("#"):
                    continue
                result[item_id] = {
                    "name": (row.get("商品名") or "").strip(),
                    "link": (row.get("网盘链接") or "").strip(),
                    "code": (row.get("提取码") or "").strip(),
                }
    except Exception as e:
        print(f"[发货] 读取失败: {e}", file=sys.stderr)
        return {}
    return result


def build_message(info):
    """生成发货话术"""
    name = info["name"] or "商品"
    link = info["link"]
    code = info["code"]

    if not link:
        return None

    lines = [f"【{name}】已收到付款，链接如下：", link]
    if code:
        lines.append(f"提取码：{code}")
    lines.append("有问题随时找我。")
    return "\n".join(lines)


def already_sent(order_key):
    """检查是否已经发过（避免重复发货）"""
    if not os.path.exists(SENT_LOG):
        return False
    try:
        with open(SENT_LOG, encoding="utf-8") as f:
            return order_key in f.read()
    except Exception:
        return False


def mark_sent(order_key):
    """记录已发货"""
    os.makedirs(os.path.dirname(SENT_LOG), exist_ok=True)
    with open(SENT_LOG, "a", encoding="utf-8") as f:
        f.write(order_key + "\n")


def create_template():
    if os.path.exists(CSV_PATH):
        print(f"已存在 {CSV_PATH}，未覆盖")
        return
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerow({
            "商品ID": "1089894534999",
            "商品名": "高性价比人生指南",
            "网盘链接": "https://pan.baidu.com/s/xxxx?pwd=abcd",
            "提取码": "abcd",
        })
    print(f"✓ 已生成模板: {CSV_PATH}")
    print("  填好商品ID、链接、提取码后重启程序生效")


def show():
    data = load_delivery()
    if not data:
        print("发货配置为空。先运行: python3 delivery.py --init")
        return
    print(f"共 {len(data)} 个商品配置了自动发货：\n")
    for item_id, info in data.items():
        print(f"  {item_id}  {info['name']}")
        print(f"      链接: {info['link'][:50]}...")
        print(f"      提取码: {info['code']}")
        print()


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""

    if arg in ("--init", "-i"):
        create_template()
    elif arg in ("--list", "-l"):
        show()
    elif arg == "--test" and len(sys.argv) > 2:
        item_id = sys.argv[2]
        data = load_delivery()
        info = data.get(item_id)
        if not info:
            print(f"商品 {item_id} 没有配置发货信息")
            sys.exit(1)
        msg = build_message(info)
        if not msg:
            print("链接为空，无法生成发货消息")
            sys.exit(1)
        print("生成的消息：")
        print("-" * 40)
        print(msg)
        print("-" * 40)
    else:
        print(__doc__)
        print("命令：")
        print("  python3 delivery.py --init          生成模板 delivery.csv")
        print("  python3 delivery.py --list          查看已配置的商品")
        print("  python3 delivery.py --test 商品ID   预览发货消息")
        if os.path.exists(CSV_PATH):
            print()
            show()
