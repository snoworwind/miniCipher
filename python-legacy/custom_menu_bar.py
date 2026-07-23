#!/usr/bin/env python3
"""
自定义菜单栏模块
使用ttk按钮和框架模拟原生菜单功能，实现完全的颜色控制
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Callable, Any
from translations import TranslationKeys, get_translator, _
from theme_manager import get_theme_manager


class CustomMenuBar(ttk.Frame):
    """自定义菜单栏类 - 使用ttk组件模拟原生菜单"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.theme_manager = get_theme_manager()
        self.translator = get_translator()
        self.colors = self.theme_manager.get_colors()
        
        # 菜单项存储
        self.menu_items = {}
        self.active_menu = None  # 当前活动的菜单索引
        self.menu_frames = {}  # 存储菜单下拉框架
        
        # 配置自身样式
        self.configure_style()
        
        # 创建菜单栏容器
        self.create_menu_bar()
        # 注意：事件绑定在各个方法中完成，不需要单独的bind_events方法
    
    def configure_style(self):
        """配置菜单栏样式"""
        # 使用主题管理器的颜色
        self.colors = self.theme_manager.get_colors()
        
        # 创建菜单按钮样式
        style = ttk.Style(self)
        
        # 菜单按钮样式
        style.configure(
            "MenuButton.TButton",
            background=self.colors["menu_bg"],
            foreground=self.colors["menu_fg"],
            borderwidth=1,
            relief="flat",
            padding=(10, 5),
            font=("Segoe UI", 10)
        )
        
        # 菜单按钮悬停样式
        style.map(
            "MenuButton.TButton",
            background=[
                ("active", self.colors["menu_active_bg"]),
                ("!active", self.colors["menu_bg"])
            ],
            foreground=[
                ("active", self.colors["menu_active_fg"]),
                ("!active", self.colors["menu_fg"])
            ],
            relief=[
                ("pressed", "sunken"),
                ("active", "raised"),
                ("!active", "flat")
            ]
        )
        
        # 菜单项按钮样式
        style.configure(
            "MenuItem.TButton",
            background=self.colors["menu_bg"],
            foreground=self.colors["menu_fg"],
            borderwidth=0,
            relief="flat",
            padding=(20, 8),
            font=("Segoe UI", 10),
            anchor="w"
        )
        
        style.map(
            "MenuItem.TButton",
            background=[
                ("active", self.colors["menu_active_bg"]),
                ("!active", self.colors["menu_bg"])
            ],
            foreground=[
                ("active", self.colors["menu_active_fg"]),
                ("!active", self.colors["menu_fg"])
            ]
        )
        
        # 菜单分隔符样式
        style.configure(
            "MenuSeparator.TSeparator",
            background=self.colors["border"]
        )
    
    def create_menu_bar(self):
        """创建菜单栏主容器"""
        # 创建水平排列的菜单按钮容器
        self.menu_container = ttk.Frame(self)
        self.menu_container.pack(fill="x", side="top")
        
        # 应用背景色到菜单容器
        self.theme_manager.apply_to_widget(self.menu_container)
    
    def add_menu(self, label: str, items: List[Dict[str, Any]]) -> None:
        """添加一个菜单
        
        Args:
            label: 菜单标签（如"文件"）
            items: 菜单项列表，每个项是包含以下键的字典：
                - type: "command"（命令项）, "separator"（分隔符）, "cascade"（子菜单）
                - label: 菜单项标签
                - command: 命令函数（仅type="command"时需要）
                - items: 子菜单项列表（仅type="cascade"时需要）
        """
        # 创建菜单按钮
        menu_button = ttk.Button(
            self.menu_container,
            text=label,
            style="MenuButton.TButton",
            command=lambda label=label: self.toggle_menu(label)
        )
        menu_button.pack(side="left", padx=(0, 1))
        
        # 存储菜单信息
        menu_id = len(self.menu_items)
        self.menu_items[label] = {
            "id": menu_id,
            "button": menu_button,
            "items": items,
            "frame": None,  # 下拉菜单框架
            "visible": False
        }
        
        # 为菜单按钮绑定事件
        menu_button.bind("<Enter>", lambda e, lbl=label: self.on_menu_hover(lbl))
        menu_button.bind("<Leave>", lambda e: self.on_menu_leave())
    
    def create_menu_frame(self, menu_label: str) -> ttk.Frame:
        """创建菜单下拉框架"""
        menu_info = self.menu_items[menu_label]
        
        # 如果已存在框架，先销毁
        if menu_info["frame"] and menu_info["frame"].winfo_exists():
            menu_info["frame"].destroy()
        
        # 创建新的下拉框架（覆盖整个窗口）
        menu_frame = ttk.Frame(self.parent)
        menu_frame.configure(style="TFrame")
        
        # 设置框架位置（在菜单按钮下方）
        menu_button = menu_info["button"]
        menu_button_x = menu_button.winfo_rootx() - self.parent.winfo_rootx()
        menu_button_y = menu_button.winfo_rooty() - self.parent.winfo_rooty()
        menu_button_height = menu_button.winfo_height()
        
        frame_width = 180  # 菜单宽度
        frame_x = menu_button_x
        frame_y = menu_button_y + menu_button_height
        
        menu_frame.place(x=frame_x, y=frame_y, width=frame_width)
        menu_frame.lift()  # 确保在最上层
        
        # 创建菜单项
        self.create_menu_items(menu_frame, menu_label)
        
        # 存储框架引用
        menu_info["frame"] = menu_frame
        
        return menu_frame
    
    def create_menu_items(self, parent_frame: ttk.Frame, menu_label: str) -> None:
        """在框架中创建菜单项"""
        menu_info = self.menu_items[menu_label]
        
        # 清除现有内容
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        # 创建菜单项
        row = 0
        for item in menu_info["items"]:
            item_type = item.get("type", "command")
            
            if item_type == "command":
                # 命令项
                btn = ttk.Button(
                    parent_frame,
                    text=item["label"],
                    style="MenuItem.TButton",
                    command=lambda cmd=item.get("command"): self.execute_command(cmd)
                )
                btn.grid(row=row, column=0, sticky="ew", padx=0, pady=0)
                btn.bind("<Enter>", lambda e, b=btn: self.on_item_hover(b))
                btn.bind("<Leave>", lambda e, b=btn: self.on_item_leave(b))
                row += 1
                
            elif item_type == "separator":
                # 分隔符
                sep = ttk.Separator(parent_frame, style="MenuSeparator.TSeparator", orient="horizontal")
                sep.grid(row=row, column=0, sticky="ew", padx=10, pady=4)
                row += 1
                
            elif item_type == "cascade":
                # 子菜单（暂不实现完整级联，可扩展）
                btn = ttk.Button(
                    parent_frame,
                    text=item["label"] + " →",
                    style="MenuItem.TButton",
                    command=lambda: None  # 可以扩展为显示子菜单
                )
                btn.grid(row=row, column=0, sticky="ew", padx=0, pady=0)
                btn.bind("<Enter>", lambda e, b=btn: self.on_item_hover(b))
                btn.bind("<Leave>", lambda e, b=btn: self.on_item_leave(b))
                row += 1
        
        # 配置网格权重
        parent_frame.grid_columnconfigure(0, weight=1)
    
    def execute_command(self, command: Optional[Callable]) -> None:
        """执行菜单命令"""
        if command:
            command()
        # 关闭所有菜单
        self.close_all_menus()
    
    def toggle_menu(self, menu_label: str) -> None:
        """切换菜单显示/隐藏"""
        menu_info = self.menu_items[menu_label]
        
        if menu_info["visible"]:
            # 如果菜单已显示，关闭它
            self.close_menu(menu_label)
        else:
            # 关闭其他菜单
            self.close_all_menus()
            # 显示当前菜单
            self.show_menu(menu_label)
    
    def show_menu(self, menu_label: str) -> None:
        """显示指定菜单"""
        menu_info = self.menu_items[menu_label]
        
        # 创建菜单框架
        self.create_menu_frame(menu_label)
        
        # 更新状态
        menu_info["visible"] = True
        self.active_menu = menu_label
        
        # 更新菜单按钮状态
        menu_info["button"].state(["active"])
        
        # 绑定全局点击事件以关闭菜单
        self.parent.bind("<Button-1>", self.on_global_click, add="+")
    
    def close_menu(self, menu_label: str) -> None:
        """关闭指定菜单"""
        menu_info = self.menu_items[menu_label]
        
        # 安全检查：确保按钮存在
        button_exists = hasattr(menu_info["button"], 'winfo_exists') and menu_info["button"].winfo_exists()
        
        if menu_info["frame"] and hasattr(menu_info["frame"], 'winfo_exists') and menu_info["frame"].winfo_exists():
            menu_info["frame"].destroy()
            menu_info["frame"] = None
        
        menu_info["visible"] = False
        
        # 安全地更新菜单按钮状态
        if button_exists:
            try:
                menu_info["button"].state(["!active"])
            except tk.TclError:
                # 如果按钮状态设置失败，忽略错误
                pass
        
        # 如果没有活动菜单，移除全局点击事件
        if not any(m["visible"] for m in self.menu_items.values()):
            try:
                self.parent.unbind("<Button-1>")
            except tk.TclError:
                # 如果取消绑定失败，忽略错误
                pass
            self.active_menu = None
    
    def close_all_menus(self) -> None:
        """关闭所有菜单"""
        for menu_label in list(self.menu_items.keys()):
            self.close_menu(menu_label)
    
    def on_menu_hover(self, menu_label: str) -> None:
        """菜单按钮悬停事件"""
        # 如果有活动菜单且不是当前悬停的菜单，切换菜单
        if self.active_menu and self.active_menu != menu_label:
            self.close_menu(self.active_menu)
            self.show_menu(menu_label)
    
    def on_menu_leave(self) -> None:
        """菜单按钮离开事件"""
        # 这里可以添加延迟关闭逻辑
        pass
    
    def on_item_hover(self, button: ttk.Button) -> None:
        """菜单项悬停事件"""
        button.state(["active"])
    
    def on_item_leave(self, button: ttk.Button) -> None:
        """菜单项离开事件"""
        button.state(["!active"])
    
    def on_global_click(self, event) -> None:
        """全局点击事件 - 点击菜单外区域关闭菜单"""
        # 检查点击位置是否在菜单框架内
        clicked_in_menu = False
        
        for menu_info in self.menu_items.values():
            if menu_info["frame"] and menu_info["frame"].winfo_exists():
                frame = menu_info["frame"]
                frame_x = frame.winfo_x()
                frame_y = frame.winfo_y()
                frame_width = frame.winfo_width()
                frame_height = frame.winfo_height()
                
                # 检查点击位置是否在框架内
                if (frame_x <= event.x <= frame_x + frame_width and
                    frame_y <= event.y <= frame_y + frame_height):
                    clicked_in_menu = True
                    break
        
        # 如果点击在菜单外，关闭所有菜单
        if not clicked_in_menu:
            # 检查点击的是否是菜单按钮
            clicked_menu_button = False
            for menu_label, menu_info in self.menu_items.items():
                button = menu_info["button"]
                button_x = button.winfo_rootx() - self.parent.winfo_rootx()
                button_y = button.winfo_rooty() - self.parent.winfo_rooty()
                button_width = button.winfo_width()
                button_height = button.winfo_height()
                
                if (button_x <= event.x <= button_x + button_width and
                    button_y <= event.y <= button_y + button_height):
                    clicked_menu_button = True
                    break
            
            # 如果点击的不是菜单按钮，关闭所有菜单
            if not clicked_menu_button:
                self.close_all_menus()
    
    def update_colors(self) -> None:
        """更新菜单颜色"""
        # 更新颜色引用
        self.colors = self.theme_manager.get_colors()
        
        # 重新配置样式
        self.configure_style()
        
        # 更新菜单容器背景
        self.theme_manager.apply_to_widget(self.menu_container)
        
        # 更新所有菜单按钮
        for menu_info in self.menu_items.values():
            # 更新按钮样式
            if menu_info["button"].winfo_exists():
                # ttk按钮样式会自动更新，无需手动配置
                pass
            
            # 如果有活动的菜单框架，重新创建以应用新颜色
            if menu_info["visible"] and menu_info["frame"] and menu_info["frame"].winfo_exists():
                self.create_menu_frame(menu_info["button"].cget("text"))
    
    def update_language(self) -> None:
        """更新菜单语言"""
        # 这里可以实现多语言更新
        # 当前菜单文本已经在创建时使用了翻译函数
        pass


