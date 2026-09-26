# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-09-26

### Fixed

- 渲染与配色全部下沉到 `figtreekit` 核心：删除 Studio 自己的位图重着色
  （`core/renderer.py` 的 Pillow 通道）与事后改写 NEXUS 标签色的私有 API 调用
  （`core/generator.py`）。前端因此确实不含自有样式逻辑。
- 导出记录的渲染步骤改为 `figtreekit --render`（而非裸 `java -jar`），使导出的
  命令行逐像素复现界面预览（由 `tests/test_exporter.py::TestReplayEquivalence` 断言：
  重放导出的命令后，序列注释与渲染像素均与界面预览一致）。
- 导出的命令行对 `#RRGGBB` 一类值做 shell 引号包裹，避免 `#` 被 shell 当注释而
  丢参数。
- `--host` 不再无校验透传：非回环绑定必须显式 `--allow-remote-bind`，并加测试。
- WCAG AA 文本颜色令牌达标（`--mut`、`--accent`、`--line-strong`），加自动对比度
  测试；修正 `style.css` 中与实测不符的注释。
- `check_java()` 现在真正解析并强制 Java 版本下限（此前只判断 java 是否存在）。
- `locate_jar()` 优先取核心库内的权威 JAR 副本，打包内副本降为回退，消除版本漂移方向。
- CI 增加打包构建与 `--smoke-test` 自检两个步骤：进程内跑测试从未证明冻结包
  可用，而 PyInstaller 数据文件、内置 JAR 与打包后的入口点恰恰只有构建之后才
  存在。`--smoke-test` 同时取消隐藏，出现在 `--help` 中。
- 工作目录改为按会话归拢（`ftk_session_<id>/run_<id>/`）：同一次会话的多次生成
  因此可整体审阅与留存，且不会与相邻会话的输出交错。
- `LICENSE` 换为规范 GPL-2.0-or-later 全文（原为删节版，缺 “or later” 授权段）；
  `CITATION.cff` 修正版本号、补全作者与单位。
- README 安装路径改为可用的仓库安装方式（`pip install figtreekit-studio` 在 PyPI
  不存在），补出仓库 URL；平台表述与 CI 实况一致（仅 macOS 验证）。

### Fixed — 冻结包（本次实测构建暴露）

- `ci.yml` 的打包步骤原先传 `--no-banner`，PyInstaller 无此参数，构建即失败；
  改为 `--noconfirm`（非交互覆盖输出目录）。
- `--smoke-test` 未传工作目录，而 0.1.1 起 `/api/generate` 必填该项，自检因此
  必定返回 `请指定工作路径`；改为用临时目录驱动完整生成链，并断言会话目录下
  确实产出文件，退出前清理。
- 打包配置原先只在 `hiddenimports` 里写了包名 `figtreekit`：子模块（`_cli`、
  `_renderer`、`_appearance_post` 等）与 `figtree_patched.jar` 均不会被收集，
  0.1.2 把渲染下沉到核心后冻结包在首次生成时抛
  `ModuleNotFoundError: No module named 'figtreekit._cli'`。改用
  `collect_submodules()` + `collect_data_files()`，并以 `importlib` 解析核心的
  真实源码目录加入 `pathex`——PyInstaller 按 `sys.path` 查找，无法定位 PEP 660
  可编辑安装，会静默丢模块并只留下 `Hidden import ... not found` 日志。
  spec 内加了两条断言，收集失败时构建直接失败而非产出坏包。

实测：`dist/FigTreeKit Studio.app/.../FigTreeKit Studio --smoke-test` 退出码 0，
输出 `SMOKE TEST PASSED`，会话目录下 3 个产物；包内同时含核心与前端两份
`figtree_patched.jar`。

### Tests
- 82 → 100 项；新增回放等价、绑定地址、对比度、JAR 一致性与 Java 版本下限测试。

> 待办：为 0.1.2 打 tag；Zenodo 会随 tag 自动产出该版本的存档 DOI，届时把
> `CITATION.cff` 的 version/date-released/doi 一并提升。任何外部文档若按版本号
> 引用本前端，都应等该 tag 存在之后再引用。
> 注：0.1.1 已在 Zenodo 存档（版本 DOI 10.5281/zenodo.22766960，
> concept DOI 10.5281/zenodo.22766959）。

## [0.1.1] - 2026-09-15

