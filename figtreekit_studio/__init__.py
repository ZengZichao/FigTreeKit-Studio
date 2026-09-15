"""
FigTreeKit Studio — Visual front-end + reproducible script generator for figtreekit.

Studio 是 ``figtreekit`` 的可视化入口：提供图形界面调参、实时 PNG 预览、
等效 CLI 命令与 JSON 配置导出。所有样式生成与渲染逻辑复用 figtreekit，
Studio 自身不含任何业务逻辑（"薄前端"原则）。
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
