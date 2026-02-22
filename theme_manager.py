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
        "menu_bg": "#ffffff",      # 菜单背景
        "menu_fg": "#212121",      # 菜单文字
        "menu_active_bg": "#2196F3", # 菜单激活背景
        "menu_active_fg": "#ffffff", # 菜单激活文字
        "menu_disabled_fg": "#bdbdbd", # 菜单禁用文字
    }
    
    # 深色主题 - 优化对比度，改进按钮可见性
    DARK = {
        "bg": "#1e1e1e",           # 更深的背景，减少刺眼感
        "fg": "#e0e0e0",           # 稍暗的白色，降低对比度
        "primary": "#1565C0",      # 更深的科技蓝，提高对比度
        "secondary": "#303030",    # 深灰背景，与主背景区分
        "accent": "#81C784",       # 更亮的绿色，提高可见性
        "success": "#81C784",      # 成功绿
        "warning": "#FFB74D",      # 更柔和的警告橙
        "error": "#E57373",        # 更柔和的错误红
        "border": "#555555",       # 边框色，提高对比度
        "hover": "#0D47A1",        # 悬停深蓝
        "active": "#0D47A1",       # 激活更深蓝
        "text_primary": "#ffffff", # 主要文本（保持白色）
        "text_secondary": "#aaaaaa", # 次要文本，提高可读性
        "disabled": "#666666",     # 禁用状态，更明显的灰色
        "window_bg": "#1e1e1e",    # 窗口背景
        "frame_bg": "#252525",     # 框架背景，与窗口背景区分
        "entry_bg": "#2d2d2d",     # 输入框背景，提高对比度
        "entry_fg": "#ffffff",     # 输入框文字
        "button_bg": "#1565C0",    # 按钮背景（使用更深的蓝色提高对比度）
        "button_fg": "#ffffff",    # 按钮文字
        "label_bg": "#1e1e1e",     # 标签背景
        "label_fg": "#ffffff",     # 标签文字
        "combobox_bg": "#2d2d2d",  # 下拉框背景
        "combobox_fg": "#ffffff",  # 下拉框文字
        "status_bg": "#252525",    # 状态栏背景
        "status_fg": "#90CAF9",    # 状态栏文字
        "menu_bg": "#252525",      # 菜单背景
        "menu_fg": "#e0e0e0",      # 菜单文字
        "menu_active_bg": "#1565C0", # 菜单激活背景
        "menu_active_fg": "#ffffff", # 菜单激活文字
        "menu_disabled_fg": "#666666", # 菜单禁用文字
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
        
        # Windows特定的深色标题栏支持
        import sys
        if sys.platform == "win32" and self.current_theme == "dark":
            try:
                # 尝试使用Windows API设置深色标题栏
                # 这需要在Windows 10/11上
                window.update()  # 确保窗口已创建
                
                # 尝试使用Windows特定属性
                try:
                    # 在某些Tkinter版本中，可以尝试这个
                    window.wm_attributes("-transparentcolor", "")
                except:
                    pass
                    
                # 另一种方法：尝试设置窗口样式
                try:
                    import ctypes
                    # Windows 10/11深色模式API
                    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                    DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
                    
                    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
                    
                    # 尝试较新的API
                    try:
                        ctypes.windll.dwmapi.DwmSetWindowAttribute(
                            hwnd,
                            DWMWA_USE_IMMERSIVE_DARK_MODE,
                            ctypes.byref(ctypes.c_int(1)),
                            ctypes.sizeof(ctypes.c_int)
                        )
                    except:
                        # 尝试较旧的API
                        try:
                            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                                hwnd,
                                DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                                ctypes.byref(ctypes.c_int(1)),
                                ctypes.sizeof(ctypes.c_int)
                            )
                        except:
                            pass
                except Exception as e:
                    # 如果Windows API调用失败，静默忽略
                    pass
                    
                # 额外尝试：强制重新绘制菜单栏
                try:
                    # 尝试重新配置窗口的菜单
                    if "menu" in window.children:
                        menu = window["menu"]
                        if menu:
                            self._force_windows_menu_color(menu)
                except:
                    pass
                    
            except Exception as e:
                # 静默处理所有异常，不影响应用程序运行
                pass
    
    def create_style(self, style: ttk.Style) -> None:
        """创建ttk样式"""
        colors = self.colors
        
        # 使用clam主题以获得更好的颜色控制
        # clam主题在所有平台上都可用，且支持完整的自定义颜色
        style.theme_use('clam')
        
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
        
        # 检查是否为ttk小部件（ttk小部件不支持直接的bg/fg选项）
        is_ttk_widget = hasattr(widget, '_w') and isinstance(widget, (ttk.Label, ttk.Button, ttk.Entry, 
                                                                     ttk.Frame, ttk.LabelFrame, ttk.Combobox,
                                                                     ttk.Scrollbar, ttk.Checkbutton, ttk.Radiobutton))
        
        # 对于ttk小部件，样式系统已经处理了颜色，跳过直接的bg/fg配置
        # 但需要检查是否为ttk.Label等，避免错误
        if isinstance(widget, ttk.Label) or isinstance(widget, ttk.Button) or \
           isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Frame) or \
           isinstance(widget, ttk.LabelFrame) or isinstance(widget, ttk.Combobox):
            # ttk小部件使用样式系统，跳过直接配置
            # 注意：ttk小部件的样式已经在create_style方法中配置
            return
            
        elif isinstance(widget, tk.Label):
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
            # tk.Scrollbar 在某些平台上可能不支持所有选项，安全地配置
            try:
                widget.configure(bg=colors["secondary"])
            except tk.TclError:
                pass
            try:
                widget.configure(troughcolor=colors["window_bg"])
            except tk.TclError:
                pass
        elif isinstance(widget, ttk.Scrollbar):
            # ttk.Scrollbar 通过样式系统处理，跳过直接配置
            pass
        elif isinstance(widget, tk.Menu):
            # 应用主题到菜单组件 - 改进版，确保所有菜单项正确应用颜色
            try:
                widget.configure(
                    bg=colors["menu_bg"], 
                    fg=colors["menu_fg"],
                    activebackground=colors["menu_active_bg"],
                    activeforeground=colors["menu_active_fg"],
                    selectcolor=colors["menu_active_bg"]
                )
                
                # 对于所有菜单项类型，确保颜色正确应用
                for index in range(widget.index("end") + 1):
                    try:
                        # 获取菜单项类型
                        menu_type = widget.type(index)
                        
                        # 配置菜单项
                        if menu_type == "command":
                            # 普通命令项
                            widget.entryconfigure(
                                index,
                                background=colors["menu_bg"],
                                foreground=colors["menu_fg"],
                                activebackground=colors["menu_active_bg"],
                                activeforeground=colors["menu_active_fg"]
                            )
                        elif menu_type == "cascade":
                            # 级联菜单（子菜单）
                            widget.entryconfigure(
                                index,
                                background=colors["menu_bg"],
                                foreground=colors["menu_fg"],
                                activebackground=colors["menu_active_bg"],
                                activeforeground=colors["menu_active_fg"]
                            )
                            # 递归应用到子菜单
                            submenu = widget.nametowidget(widget.entrycget(index, "menu"))
                            if isinstance(submenu, tk.Menu):
                                self.apply_to_widget(submenu)
                        elif menu_type == "separator":
                            # 分隔符
                            widget.entryconfigure(
                                index,
                                background=colors["border"],
                                activebackground=colors["border"]
                            )
                    except (tk.TclError, ValueError, TypeError):
                        # 忽略菜单项配置错误，继续处理其他项
                        continue
                
                # 特别处理禁用状态
                try:
                    widget.entryconfigure("disabled", foreground=colors["menu_disabled_fg"])
                except tk.TclError:
                    pass
                    
            except Exception as e:
                # 静默处理菜单配置异常，但记录错误以便调试
                import traceback
                print(f"警告: 菜单主题配置失败: {e}")
                traceback.print_exc()
    
    def apply_to_all_widgets(self, parent: tk.Widget) -> None:
        """将主题递归应用到所有子widget"""
        self.apply_to_widget(parent)
        
        for child in parent.winfo_children():
            if isinstance(child, tk.Widget):
                self.apply_to_widget(child)
                # 递归处理子widget
                self.apply_to_all_widgets(child)
        
        # 特别处理窗口的菜单（Windows系统需要特殊处理）
        if isinstance(parent, tk.Tk):
            try:
                # 获取窗口的菜单栏
                menu = parent["menu"]
                if menu:
                    self.apply_to_widget(menu)
                    # Windows系统需要额外的颜色刷新
                    import sys
                    if sys.platform == "win32":
                        self._force_windows_menu_color(menu)
            except (tk.TclError, KeyError):
                pass
    
    def _force_windows_menu_color(self, menu: tk.Menu) -> None:
        """强制Windows系统上的菜单颜色应用"""
        colors = self.colors
        try:
            # 多次刷新菜单颜色，确保Windows系统接受颜色设置
            menu.configure(
                bg=colors["menu_bg"],
                fg=colors["menu_fg"],
                activebackground=colors["menu_active_bg"],
                activeforeground=colors["menu_active_fg"],
                selectcolor=colors["menu_active_bg"]
            )
            
            # 更新窗口以应用颜色
            if menu.master:
                menu.master.update()
                
            # 短暂延迟后再次应用，确保颜色被接受
            import threading
            def reapply_colors():
                import time
                time.sleep(0.1)
                try:
                    menu.configure(
                        bg=colors["menu_bg"],
                        fg=colors["menu_fg"]
                    )
                except:
                    pass
            
            threading.Thread(target=reapply_colors, daemon=True).start()
            
        except Exception as e:
            # 静默处理异常，不影响应用程序运行
            pass


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