### Added
- 必填工作路径：生成预览前必须指定工作目录，中间文件保留在 `ftk_run_xxxxxxxx` 子目录
- 工作路径浏览按钮：桌面应用模式下调用原生文件夹选择器
- 实时预览自动触发：参数变化后自动防抖渲染，无需重复点击生成按钮
- 输入框统一高度 34px
- GitHub Actions CI 工作流（macOS + Python 3.12 + Java 17）

### Changed
- "前景色" 改名为 "分支颜色"
- 选项卡中的 "关" 统一改为 "显示 / 隐藏"
- 布局选项中文改为纯中文（矩形树 / 极坐标 / 放射状）
- 分类学级别中文改为纯中文（域 / 门 / 纲 / 目 / 科 / 属 / 种）
- 图例位置中文改为纯中文（底部 / 顶部 / 左侧 / 右侧）
- 曲率默认值从 `-1` 改为 `0`，标签改为 "曲率"，placeholder 说明 `0=直角，>0=圆角`
- 折叠级别 / 折叠样式改为同一行水平对齐
- CLI / JSON 导出标题去除带圈数字
- 健康检查状态图标改为文字（正常/异常，英文 OK/FAIL）

### Fixed
- 左侧栏颜色参数未传递到实时预览（背景色/前景色/标签色现在生效）
- 未设置背景色时预览显示黑色（改为默认白色背景）
- 曲率设置无效的认知问题（实际有效，UI 提示更清晰）
- 径向对齐标签点不点都一样（figtreekit 默认 True，未勾选时显式写入 False）
- 中英界面混排问题
- 界面 emoji 过多
- 前景色渲染测试对抗锯齿过渡色过于严格

## [0.1.0] - 2026-09-15

### Added
- 桌面应用：原生窗口运行（pywebview / WKWebView），不依赖浏览器
- 中英文双语界面，一键切换并记忆，首次按系统语言自动选择
- SVG 矢量 Logo（黑白灰极简系统发育树），同步用作应用图标
- 树输入：粘贴 Newick/Nexus 文本或上传 `.tre/.nwk/.nex` 文件
- 布局：rectilinear / polar / radial
- 末端标签显隐 + 径向对齐
- 外观：背景色、前景色、分支线宽、字体/字号/样式/标签色
- 按分类级别自动配色（`--auto-color`）
- 按分类级别折叠（`--collapse-rank` + cartoon/collapse 样式）
- 刻度轴 + 比例尺
- 节点/分支标签显隐与属性
- 极坐标参数（角度范围/根角度）
- 矩形树曲率
- 图例显隐与位置
- 实时 PNG/SVG/PDF/JPEG 预览
- 导出等效 CLI 命令 + JSON 配置（共用 `to_cli_args` 单一事实来源）
- 控制台入口 `figtreekit-studio`
- 无障碍设计：WCAG AA 对比度、`aria-live` 状态播报、键盘焦点管理、`:focus-visible` 焦点环
- 安全加固：路径穿越防护、CSP 安全头、请求体大小上限（20 MB）
- 首屏语言门控（`visibility: hidden` 消除 FOUC）
- `prefers-reduced-motion` 适配
- 冻结模式进程内执行超时保护（`concurrent.futures`）
- 前端 `AbortController` + 在途保护，防止并发渲染

### Fixed
- JSON 配置导出 6 个键名与 figtreekit schema 不符的问题
- 分类映射文件只传文件名导致静默失效 → 禁用该控件并标注「规划中」
- 静态资源路径穿越漏洞（`realpath` + 前缀校验）
- 后端无异常兜底导致连接断连（`try/except` + `internal_error` 错误码）
- 小数字号/角度导致 figtreekit 生成失败（`step="1"` + `Math.trunc`）
- 比例尺"关"选项无效（补齐 `--scale-bar-hide` / `scaleBar.isShown = False`）
- CLI 参数白名单误伤中文/多字节字体名（移除白名单，参数以 list 传递无需 shell 转义）
- 冻结模式进程内执行并发不安全（`threading.Lock` 串行化）
- 前端健康检查图标判断错误（`ftkOk` 独立于 `jarOk`）
- `hide` 语义在 JSON 配置中缺失分支
- 冻结应用导出的 CLI 命令不可直接运行（固定使用 `python` 解释器名）
- 桌面模式运行期异常不触发浏览器回退（`except Exception: return False`）
- 临时目录从不清理（`finally: shutil.rmtree`）
- 字体栈断裂 `Roboto` → `Rob, oto`
- 颜色选择器与文本框「双真源」问题

### Security
- 静态资源服务路径穿越防护
- `Content-Security-Policy`、`X-Content-Type-Options: nosniff`、`Referrer-Policy: no-referrer`
- POST 请求体大小上限 20 MB