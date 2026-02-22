#!/usr/bin/env python3
"""
主题管理器模块
支持深色/浅色主题系统，为miniCipher工具提供现代化界面
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional
from enum import Enum
from config_manager import ThemeType, get_config_manager


class ThemeColors:
    """主题颜色定义类"""
    
    # 浅色主题
    LIGHT = {
        "bg": "#ffffff",
        "fg": "#000000",
        "primary": "#2196F3",      # 科技蓝
        "secondary": "#f5f5f5",    # 浅灰背景
        "accent": "#4CAF50",       # 安全绿
        "success": "#4CAF50",      # 成功绿
        "warning": "#FF9800",      # 警告橙
        "error": "#F44336",        # 错误红
        "border": "#e0e0e0",       # 边框色
        "hover": "#1976D2",        # 悬停深蓝
        "active": "#0D47A1",       # 激活深蓝
        "text_primary": "#212121", # 主要文本
        "text_secondary": "#757575", # 次要文本
        "disabled": "#bdbdbd",     # 禁用状态
        "window_bg": "#ffffff",    # 窗口背景
        "frame_bg": "#fafafa",     # 框架背景
        "entry_bg": "#ffffff",     # 输入框背景
        "entry_fg": "#000000",     # 输入框文字
        "button_bg": "#2196F3",    # 按钮背景
        "button_fg": "#ffffff",    # 按钮文字
        "label_bg": "#ffffff",     # 标签背景
        "label_fg": "#212121",     # 标签文字
        "combobox_bg": "#ffffff",  # 下拉框背景
        "combobox_fg": "#000000",  # 下拉框文字
        "status_bg": "#e3f2fd",    # 状态栏背景
        "status_fg": "#1976D2",    # 状态栏文字
    }
    
    # 深色主题
    DARK = {
        "bg": "#2b2b2b",
        "fg": "#ffffff",
        "primary": "#2196F3",      # 科技蓝
        "secondary": "#424242",    # 深灰背景
        "accent": "#4CAF50",       # 安全绿
        "success": "#4CAF50",      # 成功绿
        "warning": "#FF9800",      # 警告橙
        "error": "#F44336",        # 错误红
        "border": "#616161",       # 边框色
        "hover": "#1976D2",        # 悬停深蓝
        "active": "#0D47A1",       # 激活深蓝
        "text_primary": "#ffffff", # 主要文本
        "text_secondary": "#b0b0b0", # 次要文本
        "disabled": "#757575",     # 禁用状态
        "window_bg": "#2b2b2b",    # 窗口背景
        "frame_bg": "#37474F",     # 框架背景
        "entry_bg": "#424242",     # 输入框背景
        "entry_fg": "#ffffff",     # 输入框文字
        "button_bg": "#2196F3",    # 按钮背景
        "button_fg": "#ffffff",    # 按钮文字
        "label_bg": "#2b2b2b",     # 标签背景
        "label_fg": "#ffffff",     # 标签文字
        "combobox_bg": "#424242",  # 下拉框背景
        "combobox_fg": "#ffffff",  # 下拉框文字
        "status_bg": "#37474F",    # 状态栏背景
        "status_fg": "#90CAF9",    # 状态栏文字
    }


class ThemeManager:
    """主题管理器类"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.current_theme = self.config_manager.get_theme()
        self.colors = self._get_colors(self.current_theme)
        
    def _get_colors(self, theme: str) -> Dict[str, str]:
        """获取指定主题的颜色配置"""
        if theme == ThemeType.DARK.value:
            return ThemeColors.DARK
        else:
            return ThemeColors.LIGHT
    
    def get_theme(self) -> str:
        """获取当前主题"""
        return self.current_theme
    
    def set_theme(self, theme: str) -> None:
        """设置主题"""
        if theme not in [ThemeType.LIGHT.value, ThemeType.DARK.value]:
            raise ValueError(f"不支持的主题: {theme}")
        
        self.current_theme = theme
        self.colors = self._get_colors(theme)
        self.config_manager.set_theme(theme)
    
    def get_colors(self) -> Dict[str, str]:
        """获取当前主题的颜色配置"""
        return self.colors.copy()
    
    def apply_to_window(self, window: tk.Tk) -> None:
        """将主题应用到窗口"""
        colors = self.colors
        window.configure(bg=colors["window_bg"])
    
    def create_style(self, style: ttk.Style) -> None:
        """创建ttk样式"""
        colors = self.colors
        
        # 配置整体样式
        style.theme_use('clam')  # 使用clam主题作为基础
        
        # 配置标签样式
        style.configure(
            "TLabel",
            background=colors["label_bg"],
            foreground=colors["label_fg"],
            font=("Segoe UI", 10)
        )
        
        # 配置按钮样式
        style.configure(
            "TButton",
            background=colors["button_bg"],
            foreground=colors["button_fg"],
            borderwidth=1,
            relief="raised",
            padding=(12, 6),
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "TButton",
            background=[("active", colors["active"]), ("!disabled", colors["button_bg"])],
            foreground=[("disabled", colors["disabled"]), ("!disabled", colors["button_fg"])],
            relief=[("pressed", "sunken"), ("!pressed", "raised")]
        )
        
        # 配置主按钮样式（用于重要操作）
        style.configure(
            "Primary.TButton",
            background=colors["primary"],
            foreground=colors["button_fg"],
            borderwidth=1,
            relief="raised",
            padding=(12, 6),
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "Primary.TButton",
            background=[("active", colors["active"]), ("!disabled", colors["primary"])],
            foreground=[("disabled", colors["disabled"]), ("!disabled", colors["button_fg"])]
        )
        
        # 配置成功按钮样式
        style.configure(
            "Success.TButton",
            background=colors["success"],
            foreground=colors["button_fg"],
            borderwidth=1,
            relief="raised",
            padding=(12, 6),
            font=("Segoe UI", 10, "bold")
        )
        
        # 配置输入框样式
        style.configure(
            "TEntry",
            fieldbackground=colors["entry_bg"],
            foreground=colors["entry_fg"],
            bordercolor=colors["border"],
            lightcolor=colors["border"],
            darkcolor=colors["border"],
            insertcolor=colors["entry_fg"],
            padding=5
        )
        
        # 配置下拉框样式
        style.configure(
            "TCombobox",
            fieldbackground=colors["combobox_bg"],
            foreground=colors["combobox_fg"],
            background=colors["combobox_bg"],
            bordercolor=colors["border"],
            arrowcolor=colors["combobox_fg"],
            padding=5
        )
        
        # 配置框架样式
        style.configure(
            "TFrame",
            background=colors["frame_bg"]
        )
        
        # 配置LabelFrame样式
        style.configure(
            "TLabelframe",
            background=colors["frame_bg"],
            foreground=colors["label_fg"],
            bordercolor=colors["border"]
        )
        style.configure(
            "TLabelframe.Label",
            background=colors["frame_bg"],
            foreground=colors["label_fg"]
        )
        
        # 配置滚动条样式
        style.configure(
            "Vertical.TScrollbar",
            background=colors["secondary"],
            troughcolor=colors["window_bg"],
            bordercolor=colors["border"],
            arrowcolor=colors["text_primary"]
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=colors["secondary"],
            troughcolor=colors["window_bg"],
            bordercolor=colors["border"],
            arrowcolor=colors["text_primary"]
        )
    
    def apply_to_widget(self, widget: tk.Widget) -> None:
        """将主题应用到单个widget"""
        colors = self.colors
        
        if isinstance(widget, tk.Label):
            # 检查是否为状态栏（通常有bd=1和relief=tk.SUNKEN）
            if hasattr(widget, 'cget'):
                try:
                    relief = widget.cget('relief')
                    bd = widget.cget('bd')
                    if relief == tk.SUNKEN and bd == 1:
                        # 状态栏使用特定的状态栏颜色
                        widget.configure(bg=colors["status_bg"], fg=colors["status_fg"])
                        return
                except:
                    pass
            widget.configure(bg=colors["label_bg"], fg=colors["label_fg"])
        elif isinstance(widget, tk.Button):
            widget.configure(bg=colors["button_bg"], fg=colors["button_fg"], 
                           activebackground=colors["active"], activeforeground=colors["button_fg"])
        elif isinstance(widget, tk.Entry):
            widget.configure(bg=colors["entry_bg"], fg=colors["entry_fg"], 
                           insertbackground=colors["entry_fg"])
        elif isinstance(widget, tk.Frame):
            widget.configure(bg=colors["frame_bg"])
        elif isinstance(widget, tk.LabelFrame):
            widget.configure(bg=colors["frame_bg"], fg=colors["label_fg"])
        elif isinstance(widget, tk.Text):
            widget.configure(bg=colors["entry_bg"], fg=colors["entry_fg"], 
                           insertbackground=colors["entry_fg"])
        elif isinstance(widget, tk.Listbox):
            widget.configure(bg=colors["entry_bg"], fg=colors["entry_fg"])
        elif isinstance(widget, tk.Scrollbar):
            widget.configure(bg=colors["secondary"], troughcolor=colors["window_bg"])
    
    def apply_to_all_widgets(self, parent: tk.Widget) -> None:
        """将主题递归应用到所有子widget"""
        self.apply_to_widget(parent)
        
        for child in parent.winfo_children():
            if isinstance(child, tk.Widget):
                self.apply_to_widget(child)
                # 递归处理子widget
                self.apply_to_all_widgets(child)


