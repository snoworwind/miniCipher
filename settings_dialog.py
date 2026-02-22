#!/usr/bin/env python3
"""
设置对话框模块 - 重构版本
为miniCipher工具提供配置管理界面
明确区分基本配置和高级配置，确保所有配置项都有实际实现
"""

import tkinter as tk
from tkinter import ttk, filedialog
import logging
from config_manager import get_config_manager, AlgorithmType, KeyType, ThemeType, Language, ConfigStatus
from translations import TranslationKeys, get_translator, _
from theme_manager import get_theme_manager, apply_theme_to_toplevel, CustomMessageBox


class SettingsDialog:
    """设置对话框类 - 重构版本"""
    
    def __init__(self, parent, cipher_gui_instance):
        """
        初始化设置对话框
        
        Args:
            parent: 父窗口
            cipher_gui_instance: CipherGUI实例，用于应用设置变更
        """
        self.parent = parent
        self.cipher_gui = cipher_gui_instance
        self.config_manager = get_config_manager()
        self.translator = get_translator()
        self.theme_manager = get_theme_manager()
        
        # 原始设置值，用于取消时恢复
        self.original_settings = {}
        
        # 跟踪设置是否已应用
        self.settings_applied = False
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(_(TranslationKeys.SETTINGS_MENU))
        self.dialog.geometry("700x550")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 应用主题
        apply_theme_to_toplevel(self.dialog)
        
        # 阻止用户直接关闭对话框
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # 创建UI
        self._setup_ui()
        
        # 加载当前设置
        self._load_settings()
        
        # 居中对话框
        self._center_dialog()
        
        # 记录日志
        logging.info("设置对话框已打开")
    
    def _setup_ui(self):
        """设置UI布局"""
        # 创建主容器
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建各个设置选项卡
        self._create_general_tab()
        self._create_encryption_tab()
        self._create_paths_tab()
        self._create_advanced_tab()
        
        # 创建按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # 应用按钮
        self.apply_button = ttk.Button(
            button_frame,
            text=_(TranslationKeys.APPLY),
            command=self._on_apply,
            style="Primary.TButton",
            state="disabled"
        )
        self.apply_button.pack(side="right", padx=5)
        
        # 取消按钮
        self.cancel_button = ttk.Button(
            button_frame,
            text=_(TranslationKeys.CANCEL),
            command=self._on_cancel
        )
        self.cancel_button.pack(side="right", padx=5)
        
        # 确定按钮
        self.ok_button = ttk.Button(
            button_frame,
            text=_(TranslationKeys.OK),
            command=self._on_ok,
            style="Success.TButton"
        )
        self.ok_button.pack(side="right", padx=5)
        
        # 重置按钮
        self.reset_button = ttk.Button(
            button_frame,
            text=_(TranslationKeys.RESET),
            command=self._on_reset
        )
        self.reset_button.pack(side="left", padx=5)
    
    def _create_general_tab(self):
        """创建常规设置选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=_("常规"))
        
        # 创建滚动区域
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 语言设置
        lang_frame = ttk.LabelFrame(scrollable_frame, text=_("语言设置"), padding=10)
        lang_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(lang_frame, text=_("界面语言：")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.language_var = tk.StringVar()
        self.language_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=["简体中文", "English"],
            state="readonly",
            width=15
        )
        self.language_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.language_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)
        
        # 主题设置
        theme_frame = ttk.LabelFrame(scrollable_frame, text=_("主题设置"), padding=10)
        theme_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(theme_frame, text=_("界面主题：")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.theme_var = tk.StringVar()
        self.theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=[_(TranslationKeys.LIGHT_THEME), _(TranslationKeys.DARK_THEME)],
            state="readonly",
            width=15
        )
        self.theme_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)
        
        # 预览区域
        preview_frame = ttk.Frame(theme_frame)
        preview_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        ttk.Label(preview_frame, text=_("主题预览：")).pack(side="left")
        self.preview_label = tk.Label(preview_frame, text="AaBbCc123", font=("Segoe UI", 12, "bold"))
        self.preview_label.pack(side="left", padx=10)
        
        # 窗口设置
        window_frame = ttk.LabelFrame(scrollable_frame, text=_("窗口设置"), padding=10)
        window_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(window_frame, text=_("默认算法：")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.default_algorithm_var = tk.StringVar()
        self.default_algorithm_combo = ttk.Combobox(
            window_frame,
            textvariable=self.default_algorithm_var,
            values=["OTP", "AES256"],
            state="readonly",
            width=10
        )
        self.default_algorithm_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.default_algorithm_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)
        
        ttk.Label(window_frame, text=_("默认密钥类型：")).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.default_key_type_var = tk.StringVar()
        self.default_key_type_combo = ttk.Combobox(
            window_frame,
            textvariable=self.default_key_type_var,
            values=["random", "password"],
            state="readonly",
            width=10
        )
        self.default_key_type_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.default_key_type_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)
    
    def _create_encryption_tab(self):
        """创建加密设置选项卡 - 仅包含实际实现的配置"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=_("加密"))
        
        # 创建滚动区域
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 密码设置
        password_frame = ttk.LabelFrame(scrollable_frame, text=_("密码设置"), padding=10)
        password_frame.pack(fill="x", padx=5, pady=5)
        
        # 密码最小长度
        ttk.Label(password_frame, text=_("密码最小长度：")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.password_min_length_var = tk.IntVar()
        self.password_min_length_spinbox = ttk.Spinbox(
            password_frame,
            textvariable=self.password_min_length_var,
            from_=4,
            to=32,
            width=8
        )
        self.password_min_length_spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.password_min_length_spinbox.bind("<KeyRelease>", self._on_setting_changed)
        self.password_min_length_spinbox.bind("<ButtonRelease>", self._on_setting_changed)
        
        # 密码强度要求
        self.require_strong_password_var = tk.BooleanVar()
        self.require_strong_password_check = ttk.Checkbutton(
            password_frame,
            text=_("要求强密码（大小写字母+数字）"),
            variable=self.require_strong_password_var,
            command=self._on_setting_changed
        )
        self.require_strong_password_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # OTP设置（开发中功能）
        otp_frame = ttk.LabelFrame(scrollable_frame, text=_("OTP设置") + " (开发中)", padding=10)
        otp_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(otp_frame, text=_("OTP密钥文件格式：")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.otp_key_format_var = tk.StringVar(value="hex")
        ttk.Radiobutton(
            otp_frame,
            text=_("十六进制 (.txt)"),
            variable=self.otp_key_format_var,
            value="hex",
            command=self._on_setting_changed,
            state="disabled"  # 暂时禁用，功能开发中
        ).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(
            otp_frame,
            text=_("二进制 (.bin)"),
            variable=self.otp_key_format_var,
            value="binary",
            command=self._on_setting_changed,
            state="disabled"  # 暂时禁用，功能开发中
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # 添加开发中提示
        ttk.Label(otp_frame, 
                 text=_("此功能正在开发中，当前固定使用十六进制格式"),
                 font=("Segoe UI", 9, "italic"),
                 foreground="gray").grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # 已弃用配置的提示
        deprecated_frame = ttk.LabelFrame(scrollable_frame, text=_("已弃用功能"), padding=10)
        deprecated_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(deprecated_frame,
                 text=_("以下配置已从当前版本中移除："),
                 font=("Segoe UI", 9, "italic"),
                 foreground="orange").pack(anchor="w", padx=5, pady=2)
        
        ttk.Label(deprecated_frame,
                 text="• " + _("自动生成IV（AES算法总是自动生成IV）"),
                 foreground="gray").pack(anchor="w", padx=15, pady=1)
        
        ttk.Label(deprecated_frame,
                 text="• " + _("加密前压缩文件（功能未实现）"),
                 foreground="gray").pack(anchor="w", padx=15, pady=1)
    
    def _create_paths_tab(self):
        """创建设置选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=_("路径"))
        
        # 创建滚动区域
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 默认路径设置
        paths_frame = ttk.LabelFrame(scrollable_frame, text=_("默认路径"), padding=10)
        paths_frame.pack(fill="x", padx=5, pady=5)
        
        # 默认输入目录
        ttk.Label(paths_frame, text=_("默认输入目录：")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.default_input_dir_var = tk.StringVar()
        self.default_input_dir_entry = ttk.Entry(paths_frame, textvariable=self.default_input_dir_var, width=40)
        self.default_input_dir_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.default_input_dir_entry.bind("<KeyRelease>", self._on_setting_changed)
        
        ttk.Button(
            paths_frame,
            text=_(TranslationKeys.BROWSE),
            command=lambda: self._browse_directory(self.default_input_dir_var)
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # 默认输出目录
        ttk.Label(paths_frame, text=_("默认输出目录：")).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.default_output_dir_var = tk.StringVar()
        self.default_output_dir_entry = ttk.Entry(paths_frame, textvariable=self.default_output_dir_var, width=40)
        self.default_output_dir_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.default_output_dir_entry.bind("<KeyRelease>", self._on_setting_changed)
        
        ttk.Button(
            paths_frame,
            text=_(TranslationKeys.BROWSE),
            command=lambda: self._browse_directory(self.default_output_dir_var)
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # 记住上次使用的文件夹
        self.remember_last_folder_var = tk.BooleanVar()
        self.remember_last_folder_check = ttk.Checkbutton(
            paths_frame,
            text=_("记住上次使用的文件夹"),
            variable=self.remember_last_folder_var,
            command=self._on_setting_changed
        )
        self.remember_last_folder_check.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        # 清空历史记录
        ttk.Button(
            paths_frame,
            text=_("清空历史记录"),
            command=self._clear_history,
            style="Primary.TButton"
        ).grid(row=3, column=0, columnspan=3, pady=10)
        
        # 配置网格权重
        paths_frame.grid_columnconfigure(1, weight=1)
    
    def _create_advanced_tab(self):
        """创建高级设置选项卡 - 仅包含实际实现的配置"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=_("高级"))
        
        # 创建滚动区域
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 调试设置
        debug_frame = ttk.LabelFrame(scrollable_frame, text=_("调试设置"), padding=10)
        debug_frame.pack(fill="x", padx=5, pady=5)
        
        self.debug_mode_var = tk.BooleanVar()
        self.debug_mode_check = ttk.Checkbutton(
            debug_frame,
            text=_("启用调试模式"),
            variable=self.debug_mode_var,
            command=self._on_setting_changed
        )
        self.debug_mode_check.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        ttk.Label(debug_frame, text=_("日志级别：")).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(
            debug_frame,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly",
            width=10
        )
        log_level_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        log_level_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)
        
        # 性能设置
        performance_frame = ttk.LabelFrame(scrollable_frame, text=_("性能设置"), padding=10)
        performance_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(performance_frame, text=_("缓冲区大小 (MB)：")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.buffer_size_var = tk.IntVar(value=10)
        buffer_size_spinbox = ttk.Spinbox(
            performance_frame,
            textvariable=self.buffer_size_var,
            from_=1,
            to=100,
            width=8
        )
        buffer_size_spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        buffer_size_spinbox.bind("<KeyRelease>", self._on_setting_changed)
        buffer_size_spinbox.bind("<ButtonRelease>", self._on_setting_changed)
        
        # 已弃用配置的提示
        deprecated_frame = ttk.LabelFrame(scrollable_frame, text=_("已弃用功能"), padding=10)
        deprecated_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(deprecated_frame,
                 text=_("以下配置已从当前版本中移除："),
                 font=("Segoe UI", 9, "italic"),
                 foreground="orange").pack(anchor="w", padx=5, pady=2)
        
        ttk.Label(deprecated_frame,
                 text="• " + _("自动检查更新（功能未实现）"),
                 foreground="gray").pack(anchor="w", padx=15, pady=1)
        
        ttk.Label(deprecated_frame,
                 text="• " + _("并行处理（功能未实现）"),
                 foreground="gray").pack(anchor="w", padx=15, pady=1)
        
        # 功能说明
        info_frame = ttk.LabelFrame(scrollable_frame, text=_("功能说明"), padding=10)
        info_frame.pack(fill="x", padx=5, pady=5)
        
        info_text = _("""当前版本的高级设置仅包含已实现的功能：
• 调试模式：控制控制台输出详细程度
• 日志级别：控制日志信息的详细程度
• 缓冲区大小：控制文件分块处理的大小

其他高级功能将在未来版本中添加。""")
        
        ttk.Label(info_frame,
                 text=info_text,
                 justify="left",
                 wraplength=600).pack(anchor="w", padx=5, pady=5)
    
    def _browse_directory(self, variable):
        """浏览目录"""
        directory_path = tk.filedialog.askdirectory(initialdir=variable.get())
        if directory_path:
            variable.set(directory_path)
            self._on_setting_changed()
    
    def _load_settings(self):
        """加载当前设置"""
        # 保存原始设置（使用新的配置路径）
        self.original_settings = {
            "basic.ui.language": self.config_manager.get("basic.ui.language"),
            "basic.ui.theme": self.config_manager.get("basic.ui.theme"),
            "basic.encryption.default_algorithm": self.config_manager.get("basic.encryption.default_algorithm"),
            "basic.encryption.default_key_type": self.config_manager.get("basic.encryption.default_key_type"),
            "basic.encryption.password_min_length": self.config_manager.get("basic.encryption.password_min_length"),
            "basic.encryption.require_strong_password": self.config_manager.get("basic.encryption.require_strong_password"),
            "basic.encryption.otp_key_format": self.config_manager.get("basic.encryption.otp_key_format", "hex"),
            "basic.paths.default_input_dir": self.config_manager.get("basic.paths.default_input_dir"),
            "basic.paths.default_output_dir": self.config_manager.get("basic.paths.default_output_dir"),
            "basic.paths.remember_last_folder": self.config_manager.get("basic.paths.remember_last_folder"),
            "basic.paths.last_input_folder": self.config_manager.get("basic.paths.last_input_folder"),
            "basic.paths.last_output_folder": self.config_manager.get("basic.paths.last_output_folder"),
            "advanced.debug_mode": self.config_manager.get("advanced.debug_mode", False),
            "advanced.log_level": self.config_manager.get("advanced.log_level", "INFO"),
            "advanced.buffer_size": self.config_manager.get("advanced.buffer_size", 10),
        }
        
        # 设置语言
        language = self.config_manager.get_language()
        if language == Language.ZH_CN.value:
            self.language_var.set("简体中文")
        else:
            self.language_var.set("English")
        
        # 设置主题
        theme = self.config_manager.get_theme()
        if theme == ThemeType.LIGHT.value:
            self.theme_var.set(_(TranslationKeys.LIGHT_THEME))
        else:
            self.theme_var.set(_(TranslationKeys.DARK_THEME))
        
        # 更新主题预览
        self._update_theme_preview()
        
        # 设置加密选项
        self.default_algorithm_var.set(self.config_manager.get_default_algorithm())
        self.default_key_type_var.set(self.config_manager.get_default_key_type())
        self.password_min_length_var.set(self.config_manager.get_password_min_length())
        self.require_strong_password_var.set(self.config_manager.requires_strong_password())
        self.otp_key_format_var.set(self.config_manager.get("basic.encryption.otp_key_format", "hex"))
        
        # 设置路径选项
        self.default_input_dir_var.set(self.config_manager.get_default_input_dir())
        self.default_output_dir_var.set(self.config_manager.get_default_output_dir())
        self.remember_last_folder_var.set(self.config_manager.should_remember_last_folder())
        
        # 设置高级选项
        self.debug_mode_var.set(self.config_manager.get("advanced.debug_mode", False))
        self.log_level_var.set(self.config_manager.get("advanced.log_level", "INFO"))
        self.buffer_size_var.set(self.config_manager.get("advanced.buffer_size", 10))
        
        # 记录日志
        logging.debug("设置对话框已加载当前配置")
    
    def _update_theme_preview(self):
        """更新主题预览"""
        theme = self.theme_var.get()
        # 使用主题管理器的颜色
        colors = self.theme_manager.get_colors()
        if theme == _(TranslationKeys.DARK_THEME):
            # 深色主题预览
            self.preview_label.configure(
                foreground=colors["text_primary"],
                background=colors["entry_bg"]
            )
        else:
            # 浅色主题预览
            self.preview_label.configure(
                foreground=colors["text_primary"],
                background=colors["entry_bg"]
            )
    
    def _apply_theme(self):
        """应用主题到设置对话框 - 与主界面相同的逻辑"""
        try:
            # 获取当前选择的主题
            theme_text = self.theme_var.get()
            if theme_text == _(TranslationKeys.DARK_THEME):
                theme = "dark"
            else:
                theme = "light"
            
            # 设置主题管理器
            self.theme_manager.set_theme(theme)
            
            # 获取当前主题颜色
            colors = self.theme_manager.get_colors()
            
            # 安全地设置对话框背景
            try:
                self.dialog.configure(bg=colors["window_bg"])
            except tk.TclError:
                # 如果Toplevel不支持bg选项，忽略错误
                pass
            
            # 重新创建ttk样式
            style = ttk.Style(self.dialog)
            self.theme_manager.create_style(style)
            
            # 应用主题到所有现有组件
            self.theme_manager.apply_to_all_widgets(self.dialog)
            
            # 更新主题预览
            self._update_theme_preview()
            
            # 记录主题变更
            logging.debug(f"设置对话框主题已切换到: {theme}")
            
        except Exception as e:
            logging.error(f"设置对话框应用主题失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_setting_changed(self, event=None):
        """设置变更事件"""
        self.apply_button.config(state="normal")
    
    def _on_apply(self):
        """应用设置"""
        try:
            # 保存语言设置
            language_text = self.language_var.get()
            if language_text == "简体中文":
                self.config_manager.set_language(Language.ZH_CN.value)
            else:
                self.config_manager.set_language(Language.EN_US.value)
            
            # 保存主题设置
            theme_text = self.theme_var.get()
            if theme_text == _(TranslationKeys.DARK_THEME):
                self.config_manager.set_theme(ThemeType.DARK.value)
            else:
                self.config_manager.set_theme(ThemeType.LIGHT.value)
            
            # 保存加密设置
            self.config_manager.set("basic.encryption.default_algorithm", self.default_algorithm_var.get())
            self.config_manager.set("basic.encryption.default_key_type", self.default_key_type_var.get())
            self.config_manager.set("basic.encryption.password_min_length", self.password_min_length_var.get())
            self.config_manager.set("basic.encryption.require_strong_password", self.require_strong_password_var.get())
            self.config_manager.set("basic.encryption.otp_key_format", self.otp_key_format_var.get())
            
            # 保存路径设置
            self.config_manager.set("basic.paths.default_input_dir", self.default_input_dir_var.get())
            self.config_manager.set("basic.paths.default_output_dir", self.default_output_dir_var.get())
            self.config_manager.set("basic.paths.remember_last_folder", self.remember_last_folder_var.get())
            
            # 保存高级设置
            self.config_manager.set("advanced.debug_mode", self.debug_mode_var.get())
            self.config_manager.set("advanced.log_level", self.log_level_var.get())
            self.config_manager.set("advanced.buffer_size", self.buffer_size_var.get())
            
            # 应用主题变更到主界面
            if self.cipher_gui:
                self.cipher_gui._change_theme(self.config_manager.get_theme())
            
            # 应用主题变更到设置对话框自身
            self._apply_theme()
            
            # 标记设置已应用
            self.settings_applied = True
            
            # 禁用应用按钮
            self.apply_button.config(state="disabled")
            
            # 记录日志
            logging.info("设置已成功应用")
            
            # 显示成功消息
            message_box = CustomMessageBox(self.dialog)
            message_box.show_success(_("成功"), _("设置已成功应用"))
            
        except Exception as e:
            # 记录错误日志
            logging.error(f"应用设置时出错: {e}")
            
            # 显示错误消息
            message_box = CustomMessageBox(self.dialog)
            message_box.show_error(_("错误"), _("应用设置时出错: {error}", error=str(e)))
    
    def _on_ok(self):
        """确定按钮事件"""
        self._on_apply()
        self.dialog.destroy()
        logging.info("设置对话框已关闭（确定）")
    
    def _on_cancel(self):
        """取消按钮事件"""
        # 只有当设置未应用时才恢复原始设置
        if not self.settings_applied:
            for key, value in self.original_settings.items():
                self.config_manager.set(key, value)
            
            # 恢复主题
            if self.cipher_gui:
                self.cipher_gui._change_theme(self.original_settings["basic.ui.theme"])
            
            logging.debug("设置已恢复为原始值")
        
        self.dialog.destroy()
        logging.info("设置对话框已关闭（取消）")
    
    def _on_reset(self):
        """重置为默认设置"""
        self.config_manager.reset_to_defaults()
        self._load_settings()
        self.apply_button.config(state="normal")
        
        # 记录日志
        logging.info("设置已重置为默认值")
        
        # 显示消息
        message_box = CustomMessageBox(self.dialog)
        message_box.show_info(_("重置"), _("设置已重置为默认值"))
    
    def _clear_history(self):
        """清空历史记录"""
        self.config_manager.set_last_input_folder("")
        self.config_manager.set_last_output_folder("")
        
        # 记录日志
        logging.info("历史记录已清空")
        
        # 显示消息
        message_box = CustomMessageBox(self.dialog)
        message_box.show_info(_("清空"), _("历史记录已清空"))
    
    def _center_dialog(self):
        """居中对话框"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        
        x = self.parent.winfo_x() + (self.parent.winfo_width() - width) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - height) // 2
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def run(self):
        """运行对话框（模态）"""
        self.dialog.wait_window()


# 测试函数
def test_settings_dialog():
    """测试设置对话框"""
    import sys
    
    # 创建测试窗口
    root = tk.Tk()
    root.title("测试设置对话框")
    root.geometry("800x600")
    
    # 应用主题
    from theme_manager import apply_theme_to_window
    apply_theme_to_window(root)
    
    # 创建测试按钮
    def open_settings():
        # 创建一个模拟的CipherGUI实例
        class MockCipherGUI:
            def __init__(self):
                self.config_manager = get_config_manager()
                self.translator = get_translator()
                self.theme_manager = get_theme_manager()
            
            def _change_theme(self, theme):
                print(f"更改主题: {theme}")
        
        mock_gui = MockCipherGUI()
        dialog = SettingsDialog(root, mock_gui)
        dialog.run()
    
    ttk.Button(root, text="打开设置", command=open_settings).pack(pady=20)
    
    # 运行主循环
    root.mainloop()


if __name__ == "__main__":
    test_settings_dialog()