class CustomMenuBarBuilder:
    """自定义菜单栏构建器，简化菜单创建"""
    
    @staticmethod
    def create_for_cipher_gui(parent, cipher_gui_instance) -> CustomMenuBar:
        """为CipherGUI创建菜单栏"""
        menu_bar = CustomMenuBar(parent)
        
        # 文件菜单
        file_menu_items = [
            {
                "type": "command",
                "label": _(TranslationKeys.SETTINGS_MENU),
                "command": cipher_gui_instance._open_settings
            },
            {
                "type": "separator"
            },
            {
                "type": "command",
                "label": _(TranslationKeys.EXIT),
                "command": parent.quit
            }
        ]
        
        # 语言菜单
        language_menu_items = [
            {
                "type": "command",
                "label": "简体中文",
                "command": lambda: cipher_gui_instance._change_language("zh_CN")
            },
            {
                "type": "command",
                "label": "English",
                "command": lambda: cipher_gui_instance._change_language("en_US")
            }
        ]
        
        # 主题菜单
        theme_menu_items = [
            {
                "type": "command",
                "label": _(TranslationKeys.LIGHT_THEME),
                "command": lambda: cipher_gui_instance._change_theme("light")
            },
            {
                "type": "command",
                "label": _(TranslationKeys.DARK_THEME),
                "command": lambda: cipher_gui_instance._change_theme("dark")
            }
        ]
        
        # 帮助菜单
        help_menu_items = [
            {
                "type": "command",
                "label": _(TranslationKeys.ABOUT),
                "command": cipher_gui_instance._show_about
            }
        ]
        
        # 添加菜单
        menu_bar.add_menu(_(TranslationKeys.FILE_MENU), file_menu_items)
        menu_bar.add_menu(_(TranslationKeys.LANGUAGE_MENU), language_menu_items)
        menu_bar.add_menu(_(TranslationKeys.THEME_MENU), theme_menu_items)
        menu_bar.add_menu(_(TranslationKeys.HELP_MENU), help_menu_items)
        
        return menu_bar


