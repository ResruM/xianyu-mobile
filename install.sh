#!/bin/sh
# 闲鱼 AI 自动回复 - 一键安装 (iOS iSH / Linux / macOS)
cd "$(dirname "$0")" || exit 1

echo "========================================"
echo "  闲鱼 AI 自动回复 - 安装"
echo "========================================"
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "✗ 没找到 python3"
    echo "  iSH 用户请先执行: apk add python3 py3-pip"
    exit 1
fi
echo "✓ Python: $(python3 -V 2>&1)"

if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "✗ 没找到 pip"
    echo "  iSH 用户请先执行: apk add py3-pip"
    exit 1
fi

# 依次尝试多个源，哪个通用哪个
MIRRORS="https://pypi.tuna.tsinghua.edu.cn/simple
https://mirrors.aliyun.com/pypi/simple
https://pypi.org/simple"

DONE=0
for M in $MIRRORS; do
    echo
    echo "正在安装依赖（源: $M）..."
    if python3 -m pip install -q --timeout 120 --retries 3 \
         --break-system-packages -i "$M" -r requirements.txt 2>/dev/null; then
        DONE=1
        break
    fi
    echo "  这个源失败，换下一个..."
done

if [ "$DONE" = "0" ]; then
    echo
    echo "✗ 依赖安装失败，请检查网络后重试"
    echo "  也可以手动执行:"
    echo "  python3 -m pip install --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt"
    exit 1
fi

echo
echo "✓ 依赖安装完成"

# 验证关键模块
if python3 -c "import websockets, openai, loguru, dotenv" 2>/dev/null; then
    echo "✓ 依赖校验通过"
else
    echo "✗ 依赖校验失败，请重新运行本脚本"
    exit 1
fi

mkdir -p logs data

echo
echo "========================================"
echo "  安装完成！"
echo "========================================"
echo
echo "  接下来按顺序执行："
echo
echo "    python3 setup.py     配置账号（只需一次）"
echo "    python3 run.py       启动自动回复"
echo
echo "  其他命令："
echo "    python3 status.py    查看运行状态和对话"
echo "    python3 stop.py      停止运行"
echo
