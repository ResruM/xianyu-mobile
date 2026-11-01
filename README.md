# 闲鱼 AI 自动回复助手

闲鱼卖家的自动回复工具，支持商品答疑、自动议价、人工接管。

## 快速开始

```sh
sh install.sh          # 安装依赖
python3 setup.py       # 配置（只需一次）
python3 run.py         # 启动
```

其他命令：

```sh
python3 status.py      # 查看状态和最近对话
python3 stop.py        # 停止
```

## 环境要求

- Python 3.8+
- 安卓：Termux
- iPhone：iSH
- 电脑：Windows / macOS / Linux

## 配置项

| 变量 | 说明 |
|---|---|
| `API_KEY` | 模型 API Key |
| `MODEL_BASE_URL` | 接口地址 |
| `MODEL_NAME` | 模型名称 |
| `COOKIES_STR` | 闲鱼 Cookie（需含 `unb`） |
| `TOGGLE_KEYWORDS` | 人工接管切换词，默认 `。` |
| `SIMULATE_HUMAN_TYPING` | 模拟真人打字延迟 |

## 自定义

`prompts/` 目录下 4 个文件可改 AI 的说话风格：

- `default_prompt.txt` 日常咨询
- `price_prompt.txt` 议价
- `tech_prompt.txt` 技术问题
- `classify_prompt.txt` 意图识别

## 注意

- 同一账号只能运行一个实例
- Cookie 会过期，需要定期更新
- 本工具仅供学习研究