# 测试函数
def test_custom_menu_bar():
    """测试自定义菜单栏"""
    root = tk.Tk()
    root.title("自定义菜单栏测试")
    root.geometry("800x600")
    
    # 应用主题
    from theme_manager import apply_theme_to_window
    apply_theme_to_window(root)
    
    # 创建菜单栏
    menu_bar = CustomMenuBar(root)
    menu_bar.pack(fill="x", side="top")
    
    # 添加测试菜单
    file_items = [
        {"type": "command", "label": "打开", "command": lambda: print("打开")},
        {"type": "command", "label": "保存", "command": lambda: print("保存")},
        {"type": "separator"},
        {"type": "command", "label": "退出", "command": root.quit}
    ]
    
    edit_items = [
        {"type": "command", "label": "复制", "command": lambda: print("复制")},
        {"type": "command", "label": "粘贴", "command": lambda: print("粘贴")}
    ]
    
    menu_bar.add_menu("文件", file_items)
    menu_bar.add_menu("编辑", edit_items)
    
    # 添加测试内容
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)
    
    label = ttk.Label(frame, text="自定义菜单栏测试\n点击菜单按钮查看效果")
    label.pack(pady=20)
    
    # 主题切换测试
    theme_manager = get_theme_manager()
    
    def switch_theme():
        current = theme_manager.get_theme()
        new_theme = "light" if current == "dark" else "dark"
        theme_manager.set_theme(new_theme)
        apply_theme_to_window(root)
        menu_bar.update_colors()
        print(f"切换到{new_theme}主题")
    
    ttk.Button(frame, text="切换主题", command=switch_theme).pack(pady=10)
    
    root.mainloop()


if __name__ == "__main__":
    test_custom_menu_bar()