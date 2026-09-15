# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
