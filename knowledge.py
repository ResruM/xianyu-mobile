#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商品知识库
每个商品可以单独配置：最低价格、服务说明、常见问题、禁区。

用法：
  1. 运行  python3 knowledge.py  生成模板 items.csv
  2. 用 Excel / 文本编辑器填写
  3. 保存后程序会自动读取（重启生效）

文件：items.csv（和本脚本同目录）
"""
import os
import csv
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "items.csv")

FIELDS = [
    "商品ID",      # 闲鱼商品 id（从消息日志能看到）
    "商品名",      # 方便自己认
    "最低价",      # 议价底线，AI 不会低于这个
    "交付方式",    # 例如：拍下后发网盘链接
    "服务说明",    # 例如：含一次修改、48小时内交付
    "常见问答",    # 格式 问题|答案 ;; 问题|答案
    "禁说内容",    # 例如：不能说包过、不能说保证录用
    "备注",        # 给自己的备注，不影响 AI
]

SAMPLE = [
    {
        "商品ID": "1089894534999",
        "商品名": "SPSS数据分析代做",
        "最低价": "60",
        "交付方式": "拍下后发网盘链接，24小时内交付",
        "服务说明": "含一次免费修改；提供结果解读",
        "常见问答": "能做信效度吗|可以做，常见做法都有 ;; 要原始数据吗|需要您提供数据文件 ;; 多久出结果|一般24小时内",
        "禁说内容": "不能说保证过审、不能说百分百准确",
        "备注": "示例行，填你自己的后可以删",
    },
]

TEMPLATE_NOTE = """# 商品知识库说明
#
# 这个文件让 AI 回答更准确。填写方式：
# - 用 Excel 打开（UTF-8 编码），或用文本编辑器直接改
# - 商品ID 可以从 logs/agent.log 里找到，形如 商品: 1089894534999
# - 常见问答的格式：问题|答案 ;; 问题|答案
# - 留空的行不影响程序
# - 改完重启程序生效
#
# 不想用某一行，把商品ID 清空即可
"""


def load_knowledge():
    """读取知识库，返回 {商品ID: {...}} 字典"""
    if not os.path.exists(CSV_PATH):
        return {}
    result = {}
    try:
        with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item_id = (row.get("商品ID") or "").strip()
                if not item_id or item_id.startswith("#"):
                    continue
                qa = []
                raw_qa = (row.get("常见问答") or "").strip()
                for pair in raw_qa.split(";;"):
                    if "|" in pair:
                        q, a = pair.split("|", 1)
                        q, a = q.strip(), a.strip()
                        if q and a:
                            qa.append((q, a))
                result[item_id] = {
                    "name": (row.get("商品名") or "").strip(),
                    "min_price": (row.get("最低价") or "").strip(),
                    "delivery": (row.get("交付方式") or "").strip(),
                    "service": (row.get("服务说明") or "").strip(),
                    "qa": qa,
                    "forbidden": (row.get("禁说内容") or "").strip(),
                }
    except Exception as e:
        print(f"[知识库] 读取失败: {e}", file=sys.stderr)
        return {}
    return result


def format_for_prompt(info):
    """把知识库条目格式化成给 AI 的文字"""
    if not info:
        return ""
    parts = []
    if info["min_price"]:
        parts.append(f"最低可接受价格：{info['min_price']} 元（低于这个价格不能答应，要婉拒）")
    if info["delivery"]:
        parts.append(f"交付方式：{info['delivery']}")
    if info["service"]:
        parts.append(f"服务内容：{info['service']}")
    if info["qa"]:
        lines = [f"  {q} → {a}" for q, a in info["qa"]]
        parts.append("常见问题解答：\n" + "\n".join(lines))
    if info["forbidden"]:
        parts.append(f"绝对不能说：{info['forbidden']}")
    if not parts:
        return ""
    return "\n【本商品知识库】\n" + "\n".join(parts)


def create_template():
    if os.path.exists(CSV_PATH):
        print(f"已存在 {CSV_PATH}，未覆盖")
        print("如需重新生成，先删除该文件")
        return
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for row in SAMPLE:
            w.writerow(row)
    print(f"✓ 已生成模板: {CSV_PATH}")
    print("  用 Excel 或文本编辑器打开，按你的实际情况填写")
    print("  填完重启程序生效")


def list_items():
    data = load_knowledge()
    if not data:
        print("知识库为空。先运行: python3 knowledge.py --init")
        return
    print(f"共 {len(data)} 个商品：\n")
    for item_id, info in data.items():
        print(f"  {item_id}  {info['name'] or '(未命名)'}")
        if info["min_price"]:
            print(f"      最低价: {info['min_price']} 元")
        if info["qa"]:
            print(f"      问答: {len(info['qa'])} 条")
        if info["forbidden"]:
            print(f"      禁说: {info['forbidden']}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg in ("--init", "-i"):
        create_template()
    elif arg in ("--list", "-l"):
        list_items()
    else:
        print(__doc__)
        print("命令：")
        print("  python3 knowledge.py --init     生成模板")
        print("  python3 knowledge.py --list     查看已配置的商品")
        if os.path.exists(CSV_PATH):
            print()
            print("当前知识库：")
            list_items()
