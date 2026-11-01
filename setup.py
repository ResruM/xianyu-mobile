#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼 AI 自动回复 - 配置向导
运行: python3 setup.py
"""
import os
import sys
import json
import urllib.request
import urllib.error

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

BANNER = r"""
========================================
   闲鱼 AI 自动回复助手  v1.0
   配置向导（只需做一次）
========================================
"""

PROVIDERS = [
    ("1", "DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat", "便宜稳定，推荐"),
    ("2", "阿里百炼通义千问", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus", "国内直连快"),
    ("3", "月之暗面 Kimi", "https://api.moonshot.cn/v1", "moonshot-v1-8k", "长上下文"),
    ("4", "智谱 GLM", "https://open.bigmodel.cn/api/paas/v4", "glm-4-flash", "有免费额度"),
    ("5", "自定义", "", "", "自己填地址和模型名"),
]


def line(char="─", n=40):
    print(char * n)


def ask(prompt, default="", secret=False):
    """询问输入，secret 时尽量不回显"""
    tip = f" [{default}]" if default else ""
    try:
        if secret and sys.stdin.isatty():
            import getpass
            val = getpass.getpass(f"{prompt}{tip}: ")
        else:
            val = input(f"{prompt}{tip}: ")
    except (EOFError, KeyboardInterrupt):
        print("\n已取消")
        sys.exit(1)
    return val.strip() or default


def parse_cookies(cookie_str):
    """解析 cookie 字符串为 dict"""
    out = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def check_cookies(cookie_str):
    """返回 (是否有效, 提示信息)"""
    c = parse_cookies(cookie_str)
    if "unb" not in c:
        return False, "缺少 unb 字段（说明没登录成功，或复制的不完整）"
    if len(c) < 5:
        return False, f"只解析到 {len(c)} 个字段，可能没复制完整"
    return True, f"识别到 {len(c)} 个 cookie 字段，用户ID: {c['unb']}"


def check_llm(base_url, api_key, model):
    """实际请求一次，验证 key 是否可用"""
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5,
    }).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
        if "choices" in data:
            return True, "模型连接正常"
        return False, f"返回异常: {str(data)[:100]}"
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:150]
        if e.code == 401:
            return False, "API Key 无效或已过期"
        if e.code == 402 or "insufficient" in msg.lower():
            return False, "账户余额不足"
        if e.code == 404:
            return False, f"模型名可能不对: {model}"
        return False, f"HTTP {e.code}: {msg}"
    except Exception as e:
        return False, f"网络错误: {type(e).__name__} {str(e)[:80]}"


def write_env(cfg):
    content = f"""# 闲鱼 AI 自动回复 - 配置文件
API_KEY={cfg['api_key']}
MODEL_BASE_URL={cfg['base_url']}
MODEL_NAME={cfg['model']}
COOKIES_STR={cfg['cookies']}

# 人工接管切换词：在闲鱼里发这个字，AI 停止回复切换人工；再发一次恢复
TOGGLE_KEYWORDS={cfg['toggle']}

# 模拟真人打字延迟（True/False）
SIMULATE_HUMAN_TYPING={cfg['typing']}

# 日志级别 DEBUG/INFO/WARNING
LOG_LEVEL=INFO
"""
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    print(BANNER)

    # ---------- 第一步：选模型 ----------
    line()
    print("第一步：选择 AI 模型服务")
    line()
    for p in PROVIDERS:
        print(f"  {p[0]}. {p[1]:<16} {p[4]}")
    print()
    choice = ask("请输入序号", "1")

    prov = next((p for p in PROVIDERS if p[0] == choice), PROVIDERS[0])
    name, base_url, model = prov[1], prov[2], prov[3]
    if name == "自定义":
        base_url = ask("模型接口地址(以 /v1 结尾)")
        model = ask("模型名称")
    print(f"已选择: {name}\n")

    # ---------- 第二步：API Key ----------
    line()
    print("第二步：填写 API Key")
    print("（去对应平台注册后，在『API Keys』页面创建）")
    line()
    while True:
        api_key = ask("API Key", secret=True)
        if not api_key:
            print("  不能为空，请重新输入")
            continue
        print("  正在验证...")
        ok, msg = check_llm(base_url, api_key, model)
        print(f"  {'✓' if ok else '✗'} {msg}")
        if ok:
            break
        if ask("是否重新输入 Key？(y/n)", "y").lower() != "y":
            print("  已跳过验证，继续配置")
            break

    # ---------- 第三步：Cookie ----------
    print()
    line()
    print("第三步：填写闲鱼 Cookie")
    print("  1) 电脑浏览器打开 www.goofish.com 并登录")
    print("  2) 按 F12 → Network → Fetch/XHR → 刷新页面")
    print("  3) 点任意请求 → Headers → Request Headers")
    print("  4) 复制 Cookie: 后面全部内容（一大串）")
    print("  关键：必须包含 unb= 这一段")
    line()
    while True:
        cookies = ask("粘到这里")
        if not cookies:
            print("  不能为空")
            continue
        ok, msg = check_cookies(cookies)
        print(f"  {'✓' if ok else '✗'} {msg}")
        if ok:
            break
        if ask("是否重新粘贴？(y/n)", "y").lower() != "y":
            print("  ！Cookie 无效，程序将无法正常工作")
            break

    # ---------- 第四步：杂项 ----------
    print()
    line()
    print("第四步：其他设置（直接回车用默认）")
    line()
    toggle = ask("人工接管切换词", "。")
    typing = ask("模拟真人打字延迟？(y/n)", "y")
    typing = "True" if typing.lower().startswith("y") else "False"

    cfg = {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "cookies": cookies,
        "toggle": toggle,
        "typing": typing,
    }
    write_env(cfg)

    print()
    line("═")
    print("配置完成！")
    line("═")
    print(f"  模型      {name} / {model}")
    print(f"  配置文件  {ENV_PATH}")
    print()
    print("  下一步：运行  python3 run.py  启动")
    print("  停止：  Ctrl+C")
    print("  状态：  python3 status.py")
    print()


if __name__ == "__main__":
    main()
