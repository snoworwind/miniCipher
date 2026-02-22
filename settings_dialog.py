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
from config_validator import ValidationError, get_validation_manager
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
        self.notebook.add(tab, text=_(TranslationKeys.TAB_GENERAL))
        
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
        lang_frame = ttk.LabelFrame(scrollable_frame, text=_(TranslationKeys.SETTINGS_LANGUAGE), padding=10)
        lang_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(lang_frame, text=_(TranslationKeys.UI_LANGUAGE)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.language_var = tk.StringVar()
        self.language_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=[_(TranslationKeys.CHINESE_LANGUAGE), _(TranslationKeys.ENGLISH_LANGUAGE)],
            state="readonly",
            width=15
        )
        self.language_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.language_combo.bind("<<ComboboxSelected>>", self._on_setting_changed)
        
        # 主题设置
        theme_frame = ttk.LabelFrame(scrollable_frame, text=_(TranslationKeys.THEME_SETTINGS), padding=10)
        theme_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(theme_frame, text=_(TranslationKeys.UI_THEME)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
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
        ttk.Label(preview_frame, text=_(TranslationKeys.SETTINGS_THEME_PREVIEW)).pack(side="left")
        self.preview_label = tk.Label(preview_frame, text="AaBbCc123", font=("Segoe UI", 12, "bold"))
        self.preview_label.pack(side="left", padx=10)
        
        # 窗口设置
        window_frame = ttk.LabelFrame(scrollable_frame, text=_(TranslationKeys.SETTINGS_WINDOW), padding=10)
        window_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(window_frame, text=_(TranslationKeys.DEFAULT_ALGORITHM_LABEL)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
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
        
        ttk.Label(window_frame, text=_(TranslationKeys.DEFAULT_KEY_TYPE_LABEL)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
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
        self.notebook.add(tab, text=_(TranslationKeys.TAB_ENCRYPTION))
        
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
        password_frame = ttk.LabelFrame(scrollable_frame, text=_(TranslationKeys.SETTINGS_PASSWORD), padding=10)
        password_frame.pack(fill="x", padx=5, pady=5)
        
        # 密码最小长度
        ttk.Label(password_frame, text=_(TranslationKeys.SETTINGS_PASSWORD_MIN_LENGTH)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
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
            text=_(TranslationKeys.SETTINGS_REQUIRE_STRONG_PASSWORD),
            variable=self.require_strong_password_var,
            command=self._on_setting_changed
        )
        self.require_strong_password_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # OTP设置
        otp_frame = ttk.LabelFrame(scrollable_frame, text=_(TranslationKeys.SETTINGS_OTP), padding=10)
        otp_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(otp_frame, text=_(TranslationKeys.SETTINGS_OTP_KEY_FORMAT)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.otp_key_format_var = tk.StringVar(value="hex")
        ttk.Radiobutton(
            otp_frame,
            text=_(TranslationKeys.SETTINGS_OTP_HEX),
            variable=self.otp_key_format_var,
            value="hex",
            command=self._on_setting_changed
        ).grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Radiobutton(
            otp_frame,
            text=_(TranslationKeys.SETTINGS_OTP_BINARY),
            variable=self.otp_key_format_var,
            value="binary",
            command=self._on_setting_changed
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # 功能说明
        ttk.Label(otp_frame, 
                 text=_(TranslationKeys.OTP_FORMAT_INFO),
                 font=("Segoe UI", 9, "italic"),
                 foreground="gray").grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
    
    def _create_paths_tab(self):
        """创建设置选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=_(TranslationKeys.TAB_PATHS))
        
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
        paths_frame = ttk.LabelFrame(scrollable_frame, text=_(TranslationKeys.SETTINGS_DEFAULT_PATHS), padding=10)
        paths_frame.pack(fill="x", padx=5, pady=5)
        
        # 默认输入目录
        ttk.Label(paths_frame, text=_(TranslationKeys.DEFAULT_INPUT_DIRECTORY)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
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
        ttk.Label(paths_frame, text=_(TranslationKeys.DEFAULT_OUTPUT_DIRECTORY)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
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
            text=_(TranslationKeys.SETTINGS_REMEMBER_LAST_FOLDER),
            variable=self.remember_last_folder_var,
            command=self._on_setting_changed
        )
        self.remember_last_folder_check.grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        # 清空历史记录
        ttk.Button(
            paths_frame,
            text=_(TranslationKeys.SETTINGS_CLEAR_HISTORY),
            command=self._clear_history,
            style="Primary.TButton"
        ).grid(row=3, column=0, columnspan=3, pady=10)
        
        # 配置网格权重
        paths_frame.grid_columnconfigure(1, weight=1)
    
    def _create_advanced_tab(self):
        """创建高级设置选项卡 - 仅包含实际实现的配置"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=_(TranslationKeys.TAB_ADVANCED))
        
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
        debug_frame = ttk.LabelFrame(scrollable_frame, text=_(TranslationKeys.SETTINGS_DEBUG), padding=10)
        debug_frame.pack(fill="x", padx=5, pady=5)
        
        self.debug_mode_var = tk.BooleanVar()
        self.debug_mode_check = ttk.Checkbutton(
            debug_frame,
            text=_(TranslationKeys.SETTINGS_DEBUG_MODE),
            variable=self.debug_mode_var,
            command=self._on_setting_changed
        )
        self.debug_mode_check.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        ttk.Label(debug_frame, text=_(TranslationKeys.LOG_LEVEL_LABEL)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
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
        performance_frame = ttk.LabelFrame(scrollable_frame, text=_(TranslationKeys.SETTINGS_PERFORMANCE), padding=10)
        performance_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(performance_frame, text=_(TranslationKeys.BUFFER_SIZE_LABEL)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
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
        
        
        # 功能说明
        info_frame = ttk.LabelFrame(scrollable_frame, text=_(TranslationKeys.FEATURE_DESCRIPTION), padding=10)
        info_frame.pack(fill="x", padx=5, pady=5)
        
        info_text = _(TranslationKeys.ADVANCED_SETTINGS_INFO)
        
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
            self.language_var.set(_(TranslationKeys.CHINESE_LANGUAGE))
        else:
            self.language_var.set(_(TranslationKeys.ENGLISH_LANGUAGE))
        
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
            # 检查对话框是否仍然存在
            if not hasattr(self.dialog, 'winfo_exists') or not self.dialog.winfo_exists():
                logging.debug("设置对话框已销毁，跳过主题应用")
                return
                
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
            
            # 安全地应用主题到所有现有组件
            try:
                self.theme_manager.apply_to_all_widgets(self.dialog)
            except tk.TclError as e:
                # 如果对话框部件已销毁，记录并继续
                logging.debug(f"主题应用时遇到Tcl错误（可能部件已销毁）: {e}")
            
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
        """应用设置 - 改进版：检测UI相关变更并提示重启"""
        try:
            # 首先验证所有设置值
            self._validate_settings()
            
            # 检测UI相关设置是否变更
            ui_changed = False
            language_changed = False
            theme_changed = False
            
            # 检查语言是否变更
            language_text = self.language_var.get()
            if language_text == _(TranslationKeys.CHINESE_LANGUAGE):
                new_language_value = Language.ZH_CN.value
            else:
                new_language_value = Language.EN_US.value
            
            current_language_value = self.config_manager.get_language()
            if new_language_value != current_language_value:
                language_changed = True
                ui_changed = True
            
            # 检查主题是否变更
            theme_text = self.theme_var.get()
            if theme_text == _(TranslationKeys.DARK_THEME):
                new_theme_value = ThemeType.DARK.value
            else:
                new_theme_value = ThemeType.LIGHT.value
            
            current_theme_value = self.config_manager.get_theme()
            if new_theme_value != current_theme_value:
                theme_changed = True
                ui_changed = True
            
            # 保存所有设置（包括UI相关设置）
            # 保存语言设置
            self.config_manager.set_language(new_language_value)
            
            # 保存主题设置
            self.config_manager.set_theme(new_theme_value)
            
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
            
            # 标记设置已应用
            self.settings_applied = True
            
            # 安全地禁用应用按钮（检查按钮是否存在）
            if hasattr(self.apply_button, 'winfo_exists') and self.apply_button.winfo_exists():
                try:
                    self.apply_button.config(state="disabled")
                except tk.TclError:
                    # 如果按钮已销毁，忽略错误
                    pass
            
            # 记录日志
            logging.info("设置已成功应用")
            
            # 根据UI变更情况采取不同操作
            if ui_changed:
                # UI相关设置已变更，显示重启提示
                self._show_restart_prompt(language_changed, theme_changed)
            else:
                # 非UI设置变更，显示标准成功消息
                self._show_standard_success_message()
            
        except ValidationError as e:
            # 验证错误
            logging.error(f"设置验证失败: {e}")
            
            # 安全地显示验证错误消息
            # 首先尝试使用对话框作为父窗口，如果已销毁则使用主窗口
            parent_window = None
            if hasattr(self.dialog, 'winfo_exists') and self.dialog.winfo_exists():
                parent_window = self.dialog
            elif hasattr(self.parent, 'winfo_exists') and self.parent.winfo_exists():
                parent_window = self.parent
            
            error_message = _(TranslationKeys.VALIDATION_ERROR_MESSAGE, error=str(e))
            message_box = CustomMessageBox(parent_window)
            message_box.show_error(_(TranslationKeys.VALIDATION_ERROR_TITLE), error_message)
            
        except Exception as e:
            # 记录错误日志
            logging.error(f"应用设置时出错: {e}")
            
            # 安全地显示错误消息
            # 首先尝试使用对话框作为父窗口，如果已销毁则使用主窗口
            parent_window = None
            if hasattr(self.dialog, 'winfo_exists') and self.dialog.winfo_exists():
                parent_window = self.dialog
            elif hasattr(self.parent, 'winfo_exists') and self.parent.winfo_exists():
                parent_window = self.parent
            
            message_box = CustomMessageBox(parent_window)
            message_box.show_error(_(TranslationKeys.ERROR_TITLE), _(TranslationKeys.ERROR_MESSAGE_TEMPLATE, error=str(e)))
            
        except ValidationError as e:
            # 验证错误
            logging.error(f"设置验证失败: {e}")
            
            # 安全地显示验证错误消息
            # 首先尝试使用对话框作为父窗口，如果已销毁则使用主窗口
            parent_window = None
            if hasattr(self.dialog, 'winfo_exists') and self.dialog.winfo_exists():
                parent_window = self.dialog
            elif hasattr(self.parent, 'winfo_exists') and self.parent.winfo_exists():
                parent_window = self.parent
            
            error_message = _(TranslationKeys.VALIDATION_ERROR_MESSAGE, error=str(e))
            message_box = CustomMessageBox(parent_window)
            message_box.show_error(_(TranslationKeys.VALIDATION_ERROR_TITLE), error_message)
            
        except Exception as e:
            # 记录错误日志
            logging.error(f"应用设置时出错: {e}")
            
            # 安全地显示错误消息
            # 首先尝试使用对话框作为父窗口，如果已销毁则使用主窗口
            parent_window = None
            if hasattr(self.dialog, 'winfo_exists') and self.dialog.winfo_exists():
                parent_window = self.dialog
            elif hasattr(self.parent, 'winfo_exists') and self.parent.winfo_exists():
                parent_window = self.parent
            
            message_box = CustomMessageBox(parent_window)
            message_box.show_error(_(TranslationKeys.ERROR_TITLE), _(TranslationKeys.ERROR_MESSAGE_TEMPLATE, error=str(e)))
    
    def _on_ok(self):
        """确定按钮事件 - 改进版：正确处理重启提示"""
        # 保存当前UI变更状态
        ui_changed = False
        language_changed = False
        theme_changed = False
        
        # 检查语言是否变更
        language_text = self.language_var.get()
        if language_text == _(TranslationKeys.CHINESE_LANGUAGE):
            new_language_value = Language.ZH_CN.value
        else:
            new_language_value = Language.EN_US.value
        
        current_language_value = self.config_manager.get_language()
        if new_language_value != current_language_value:
            language_changed = True
            ui_changed = True
        
        # 检查主题是否变更
        theme_text = self.theme_var.get()
        if theme_text == _(TranslationKeys.DARK_THEME):
            new_theme_value = ThemeType.DARK.value
        else:
            new_theme_value = ThemeType.LIGHT.value
        
        current_theme_value = self.config_manager.get_theme()
        if new_theme_value != current_theme_value:
            theme_changed = True
            ui_changed = True
        
        # 应用设置
        self._on_apply()
        
        # 根据UI变更情况决定是否关闭对话框
        if not ui_changed:
            # 没有UI变更，可以关闭对话框
            self.dialog.destroy()
            logging.info("设置对话框已关闭（确定）- 无UI变更")
        else:
            # 有UI变更，已经显示重启提示，不立即关闭对话框
            # 重启提示对话框会处理后续关闭逻辑
            logging.info("设置对话框等待重启提示处理")
    
    def _on_cancel(self):
        """取消按钮事件"""
        # 只有当设置未应用时才恢复原始设置
        if not self.settings_applied:
            for key, value in self.original_settings.items():
                self.config_manager.set(key, value)
            
            # 恢复主题
            if self.cipher_gui:
                self.cipher_gui._change_theme(self.original_settings["basic.ui.theme"])
            
            # 恢复语言
            if self.cipher_gui and "basic.ui.language" in self.original_settings:
                language_value = self.original_settings["basic.ui.language"]
                self.cipher_gui._change_language(language_value)
            
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
        message_box.show_info(_(TranslationKeys.RESET_TITLE), _(TranslationKeys.RESET_MESSAGE))
    
    def _clear_history(self):
        """清空历史记录"""
        self.config_manager.set_last_input_folder("")
        self.config_manager.set_last_output_folder("")
        
        # 记录日志
        logging.info("历史记录已清空")
        
        # 显示消息
        message_box = CustomMessageBox(self.dialog)
        message_box.show_info(_(TranslationKeys.CLEAR_TITLE), _(TranslationKeys.CLEAR_MESSAGE))
    
    def _update_dialog_language(self):
        """立即更新设置对话框的界面语言 - 安全版本"""
        try:
            # 首先检查对话框是否仍然存在
            if not hasattr(self.dialog, 'winfo_exists') or not self.dialog.winfo_exists():
                logging.debug("设置对话框已销毁，跳过语言更新")
                return
            
            # 更新对话框标题
            try:
                self.dialog.title(_(TranslationKeys.SETTINGS_MENU))
            except tk.TclError:
                logging.debug("无法更新对话框标题（可能已销毁）")
                return
            
            # 检查notebook是否存在
            if not hasattr(self.notebook, 'winfo_exists') or not self.notebook.winfo_exists():
                logging.debug("Notebook已销毁，跳过选项卡更新")
            else:
                # 更新选项卡标签
                try:
                    tab_count = self.notebook.index("end")
                    for i, tab_text in enumerate([
                        _(TranslationKeys.TAB_GENERAL),
                        _(TranslationKeys.TAB_ENCRYPTION),
                        _(TranslationKeys.TAB_PATHS),
                        _(TranslationKeys.TAB_ADVANCED)
                    ]):
                        if i < tab_count:
                            self.notebook.tab(i, text=tab_text)
                except tk.TclError:
                    logging.debug("更新选项卡标签失败（部件可能已销毁）")
            
            # 更新所有标签框架和标签文本 - 使用安全版本
            self._safe_update_widget_text_recursive(self.dialog)
            
            # 更新语言选择框的值（使用翻译后的文本）
            current_language = self.config_manager.get_language()
            try:
                if current_language == Language.ZH_CN.value:
                    self.language_var.set(_(TranslationKeys.CHINESE_LANGUAGE))
                else:
                    self.language_var.set(_(TranslationKeys.ENGLISH_LANGUAGE))
            except tk.TclError:
                logging.debug("更新语言选择框失败")
            
            # 更新主题选择框的值
            current_theme = self.config_manager.get_theme()
            try:
                if current_theme == ThemeType.DARK.value:
                    self.theme_var.set(_(TranslationKeys.DARK_THEME))
                else:
                    self.theme_var.set(_(TranslationKeys.LIGHT_THEME))
            except tk.TclError:
                logging.debug("更新主题选择框失败")
            
            # 更新按钮文本 - 检查每个按钮是否存在
            try:
                if hasattr(self.apply_button, 'winfo_exists') and self.apply_button.winfo_exists():
                    self.apply_button.config(text=_(TranslationKeys.APPLY))
            except tk.TclError:
                logging.debug("更新应用按钮失败")
            
            try:
                if hasattr(self.cancel_button, 'winfo_exists') and self.cancel_button.winfo_exists():
                    self.cancel_button.config(text=_(TranslationKeys.CANCEL))
            except tk.TclError:
                logging.debug("更新取消按钮失败")
            
            try:
                if hasattr(self.ok_button, 'winfo_exists') and self.ok_button.winfo_exists():
                    self.ok_button.config(text=_(TranslationKeys.OK))
            except tk.TclError:
                logging.debug("更新确定按钮失败")
            
            try:
                if hasattr(self.reset_button, 'winfo_exists') and self.reset_button.winfo_exists():
                    self.reset_button.config(text=_(TranslationKeys.RESET))
            except tk.TclError:
                logging.debug("更新重置按钮失败")
            
            # 强制重新绘制对话框（安全地）
            try:
                self.dialog.update()
            except tk.TclError:
                logging.debug("更新对话框失败（可能已销毁）")
            
            logging.debug("设置对话框界面语言已安全更新")
            
        except Exception as e:
            logging.error(f"更新设置对话框语言时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_widget_text_recursive(self, widget):
        """递归更新widget及其子widget的文本"""
        try:
            # 获取当前widget类型并尝试更新文本
            if isinstance(widget, ttk.LabelFrame):
                # 获取当前文本配置，如果是翻译键则更新
                current_text = widget.cget('text')
                if current_text:
                    # 尝试查找对应的翻译键（简化逻辑，实际可能需要映射）
                    # 这里只处理我们知道的需要翻译的标签框架
                    pass
            
            elif isinstance(widget, ttk.Label):
                # 对于标签，如果它是通过翻译键设置的，需要更新
                # 实际实现可能需要更复杂的逻辑来确定哪些标签需要更新
                pass
            
            # 递归处理子widget
            for child in widget.winfo_children():
                self._update_widget_text_recursive(child)
                
        except (tk.TclError, AttributeError):
            # 如果widget已销毁或没有相关属性，忽略错误
            pass
    
    def _safe_update_widget_text_recursive(self, widget):
        """安全递归更新widget及其子widget的文本 - 检查部件是否存在"""
        try:
            # 检查部件是否存在
            if not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
                return
            
            # 递归处理子widget
            try:
                children = widget.winfo_children()
                for child in children:
                    self._safe_update_widget_text_recursive(child)
            except tk.TclError:
                # 如果获取子部件失败，忽略错误
                pass
                
        except (tk.TclError, AttributeError):
            # 如果widget已销毁或没有相关属性，忽略错误
            pass
    
    def _center_dialog(self):
        """居中对话框"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        
        x = self.parent.winfo_x() + (self.parent.winfo_width() - width) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - height) // 2
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _validate_settings(self):
        """验证所有设置值"""
        # 获取验证管理器
        validation_manager = get_validation_manager()
        
        # 验证密码最小长度
        password_min_length = self.password_min_length_var.get()
        is_valid, error_msg = validation_manager.validate_key("basic.encryption.password_min_length", password_min_length)
        if not is_valid:
            raise ValidationError("basic.encryption.password_min_length", password_min_length, error_msg)
        
        # 验证缓冲区大小
        buffer_size = self.buffer_size_var.get()
        is_valid, error_msg = validation_manager.validate_key("advanced.buffer_size", buffer_size)
        if not is_valid:
            raise ValidationError("advanced.buffer_size", buffer_size, error_msg)
        
        # 验证语言
        language_text = self.language_var.get()
        language_value = Language.ZH_CN.value if language_text == _(TranslationKeys.CHINESE_LANGUAGE) else Language.EN_US.value
        is_valid, error_msg = validation_manager.validate_key("basic.ui.language", language_value)
        if not is_valid:
            raise ValidationError("basic.ui.language", language_value, error_msg)
        
        # 验证主题
        theme_text = self.theme_var.get()
        theme_value = ThemeType.DARK.value if theme_text == _(TranslationKeys.DARK_THEME) else ThemeType.LIGHT.value
        is_valid, error_msg = validation_manager.validate_key("basic.ui.theme", theme_value)
        if not is_valid:
            raise ValidationError("basic.ui.theme", theme_value, error_msg)
        
        # 验证默认算法
        algorithm_value = self.default_algorithm_var.get()
        is_valid, error_msg = validation_manager.validate_key("basic.encryption.default_algorithm", algorithm_value)
        if not is_valid:
            raise ValidationError("basic.encryption.default_algorithm", algorithm_value, error_msg)
        
        # 验证默认密钥类型
        key_type_value = self.default_key_type_var.get()
        is_valid, error_msg = validation_manager.validate_key("basic.encryption.default_key_type", key_type_value)
        if not is_valid:
            raise ValidationError("basic.encryption.default_key_type", key_type_value, error_msg)
        
        # 验证OTP密钥格式
        otp_format_value = self.otp_key_format_var.get()
        is_valid, error_msg = validation_manager.validate_key("basic.encryption.otp_key_format", otp_format_value)
        if not is_valid:
            raise ValidationError("basic.encryption.otp_key_format", otp_format_value, error_msg)
        
        # 验证日志级别
        log_level_value = self.log_level_var.get()
        is_valid, error_msg = validation_manager.validate_key("advanced.log_level", log_level_value)
        if not is_valid:
            raise ValidationError("advanced.log_level", log_level_value, error_msg)
        
        # 路径验证（如果非空）
        input_dir = self.default_input_dir_var.get()
        if input_dir:
            is_valid, error_msg = validation_manager.validate_key("basic.paths.default_input_dir", input_dir)
            if not is_valid:
                raise ValidationError("basic.paths.default_input_dir", input_dir, error_msg)
        
        output_dir = self.default_output_dir_var.get()
        if output_dir:
            is_valid, error_msg = validation_manager.validate_key("basic.paths.default_output_dir", output_dir)
            if not is_valid:
                raise ValidationError("basic.paths.default_output_dir", output_dir, error_msg)
    
    def _show_restart_prompt(self, language_changed, theme_changed):
        """显示重启提示对话框 - 改进版：确保按钮正确显示
        
        Args:
            language_changed: 语言是否已变更
            theme_changed: 主题是否已变更
        """
        try:
            # 创建重启提示对话框
            prompt_dialog = tk.Toplevel(self.dialog)
            prompt_dialog.title(_(TranslationKeys.RESTART_REQUIRED_TITLE))
            prompt_dialog.geometry("550x350")
            prompt_dialog.transient(self.dialog)
            prompt_dialog.grab_set()
            
            # 阻止用户直接关闭对话框
            prompt_dialog.protocol("WM_DELETE_WINDOW", prompt_dialog.destroy)
            
            # 应用主题
            from theme_manager import apply_theme_to_toplevel
            apply_theme_to_toplevel(prompt_dialog)
            
            # 创建主容器 - 使用网格布局确保按钮可见
            main_frame = ttk.Frame(prompt_dialog, padding=20)
            main_frame.pack(fill="both", expand=True)
            
            # 配置网格权重
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(2, weight=1)  # 消息文本区域可扩展
            main_frame.rowconfigure(4, weight=0)  # 按钮区域固定
            
            # 创建图标和标题区域
            header_frame = ttk.Frame(main_frame)
            header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
            header_frame.columnconfigure(0, weight=0)  # 图标
            header_frame.columnconfigure(1, weight=1)  # 标题
            
            # 警告图标
            icon_label = tk.Label(header_frame, text="⚠", font=("Segoe UI", 36, "bold"))
            icon_label.grid(row=0, column=0, padx=(0, 15))
            
            # 标题
            title_label = ttk.Label(
                header_frame,
                text=_(TranslationKeys.RESTART_REQUIRED_TITLE),
                font=("Segoe UI", 14, "bold")
            )
            title_label.grid(row=0, column=1, sticky="w")
            
            # 说明文字
            description_frame = ttk.Frame(main_frame)
            description_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
            
            description_text = tk.Text(description_frame, height=3, wrap="word", font=("Segoe UI", 10))
            description_text.pack(fill="x", expand=True)
            
            # 构建说明内容
            description_lines = []
            description_lines.append(_(TranslationKeys.RESTART_REQUIRED_INTRO))
            description_lines.append("")
            
            if language_changed:
                description_lines.append(f"• {_(TranslationKeys.RESTART_LANGUAGE_CHANGED)}")
            
            if theme_changed:
                description_lines.append(f"• {_(TranslationKeys.RESTART_THEME_CHANGED)}")
            
            description_text.insert("1.0", "\n".join(description_lines))
            description_text.configure(state="disabled")
            
            # 详细说明区域
            detail_frame = ttk.LabelFrame(main_frame, text=_("操作说明"), padding=10)
            detail_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
            
            detail_text = tk.Text(detail_frame, height=4, wrap="word", font=("Segoe UI", 9))
            detail_text.pack(fill="both", expand=True)
            
            detail_text.insert("1.0", _(TranslationKeys.RESTART_REQUIRED_INSTRUCTIONS))
            detail_text.configure(state="disabled")
            
            # 按钮框架 - 确保按钮可见并正确布局
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
            
            # 配置按钮框架列权重
            button_frame.columnconfigure(0, weight=1)  # 左对齐空间
            button_frame.columnconfigure(1, weight=0)  # 稍后重启按钮
            button_frame.columnconfigure(2, weight=0)  # 立即重启按钮
            
            # 稍后重启按钮 - 左对齐
            later_button = ttk.Button(
                button_frame,
                text=_(TranslationKeys.RESTART_LATER_BUTTON),
                command=prompt_dialog.destroy,
                width=15
            )
            later_button.grid(row=0, column=1, padx=(0, 10))
            
            # 立即重启按钮 - 右对齐
            restart_button = ttk.Button(
                button_frame,
                text=_(TranslationKeys.RESTART_NOW_BUTTON),
                command=lambda: self._perform_restart(prompt_dialog),
                style="Primary.TButton",
                width=15
            )
            restart_button.grid(row=0, column=2)
            
            # 强制更新布局
            prompt_dialog.update_idletasks()
            
            # 居中对话框
            width = prompt_dialog.winfo_width()
            height = prompt_dialog.winfo_height()
            x = self.dialog.winfo_x() + (self.dialog.winfo_width() - width) // 2
            y = self.dialog.winfo_y() + (self.dialog.winfo_height() - height) // 2
            prompt_dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # 确保对话框获得焦点
            prompt_dialog.focus_force()
            
            # 记录日志
            logging.info(f"显示重启提示对话框，尺寸: {width}x{height}")
            logging.info(f"语言变更: {language_changed}, 主题变更: {theme_changed}")
            
        except Exception as e:
            logging.error(f"显示重启提示对话框时出错: {e}")
            import traceback
            traceback.print_exc()
            # 如果出错，尝试简单的消息框
            try:
                from theme_manager import CustomMessageBox
                message_box = CustomMessageBox(self.dialog)
                message_box.show_warning(
                    _(TranslationKeys.RESTART_REQUIRED_TITLE),
                    _(TranslationKeys.RESTART_REQUIRED_INSTRUCTIONS)
                )
            except Exception as inner_e:
                logging.error(f"回退消息框也失败: {inner_e}")
    
    def _show_standard_success_message(self):
        """显示标准成功消息"""
        try:
            # 安全地显示成功消息（检查对话框是否存在且有效）
            if hasattr(self.dialog, 'winfo_exists') and self.dialog.winfo_exists():
                # 双重检查对话框是否仍然有效
                try:
                    # 尝试获取对话框的ID，如果失败则说明对话框无效
                    self.dialog.winfo_id()
                except tk.TclError:
                    logging.debug("对话框无效，跳过显示消息框")
                    return
                
                # 显示消息框，但不等待它关闭（避免对话框阻塞）
                def show_message_box():
                    try:
                        if hasattr(self.dialog, 'winfo_exists') and self.dialog.winfo_exists():
                            message_box = CustomMessageBox(self.dialog)
                            message_box.show_success(_(TranslationKeys.SETTINGS_SUCCESS_TITLE), _(TranslationKeys.SETTINGS_SUCCESS_MESSAGE))
                    except Exception as e:
                        logging.error(f"显示成功消息框时出错: {e}")
                
                # 使用after延迟显示消息框，确保对话框已经完成当前更新
                if hasattr(self.dialog, 'after'):
                    self.dialog.after(100, show_message_box)
                else:
                    # 如果没有after方法，直接显示
                    show_message_box()
                    
        except Exception as e:
            logging.error(f"准备显示消息框时出错: {e}")
    
    def _perform_restart(self, prompt_dialog):
        """执行UI重启
        
        Args:
            prompt_dialog: 重启提示对话框
        """
        try:
            # 关闭重启提示对话框
            prompt_dialog.destroy()
            
            # 关闭设置对话框
            self.dialog.destroy()
            
            # 通知主界面重启UI
            if self.cipher_gui and hasattr(self.cipher_gui, 'restart_ui'):
                logging.info("通知主界面重启UI...")
                self.cipher_gui.restart_ui()
            else:
                logging.warning("主界面没有重启UI方法，将使用传统方式重新加载")
                # 如果没有restart_ui方法，尝试传统方式
                if self.cipher_gui:
                    # 应用语言变更到主界面
                    language_value = self.config_manager.get_language()
                    self.cipher_gui._change_language(language_value)
                    
                    # 应用主题变更到主界面
                    theme_value = self.config_manager.get_theme()
                    self.cipher_gui._change_theme(theme_value)
            
            # 记录日志
            logging.info("UI重启已触发")
            
        except Exception as e:
            logging.error(f"执行UI重启时出错: {e}")
            import traceback
            traceback.print_exc()
    
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