def apply_theme_to_toplevel(toplevel: tk.Toplevel) -> None:
    """应用主题到Toplevel窗口的便捷函数"""
    theme_manager = get_theme_manager()
    theme_manager.apply_to_window(toplevel)
    
    # 创建并应用ttk样式
    style = ttk.Style(toplevel)
    theme_manager.create_style(style)
    
    # 应用主题到所有现有子部件
    theme_manager.apply_to_all_widgets(toplevel)


class CustomMessageBox:
    """自定义消息框，支持主题颜色"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.theme_manager = get_theme_manager()
        self.colors = self.theme_manager.get_colors()
    
    def _create_dialog(self, title: str, message: str, icon_type: str = "info") -> tk.Toplevel:
        """创建对话框窗口"""
        dialog = tk.Toplevel(self.parent)
        dialog.title(title)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # 阻止用户关闭对话框
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # 应用主题
        apply_theme_to_toplevel(dialog)
        
        # 设置对话框外观
        dialog.configure(bg=self.colors["window_bg"])
        
        # 创建内容框架
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)
        
        # 图标（基于类型）
        icon_text = ""
        icon_color = self.colors["primary"]
        if icon_type == "error":
            icon_text = "✗"
            icon_color = self.colors["error"]
        elif icon_type == "warning":
            icon_text = "⚠"
            icon_color = self.colors["warning"]
        elif icon_type == "success":
            icon_text = "✓"
            icon_color = self.colors["success"]
        else:  # info
            icon_text = "ℹ"
            icon_color = self.colors["primary"]
        
        # 图标标签
        if icon_text:
            icon_label = tk.Label(frame, text=icon_text, font=("Segoe UI", 24), 
                                bg=self.colors["window_bg"], fg=icon_color)
            icon_label.pack(pady=(0, 10))
        
        # 消息文本
        message_label = tk.Label(frame, text=message, wraplength=400, justify="left",
                               bg=self.colors["window_bg"], fg=self.colors["text_primary"],
                               font=("Segoe UI", 10))
        message_label.pack(pady=10, fill="x")
        
        # 按钮框架
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=(10, 0))
        
        return dialog, button_frame
    
    def show_info(self, title: str, message: str) -> None:
        """显示信息对话框"""
        dialog, button_frame = self._create_dialog(title, message, "info")
        
        # 确定按钮
        ok_button = ttk.Button(button_frame, text="确定", 
                              command=dialog.destroy,
                              style="Primary.TButton")
        ok_button.pack(side="left", padx=5)
        
        # 居中对话框
        self._center_dialog(dialog)
        dialog.wait_window()
    
    def show_error(self, title: str, message: str) -> None:
        """显示错误对话框"""
        dialog, button_frame = self._create_dialog(title, message, "error")
        
        # 确定按钮
        ok_button = ttk.Button(button_frame, text="确定", 
                              command=dialog.destroy,
                              style="Primary.TButton")
        ok_button.pack(side="left", padx=5)
        
        # 居中对话框
        self._center_dialog(dialog)
        dialog.wait_window()
    
    def show_warning(self, title: str, message: str) -> None:
        """显示警告对话框"""
        dialog, button_frame = self._create_dialog(title, message, "warning")
        
        # 确定按钮
        ok_button = ttk.Button(button_frame, text="确定", 
                              command=dialog.destroy,
                              style="Primary.TButton")
        ok_button.pack(side="left", padx=5)
        
        # 居中对话框
        self._center_dialog(dialog)
        dialog.wait_window()
    
    def show_success(self, title: str, message: str) -> None:
        """显示成功对话框"""
        dialog, button_frame = self._create_dialog(title, message, "success")
        
        # 确定按钮
        ok_button = ttk.Button(button_frame, text="确定", 
                              command=dialog.destroy,
                              style="Success.TButton")
        ok_button.pack(side="left", padx=5)
        
        # 居中对话框
        self._center_dialog(dialog)
        dialog.wait_window()
    
    def _center_dialog(self, dialog: tk.Toplevel) -> None:
        """居中对话框"""
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        
        if self.parent:
            x = self.parent.winfo_x() + (self.parent.winfo_width() - width) // 2
            y = self.parent.winfo_y() + (self.parent.winfo_height() - height) // 2
        else:
            # 如果没有父窗口，居中于屏幕
            screen_width = dialog.winfo_screenwidth()
            screen_height = dialog.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
        
        dialog.geometry(f"{width}x{height}+{x}+{y}")


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