# 单例实例
_theme_manager: Optional[ThemeManager] = None

def get_theme_manager() -> ThemeManager:
    """获取主题管理器单例实例"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def apply_theme_to_window(window: tk.Tk) -> None:
    """应用主题到窗口的便捷函数"""
    theme_manager = get_theme_manager()
    theme_manager.apply_to_window(window)
    
    # 创建并应用ttk样式
    style = ttk.Style(window)
    theme_manager.create_style(style)


if __name__ == "__main__":
    # 测试主题管理器
    root = tk.Tk()
    root.title("主题管理器测试")
    root.geometry("400x300")
    
    theme_manager = get_theme_manager()
    apply_theme_to_window(root)
    
    # 测试不同组件
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)
    
    label = ttk.Label(frame, text="主题管理器测试")
    label.pack(pady=10)
    
    entry = ttk.Entry(frame)
    entry.pack(pady=10)
    entry.insert(0, "输入测试")
    
    combo = ttk.Combobox(frame, values=["选项1", "选项2", "选项3"])
    combo.pack(pady=10)
    combo.set("选项1")
    
    button1 = ttk.Button(frame, text="普通按钮")
    button1.pack(pady=10)
    
    button2 = ttk.Button(frame, text="主按钮", style="Primary.TButton")
    button2.pack(pady=10)
    
    button3 = ttk.Button(frame, text="成功按钮", style="Success.TButton")
    button3.pack(pady=10)
    
    # 显示当前主题
    theme_label = ttk.Label(frame, text=f"当前主题: {theme_manager.get_theme()}")
    theme_label.pack(pady=10)
    
    # 测试主题切换
    def switch_theme():
        current = theme_manager.get_theme()
        new_theme = ThemeType.DARK.value if current == ThemeType.LIGHT.value else ThemeType.LIGHT.value
        theme_manager.set_theme(new_theme)
        apply_theme_to_window(root)
        theme_label.config(text=f"当前主题: {theme_manager.get_theme()}")
    
    switch_btn = ttk.Button(frame, text="切换主题", command=switch_theme)
    switch_btn.pack(pady=10)
    
    root.mainloop()