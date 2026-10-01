# FigTreeKit Studio — 常用开发任务
#
# 目的是把「必须本地跑通」的三件事固化成一条命令，避免文档与实际脱节。

PYTHON ?= python3

.DEFAULT_GOAL := help
.PHONY: help install test lint check build run clean

help:  ## 显示本帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install:  ## 以可编辑模式安装本项目与开发依赖
	$(PYTHON) -m pip install -e ".[dev]"

test:  ## 跑全部测试（本地模式，允许 skip）
	$(PYTHON) -m pytest tests/ -v

test-strict:  ## 以 CI 的 strict 模式跑测试：出现任何 skip 即失败
	FIGTREEKIT_STUDIO_STRICT_TESTS=1 $(PYTHON) -m pytest tests/ -v

lint:  ## 静态检查（语法错误 + 未定义名）
	$(PYTHON) -m ruff check --no-cache .

check: lint test  ## 提交前必跑：静态检查 + 全部测试
	@echo "✓ lint 与测试均通过"

coverage:  ## 跑测试并输出覆盖率（门槛数值见 pyproject.toml [tool.coverage.report]）
	$(PYTHON) -m pytest tests/ --cov --cov-report=term-missing

run:  ## 启动应用（原生窗口）
	$(PYTHON) -m figtreekit_studio

build:  ## 打包 macOS .app
	$(PYTHON) -m pip install "pyinstaller>=6.0"
	$(PYTHON) -m PyInstaller --noconfirm --distpath dist "FigTreeKit Studio.spec"

smoke: build  ## 打包后跑冻结包自检
	"./dist/FigTreeKit Studio.app/Contents/MacOS/FigTreeKit Studio" --smoke-test

clean:  ## 清理构建产物与缓存
	rm -rf build dist .pytest_cache .ruff_cache .coverage coverage.xml
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
