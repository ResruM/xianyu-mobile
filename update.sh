#!/bin/sh
# 闲鱼 AI 自动回复 - 更新脚本
# 用法: sh update.sh
# 作用: 只更新程序文件（提示词、知识库、代码），保留你的 .env 和 logs

cd "$(dirname "$0")" || exit 1

echo "========================================"
echo "  更新程序（保留配置和日志）"
echo "========================================"
echo

# 检查环境
if ! command -v wget >/dev/null 2>&1; then
    echo "✗ 缺少 wget，先执行: pkg install wget  或  apk add wget"
    exit 1
fi
if ! command -v unzip >/dev/null 2>&1; then
    echo "✗ 缺少 unzip，先执行: pkg install unzip  或  apk add unzip"
    exit 1
fi

# 备份配置
if [ -f .env ]; then
    cp .env .env.bak
    echo "✓ 已备份配置到 .env.bak"
fi
if [ -f items.csv ]; then
    cp items.csv items.csv.bak
    echo "✓ 已备份知识库到 items.csv.bak"
fi

echo
echo "正在下载最新版本..."

TMPDIR=$(mktemp -d)
cd "$TMPDIR" || exit 1

URL="https://github.com/ResruM/xianyu-mobile/archive/refs/heads/main.zip"
if ! wget -q -O main.zip "$URL"; then
    echo "✗ 下载失败，请检查网络"
    echo "  国内网络慢可以多试几次，或换个网络环境"
    cd - >/dev/null && rm -rf "$TMPDIR"
    exit 1
fi

if ! unzip -q main.zip; then
    echo "✗ 解压失败"
    cd - >/dev/null && rm -rf "$TMPDIR"
    exit 1
fi

SRC="$TMPDIR/xianyu-mobile-main"
if [ ! -d "$SRC" ]; then
    echo "✗ 压缩包结构异常"
    cd - >/dev/null && rm -rf "$TMPDIR"
    exit 1
fi

echo "✓ 下载完成"

# 回到原目录
cd - >/dev/null || exit 1

echo
echo "正在更新文件..."

# 更新程序文件，但不动 .env / logs / data / items.csv
for f in main.py XianyuAgent.py XianyuApis.py context_manager.py \
         llm_client.py knowledge.py run.py setup.py status.py stop.py \
         install.sh requirements.txt config.example.txt README.md; do
    if [ -f "$SRC/$f" ]; then
        cp "$SRC/$f" "$f"
        echo "  ✓ $f"
    fi
done

# 更新 prompts 目录
if [ -d "$SRC/prompts" ]; then
    mkdir -p prompts
    cp "$SRC"/prompts/*.txt prompts/ 2>/dev/null
    echo "  ✓ prompts/"
fi

# 更新 utils 目录
if [ -d "$SRC/utils" ]; then
    mkdir -p utils
    cp "$SRC"/utils/*.py utils/ 2>/dev/null
    echo "  ✓ utils/"
fi

# 恢复配置和知识库
if [ -f .env.bak ]; then
    mv .env.bak .env
    echo "  ✓ 已恢复你的配置 .env"
fi
if [ -f items.csv.bak ]; then
    cp items.csv.bak items.csv
    rm -f items.csv.bak
    echo "  ✓ 已保留你的知识库 items.csv"
elif [ -f "$SRC/items.csv" ] && [ ! -f items.csv ]; then
    cp "$SRC/items.csv" items.csv
    echo "  ✓ 已安装示例知识库 items.csv"
fi

rm -rf "$TMPDIR"

echo
echo "========================================"
echo "  更新完成！"
echo "========================================"
echo
echo "请重启程序使其生效："
echo "  python3 stop.py"
echo "  python3 run.py"
echo
