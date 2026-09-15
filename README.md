# FigTreeKit Studio

> 桌面应用 · 可视化调参 · 实时预览 · 可复现脚本导出

FigTreeKit Studio 是 [`figtreekit`](https://pypi.org/project/figtreekit/) 的可视化前端。
它提供图形界面调参、实时 PNG 预览、等效 CLI 命令与 JSON 配置导出，
让非编程的生物学家、审稿人也能快速样式化系统发育树，同时保持完全可复现性。

[🇬🇧 English](README_EN.md) · 🇨🇳 中文

**v0.1.1 维护更新**
- 🖥️ **独立桌面应用**：原生窗口运行（pywebview），不依赖浏览器
- 🌐 **中英文双语界面**：一键切换（右上角 `EN / 中文`），自动记忆，首次按系统语言选择
- 🌿 **SVG 矢量 Logo**：黑白灰配色的极简系统发育树（`static/logo.svg`），同步用作应用图标
- ♿ **无障碍设计**：WCAG AA 对比度、`aria-live` 状态播报、键盘焦点管理
- 🔒 **安全加固**：路径穿越防护、CSP 安全头、请求体大小上限

**设计原则**：薄前端（前端零业务逻辑）+ 核心零改动（直接复用 figtreekit）+
可复现性优先（GUI 所见 = 命令行所得）。

---

## 安装

```bash
pip install figtreekit-studio
```

**运行时依赖**：
- Python 3.11+
- Java 8+（JRE/JDK，用于渲染）
- `figtreekit` 1.1.2+（自动安装）
- `pywebview` 5.0+（自动安装，提供原生桌面窗口）

macOS 验证通过；Windows/Linux 理论兼容（界面层规避原生控件）。

> ⚠️ 本项目处于 Alpha 阶段（v0.1.1），API 和界面可能随版本迭代调整。

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

### 当前版本（v0.1.1）
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
uv pip install --python .venv-build/bin/python pyinstaller pywebview "figtreekit>=1.1.2"

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
cd FigTreeKit-Studio-项目代码
pip install pytest
python -m pytest tests/ -v
```

| 层级 | 内容 |
|------|------|
| 单元 | `params.to_cli_args` / `to_config_dict` 映射正确 |
| 单元 | exporter 与 generator 共用同一映射（无漂移） |
| 单元 | renderer JAR 缺失/超时错误处理 |
| 静态 | logo.svg / i18n 词典 / 页面 data-i18n 完整性 |
| 端到端 | 启动 server → POST Newick → 返回合法 PNG base64 |

---

## 许可证

GPL-2.0-or-later（与 figtreekit 一致）。详见 [LICENSE](LICENSE)。

内嵌 `figtree_patched.jar` 衍生自 FigTree v1.4.4（GPL-2.0-or-later），含 iText（AGPL-3.0）。

---

## 贡献

欢迎提交 Issue 和 Pull Request。请确保：
- 提交前运行 `python -m pytest tests/ -v` 且全部通过
- 遵循现有的代码风格（Python: `from __future__ import annotations`；JS: vanilla, 无构建步骤）
- 不修改 `params.to_cli_args` 的单一事实来源设计

---

## 引用 / Citation

FigTreeKit Studio 基于 [`figtreekit`](https://pypi.org/project/figtreekit/) 构建。若你在研究中使用了 FigTreeKit（或其可视化前端 FigTreeKit Studio），请引用：

> Zeng Z. (2026). *FigTreeKit: A Python toolkit for programmatic FigTree styling, taxonomy-aware clade auditing, and phylogenetic tree rendering*. https://doi.org/10.64898/2026.08.27.747475

- **PyPI**：https://pypi.org/project/figtreekit/
- **源代码**：https://github.com/ZengZichao/FigTreeKit
- **DOI**：https://doi.org/10.64898/2026.08.27.747475

BibTeX：

```bibtex
@software{figtreekit2026,
  author = {Zeng, Zichao},
  title = {FigTreeKit: A Python toolkit for programmatic FigTree styling, taxonomy-aware clade auditing, and phylogenetic tree rendering},
  year = {2026},
  url = {https://github.com/ZengZichao/FigTreeKit},
  doi = {10.64898/2026.08.27.747475}
}
```
