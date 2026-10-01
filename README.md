# FigTreeKit Studio

[![CI](https://github.com/ZengZichao/FigTreeKit-Studio/actions/workflows/ci.yml/badge.svg)](https://github.com/ZengZichao/FigTreeKit-Studio/actions/workflows/ci.yml)
[![License: GPL-2.0-or-later](https://img.shields.io/badge/License-GPL--2.0--or--later-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Stage: Alpha](https://img.shields.io/badge/stage-alpha-orange.svg)](#)

> 桌面应用 · 可视化调参 · 实时预览 · 可复现脚本导出

FigTreeKit Studio 是 [`figtreekit`](https://pypi.org/project/figtreekit/) 的可视化前端。
它提供图形界面调参、实时 PNG 预览、等效 CLI 命令与 JSON 配置导出，
让非编程的生物学家、审稿人也能快速样式化系统发育树，同时保持完全可复现性。

[🇬🇧 English](README_EN.md) · 🇨🇳 中文

**v0.1.2 — 当前发布版本**
- 🖥️ **独立桌面应用**：原生窗口运行（pywebview），不依赖浏览器
- 🌐 **中英文双语界面**：一键切换（右上角 `EN / 中文`），自动记忆，首次按系统语言选择
- 🌿 **SVG 矢量 Logo**：黑白灰配色的极简系统发育树（`static/logo.svg`），同步用作应用图标
- ♿ **无障碍设计**：WCAG AA 对比度、`aria-live` 状态播报、键盘焦点管理
- 🔒 **安全加固**：路径穿越防护、CSP 安全头、请求体大小上限

**设计原则**：薄前端（前端零业务逻辑）+ 核心零改动（直接复用 figtreekit）+
可复现性优先（GUI 所见 = 命令行所得）。

---

## 安装

FigTreeKit Studio **未发布到 PyPI**，请从本仓库安装（分发包名为
`figtreekit-studio`，会自动拉取核心库 `figtreekit`）：

```bash
git clone https://github.com/ZengZichao/FigTreeKit-Studio.git
cd FigTreeKit-Studio
pip install .
```

也可下载源码归档 <https://github.com/ZengZichao/FigTreeKit-Studio/archive/refs/tags/v0.1.2.tar.gz>。
本前端已在 Zenodo 存档：版本 DOI <https://doi.org/10.5281/zenodo.22977933>（v0.1.2），
concept DOI <https://doi.org/10.5281/zenodo.22766959>（跨版本）。核心库 `figtreekit` 另行存档。

**运行时依赖**：
- Python 3.11+
- Java 8 及以上（JRE/JDK，用于渲染；启动时读取并检查 `java -version` 报告的版本）
- `figtreekit[render]` 1.1.3+（自动安装；`[render]` 提供渲染后外观处理所需的 Pillow）
- `pywebview` 5.0+（自动安装，提供原生桌面窗口）

仅在 macOS 上验证（CI 亦运行于 macOS）。界面层规避原生控件，Windows/Linux 预期可用，但均未实测，因此不作跨平台支持声明。

> ⚠️ 本项目处于 Alpha 阶段，API 和界面可能随版本迭代调整。

---

## 启动

```bash
figtreekit-studio                    # 原生桌面窗口（默认，不依赖浏览器）
figtreekit-studio --browser          # 改用系统浏览器打开
figtreekit-studio --no-window        # 仅启动服务，不打开任何界面
figtreekit-studio --port 9000 --browser
python -m figtreekit_studio          # 等效入口
```

macOS 应用包（`FigTreeKit Studio.app`）双击即用，同样为原生窗口，无需浏览器、无需命令行。

---

## 语言切换

界面右上角 **`EN` / `中文`** 按钮可随时切换全部界面文案（表单标签、按钮、提示、错误信息）。
选择会写入 `localStorage` 并在下次启动时保持；首次启动按系统语言自动选择。

---

## 首次渲染

1. 在左侧表单粘贴 Newick/Nexus 树文本（或上传 `.tre/.nwk/.nex` 文件）。
2. 调整布局、外观、分类学、刻度轴等参数。
3. 点击「⚡ 生成预览 + 导出脚本」。
4. 右侧实时显示渲染预览图。
5. 右下角显示等效 CLI 命令与 JSON 配置，可一键复制。

> 首次使用时如果 Java 不可用或 JAR 缺失，界面会给出明确指引（跟随界面语言）。
> 可点击右上角「环境检测」按钮检查。

---

## 导出即复现

Studio 导出的 CLI 命令与 generator 实际执行的完全一致（共用 `params.to_cli_args` 单一来源）：

```bash
python -m figtreekit input.tre -o output.nex --force \
  --layout polar --tip-labels-hide --auto-color phylum \
  --scale-axis-show \
  --background-color #FAFAFA --branch-width 2.0 \
  && java -jar figtree_patched.jar -graphic PNG -width 1600 -height 1000 output.nex output.png
```

对应 JSON 配置（可直接 `figtreekit --config` 消费）：

```json
{
  "layout.layoutType": "POLAR",
  "tipLabels.isShown": false,
  "appearance.backgroundColour": "#FAFAFA",
  "appearance.branchLineWidth": 2.0,
  "scaleAxis.isShown": true
}
```

> **JSON 配置能力边界**：自动配色（`--auto-color`）与分类折叠（`--collapse-rank` / `--collapse-style`）
> 属于 figtreekit 的 clade 操作，在 CLI 中是独立开关，在配置 schema 中没有对应的简单键。
> 因此 **JSON 配置不包含这三项**，仅 CLI 命令可完整复现含配色/折叠的结果。
> 若需完整复现，请始终以导出的 CLI 命令为准。

---

## 功能

### 当前版本（v0.1.2）
- ✅ 桌面应用：原生窗口，不依赖浏览器（pywebview / WKWebView）
- ✅ 中英文双语界面，一键切换并记忆
- ✅ SVG 矢量 Logo（黑白灰极简风）+ 同源应用图标
- ✅ 树输入：粘贴 Newick/Nexus 文本或上传文件
- ✅ 布局：rectilinear / polar / radial
- ✅ 末端标签显隐 + 径向对齐
- ✅ 外观：背景色、前景色、分支线宽、字体/字号/样式/标签色
- ✅ 按分类级别自动配色（`--auto-color`）
- ✅ 按分类级别折叠（`--collapse-rank` + cartoon/collapse 样式）
- ✅ 刻度轴 + 比例尺
- ✅ 节点/分支标签显隐与属性
- ✅ 极坐标参数（角度范围/根角度）
- ✅ 矩形树曲率
- ✅ 图例显隐与位置
- ✅ 实时 PNG/SVG/PDF/JPEG 预览
- ✅ 导出等效 CLI 命令 + JSON 配置
- ✅ 控制台入口 `figtreekit-studio`

### P1（规划中）
- Clade 级手动高亮/着色
- 分类学映射文件上传驱动配色/折叠（界面已标注「规划中」并禁用）
- 预设主题

### P2（规划中）
- 批量模式
- 历史/会话
- 输入校验反馈

---

## 架构

```
桌面窗口 (pywebview 原生窗口，可选 --browser 回退)
    │ HTTP (JSON, 仅本机回环)
    ▼
FigTreeKit Studio 后端 (Python)
  ┌──────────┐  ┌───────────┐  ┌──────────┐
  │ params   │  │ generator │  │ renderer │
  │ (schema) │  │ (→.nex)   │  │ (→png)   │
  └──────────┘  └───────────┘  └──────────┘
                     │               │
                     ▼               ▼
               figtreekit      figtree_patched.jar
               (CLI/API)       (java -jar)
```

所有生成/渲染逻辑复用 figtreekit，Studio 自身不含任何业务逻辑。
冻结打包（.app）时 generator 自动切换为进程内执行 figtreekit CLI。

---

## 项目结构

```
figtreekit_studio/
├── __init__.py
├── __main__.py             # python -m figtreekit_studio
├── cli.py                  # 控制台入口（桌面窗口 / --browser / --no-window）
├── desktop.py              # pywebview 原生桌面窗口
├── server.py               # HTTP 服务（仅 127.0.0.1）
├── core/
│   ├── params.py           # 参数 schema + UI↔figtreekit 映射
│   ├── generator.py        # 参数 → figtreekit → .nex（冻结时进程内执行）
│   ├── renderer.py         # .nex → png/pdf/svg
│   └── exporter.py         # 参数 → CLI 命令 + JSON 配置
├── static/
│   ├── index.html          # 调参表单 + 预览 + 导出区（i18n 就绪）
│   ├── app.js              # fetch API + 渲染逻辑 + 中英双语词典
│   ├── style.css
│   └── logo.svg            # 黑白灰极简 SVG Logo
└── data/
    └── figtree_patched.jar # 随包分发
assets/
└── icon.icns               # 由 logo.svg 生成的 macOS 应用图标
```

---

## 打包 macOS .app

```bash
# 1) 构建环境（Python 3.12 + PyInstaller + pywebview + figtreekit）
uv venv --python 3.12 .venv-build
uv pip install --python .venv-build/bin/python pyinstaller pywebview "figtreekit[render]>=1.1.3"

# 2) 打包
.venv-build/bin/pyinstaller "FigTreeKit Studio.spec" --noconfirm --clean

# 3) 冒烟验证（冻结环境完整生成链路）
"./dist/FigTreeKit Studio.app/Contents/MacOS/FigTreeKit Studio" --smoke-test
```

产物：`dist/FigTreeKit Studio.app`（含 icon.icns、static、JAR）。
备选方案：`python setup_py2app.py py2app`。

---

## 测试

```bash
cd FigTreeKit-Studio
pip install -e ".[dev]"
make check          # 静态检查 + 全部测试
```

`make test-strict` 会以 CI 的严格模式运行：**出现任何被跳过的用例即判失败**。
这是有意为之——静默跳过等于什么都没验却显示通过。

| 层级 | 内容 |
|------|------|
| 单元 | `params.to_cli_args` / `to_config_dict` 映射正确 |
| 单元 | exporter 与 generator 共用同一映射（无漂移） |
| 单元 | renderer JAR 缺失/超时错误处理 |
| 单元 | 两份 `figtree_patched.jar` 副本的 SHA-256 一致（防漂移） |
| 静态 | logo.svg / i18n 词典 / 页面 data-i18n 完整性 |
| 端到端 | 启动 server → POST Newick → 返回合法 PNG base64 |
| 端到端 | 冻结包内 `--smoke-test` 跑通完整生成链（CI 中执行） |

CI 覆盖 Python 3.11 与 3.12（与 `requires-python = ">=3.11"` 一致）。
静态检查与单元测试跑在 Ubuntu 上——被测代码没有 macOS 专属分支，且公开仓库的
Linux runner 免费而 macOS runner 按 10x 倍率计费；只有 PyInstaller 打包与
冻结包自检留在 macOS 上。

---

## 许可证

本项目以 **GPL-2.0-or-later** 授权。详见 [LICENSE](LICENSE)。

### ⚠️ 第三方组件的授权冲突（尚未解决）

仓库中随包分发的 `figtree_patched.jar` 内含 **iText（AGPL-3.0）**。
AGPL-3.0 与 GPL-2.0 不兼容，这一点**尚未有明确结论**。

完整的第三方组件清单、该 JAR 的 SHA-256 指纹、以及冲突的可选处理方向见
[NOTICE](NOTICE)。在完成复核前，请勿将本项目产物用于对外分发。

> 另注：README 此前称该 JAR 衍生自 "FigTree（GPL-2.0-or-later）"，
> 但 JAR 内随附的 LICENSE 文件实为 Apache-2.0，且 FigTree 上游的许可证
> 尚未能核实。`NOTICE` 中已记录这一不一致。

---

## 安全

发现安全问题请勿开公开 Issue，参见 [SECURITY.md](SECURITY.md)。

---

## 贡献

欢迎提交 Issue 和 Pull Request。使用 PR 模板中的清单，请确保：
- 提交前运行 `make check` 且全部通过
- 遵循现有的代码风格（Python: `from __future__ import annotations`；JS: vanilla, 无构建步骤）
- 不修改 `params.to_cli_args` 的单一事实来源设计
- 引入或修改第三方组件时同步更新 `NOTICE`

---

## 引用 / Citation

FigTreeKit Studio 基于 [`figtreekit`](https://pypi.org/project/figtreekit/) 构建。若你在研究中使用了 FigTreeKit（或其可视化前端 FigTreeKit Studio），请引用**你实际使用的那个 `figtreekit` 版本**：

> Zeng Z., Wang Y. (2026). *FigTreeKit: A Python toolkit for programmatic FigTree styling,
> taxonomy-aware clade auditing, and phylogenetic tree rendering* (Version ⟨填你实际使用的版本⟩) [计算机程序].
> Zenodo. https://doi.org/10.5281/zenodo.⟨对应的版本 DOI⟩

> ⚠️ **维护者注意（待处理）**：本段此前硬编码为 `Version 1.1.2` +
> `10.5281/zenodo.22273864`，但 `pyproject.toml` 的依赖下限已是
> `figtreekit[render]>=1.1.3`（实测解析到 1.1.4）。版本号与版本 DOI 必须成对
> 核对后一起更新——只改其一即产生错误引用。此处不代填，因为无法核实
> 1.1.3/1.1.4 各自的 Zenodo DOI。

- **PyPI（核心库）**：https://pypi.org/project/figtreekit/
- **源代码（核心库）**：https://github.com/ZengZichao/FigTreeKit
- **软件 DOI（concept，跨版本）**：https://doi.org/10.5281/zenodo.22043258
- **本前端（Zenodo）**：https://doi.org/10.5281/zenodo.22977933（v0.1.2）；
  concept DOI https://doi.org/10.5281/zenodo.22766959
- **本前端在 Zenodo 的存档**：https://doi.org/10.5281/zenodo.22977933（v0.1.2；
  跨版本 https://doi.org/10.5281/zenodo.22766959）
- **描述性文章预印本**（不作为软件引用）：https://doi.org/10.64898/2026.08.27.747475

BibTeX：

```bibtex
@software{figtreekit2026,
  author = {Zeng, Zichao and Wang, Yinzhao},
  title = {FigTreeKit: A Python toolkit for programmatic FigTree styling, taxonomy-aware clade auditing, and phylogenetic tree rendering},
  year = {2026},
  version = {1.1.2},
  publisher = {Zenodo},
  url = {https://github.com/ZengZichao/FigTreeKit},
  doi = {10.5281/zenodo.22273864}
  % TODO(维护者): 上面的 version 与 doi 必须成对更新为实际使用的 figtreekit
  % 版本（当前依赖下限为 >=1.1.3）。概念 DOI 10.5281/zenodo.22043258 始终有效。
}

@software{figtreekitstudio2026,
  author = {Zeng, Zichao and Wang, Yinzhao},
  title = {FigTreeKit Studio},
  year = {2026},
  version = {0.1.2},
  publisher = {Zenodo},
  url = {https://github.com/ZengZichao/FigTreeKit-Studio},
  doi = {10.5281/zenodo.22977933}
}
```
