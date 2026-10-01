# 提交 PR 前请确认

## 必须本地跑通

```bash
pip install -e ".[dev]"
ruff check .                          # 门禁：语法错误与未定义名
python -m pytest tests/ -v            # 全部用例通过，且**没有** skip
```

`make check` 可一次跑完以上三步。

若你的改动需要 JAR 或 java，请确认 `python -m pytest tests/ -v` 仍然
100% 通过且没有 skip 出现——CI 开启了 strict 模式，出现任何 skip 都会让
整次运行判失败，这是有意为之：静默跳过等于什么都没验。

## 硬性约束

- [ ] 不修改 `params.to_cli_args` 的单一事实来源设计。它是 exporter 与
      generator 的共享映射，改动会同时影响界面与导出的命令行等价性。
- [ ] 渲染与样式逻辑**不得**下沉回本前端。Studio 是薄前端，渲染能力一律
      复用 `figtreekit` 核心；新增样式能力应先在核心库实现。
- [ ] 导出记录里的命令行必须能被 shell 逐字复现出与界面一致的像素。
      `tests/test_exporter.py::TestReplayEquivalence` 会断言这一点。
- [ ] 涉及网络监听、命令拼接、文件路径、请求体大小的改动，必须在
      `tests/test_hardening.py` 补对应回归测试。
- [ ] Python 文件沿用 `from __future__ import annotations`；
      JS 保持 vanilla，无构建步骤。

## 提交信息

沿用仓库既有的 Conventional Commits 风格，例如：

```
fix(renderer): 超时后正确终止子进程
feat(params): 新增 arc 布局透传
ci: 补 3.11 测试矩阵
```

## 版本号

版本号目前**分散硬编码在 7 个文件**（`pyproject.toml`、`__init__.py`、
`CITATION.cff`、`CHANGELOG.md`、`README.md`、`README_EN.md`、
`FigTreeKit Studio.spec`）。如果你只是修 bug 或加功能，**不需要**改版本号；
发布时由维护者统一处理。

## 许可证

贡献即表示同意你的代码以 GPL-2.0-or-later 授权。若改动引入或修改了
第三方组件，请同步更新 `NOTICE`。
