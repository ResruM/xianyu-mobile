#!/bin/sh
# 闲鱼 AI 自动回复 - 一键安装 (iOS iSH / Linux / macOS)
cd "$(dirname "$0")" || exit 1

echo "========================================"
echo "  闲鱼 AI 自动回复 - 安装"
echo "========================================"
echo

# ---------- 先检查文件是否完整（解压不全是最常见的坑） ----------
MISSING=""
for F in main.py XianyuAgent.py XianyuApis.py context_manager.py llm_client.py \
         run.py setup.py requirements.txt utils/__init__.py utils/xianyu_utils.py \
         prompts/default_prompt.txt prompts/price_prompt.txt \
         prompts/tech_prompt.txt prompts/classify_prompt.txt; do
    [ -e "$F" ] || MISSING="$MISSING $F"
done

if [ -n "$MISSING" ]; then
    echo "✗ 文件不完整，缺少以下内容："
    for F in $MISSING; do
        echo "    - $F"
    done
    echo
    echo "  这说明压缩包没有完整解压。请按下面步骤重新来一遍："
    echo
    echo "    cd ~"
    echo "    rm -rf xianyu-mobile"
    echo "    wget -O xianyu-mobile.zip \"https://github.com/ResruM/xianyu-mobile/releases/download/v3.4/xianyu-mobile.zip\""
    echo "    unzip xianyu-mobile.zip"
    echo "    cd xianyu-mobile"
    echo "    sh install.sh"
    echo
    echo "  提示：解压时如果看到 'replacing' 之类的提示，"
    echo "        说明目录里有旧文件，先 rm -rf 删掉再解压更稳妥。"
    exit 1
fi

echo "✓ 文件完整性检查通过"
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "✗ 没找到 python3"
    echo "  iSH 用户请先执行: apk add python3 py3-pip"
    exit 1
fi
PYVER=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)
echo "✓ Python: $(python3 -V 2>&1)  ($PYVER)"

if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "✗ 没找到 pip"
    echo "  iSH 用户请先执行: apk add py3-pip"
    exit 1
fi

# ---------- 自动探测 pip 支持哪些参数 ----------
BREAK=""
if python3 -m pip install --help 2>/dev/null | grep -q -- '--break-system-packages'; then
    BREAK="--break-system-packages"
fi

# 是否允许 --user（虚拟环境里被禁用）
USEROPT="--user"
if python3 -m pip install --user --help >/dev/null 2>&1; then
    USEROPT="--user"
elif [ -n "$VIRTUAL_ENV" ]; then
    USEROPT=""
fi

echo "  pip 参数: ${BREAK:-（旧版pip，不使用）} ${USEROPT:-（不需 --user）}"

# ---------- 先试能否直接 import ----------
if python3 -c "import websockets, loguru, dotenv, requests" 2>/dev/null; then
    echo
    echo "✓ 依赖已就绪，无需安装"
    mkdir -p logs data
    echo
    echo "========================================"
    echo "  安装完成！"
    echo "========================================"
    echo
    echo "  下一步：python3 setup.py   然后  python3 run.py"
    echo
    exit 0
fi

# ---------- 依次尝试多个源 ----------
set -- https://pypi.tuna.tsinghua.edu.cn/simple \
       https://mirrors.aliyun.com/pypi/simple \
       https://pypi.org/simple

DONE=0
for M in "$@"; do
    echo
    echo "正在安装依赖（源: $M）..."

    # 第1轮：标准参数
    if python3 -m pip install -q --timeout 120 --retries 2 \
         $BREAK -i "$M" -r requirements.txt 2>/dev/null; then
        DONE=1
        break
    fi

    # 第2轮：加 --user（普通用户权限不足时）
    if [ -n "$USEROPT" ]; then
        if python3 -m pip install -q --timeout 120 --retries 2 \
             $BREAK $USEROPT -i "$M" -r requirements.txt 2>/dev/null; then
            DONE=1
            break
        fi
    fi

    # 第3轮：逐个包单独装（requirements 解析失败时的兜底）
    OK=1
    for P in "websockets==13.1" "loguru==0.7.3" "python-dotenv==1.0.1" "requests==2.32.3"; do
        if ! python3 -m pip install -q --timeout 120 --retries 2 \
              $BREAK $USEROPT -i "$M" "$P" 2>/dev/null; then
            OK=0
            break
        fi
    done
    if [ "$OK" = "1" ]; then
        DONE=1
        break
    fi

    echo "  这个源失败了，换下一个..."
done

# ---------- 最终校验 ----------
if python3 -c "import websockets, loguru, dotenv, requests" 2>/dev/null; then
    echo
    echo "✓ 依赖安装完成"
    echo "✓ 依赖校验通过"
    DONE=1
else
    DONE=0
fi

if [ "$DONE" = "0" ]; then
    echo
    echo "✗ 依赖安装失败"
    echo
    echo "  请手动执行下面这条（内容可以整段复制）："
    echo
    echo "  python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple websockets==13.1 loguru==0.7.3 python-dotenv==1.0.1 requests==2.32.3"
    echo
    echo "  如果是权限问题，加上 --user："
    echo "  python3 -m pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple websockets==13.1 loguru==0.7.3 python-dotenv==1.0.1 requests==2.32.3"
    echo
    echo "  装完后再运行: sh install.sh   （会自动检查并跳过）"
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
