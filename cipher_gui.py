#!/usr/bin/env python3
"""
文件加密/解密GUI工具 - 支持多语言和配置文件
支持多种加密算法：OTP和AES256-GCM
改进版：解决UI稳定性问题，增强错误处理，支持国际化
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from config_manager import get_config_manager
from translations import TranslationKeys, get_translator, _

class CipherGUI:
    """加密工具GUI主类 - 支持多语言和配置"""
    
    def __init__(self):
        # 初始化配置和翻译
        self.config_manager = get_config_manager()
        self.translator = get_translator()
        
        # 设置默认值
        default_algorithm = self.config_manager.get_default_algorithm()
        default_key_type = self.config_manager.get_default_key_type()
        
        self.root = tk.Tk()
        self.root.title(_(TranslationKeys.APP_TITLE))
        
        # 设置窗口最小尺寸
        self.root.minsize(800, 600)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 初始化所有UI组件变量
        self._init_ui_variables(default_algorithm, default_key_type)
        
        # 一次性构建完整UI，避免延迟加载导致的闪烁
        self.setup_complete_ui()
        
        # 应用配置
        self._apply_configuration()
        
        # 初始UI状态更新
        self.update_ui_state()
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_(TranslationKeys.FILE_MENU), menu=file_menu)
        file_menu.add_command(label=_(TranslationKeys.SETTINGS_MENU), command=self._open_settings)
        file_menu.add_separator()
        file_menu.add_command(label=_(TranslationKeys.EXIT), command=self.root.quit)
        
        # 语言菜单
        language_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_(TranslationKeys.LANGUAGE_MENU), menu=language_menu)
        language_menu.add_command(label="简体中文", command=lambda: self._change_language("zh_CN"))
        language_menu.add_command(label="English", command=lambda: self._change_language("en_US"))
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=_(TranslationKeys.HELP_MENU), menu=help_menu)
        help_menu.add_command(label=_(TranslationKeys.ABOUT), command=self._show_about)
    
    def _init_ui_variables(self, default_algorithm, default_key_type):
        """初始化所有UI组件变量，确保安全引用"""
        # 算法选择相关
        self.algorithm_var = tk.StringVar(value=default_algorithm)
        self.key_type_var = tk.StringVar(value=default_key_type)
        self.algorithm_combo = None
        self.key_type_combo = None
        self.algorithm_info = None
        
        # 加密部分
        self.entry_input_file = None
        self.entry_output_dir = None
        self.password_entry = None
        
        # 解密部分
        self.entry_input_cipher = None
        self.entry_key_file = None
        self.entry_decrypt_password = None
        self.entry_decrypt_output = None
        
        # 状态栏
        self.status_bar = None
        
        # 缓存已导入的模块，避免重复导入
        self._cipher_modules_imported = False
        self._AlgorithmType = None
        self._KeyType = None
        self._get_algorithm = None
        self._FileFormatHandler = None
    
    def _apply_configuration(self):
        """应用配置文件中的设置"""
        # 如果有默认输入/输出目录，设置到输入框
        default_input_dir = self.config_manager.get_default_input_dir()
        default_output_dir = self.config_manager.get_default_output_dir()
        
        if default_input_dir and self.entry_input_file:
            self.entry_input_file.delete(0, tk.END)
            self.entry_input_file.insert(0, default_input_dir)
        
        if default_output_dir and self.entry_output_dir:
            self.entry_output_dir.delete(0, tk.END)
            self.entry_output_dir.insert(0, default_output_dir)
        
        # 如果有上次使用的文件夹，且配置允许记住
        if self.config_manager.should_remember_last_folder():
            last_input_folder = self.config_manager.get_last_input_folder()
            last_output_folder = self.config_manager.get_last_output_folder()
            
            # 这里可以在文件对话框中使用这些路径
    
    def setup_complete_ui(self):
        """设置完整的用户界面（一次性构建）"""
        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 算法选择部分
        frame_algorithm = tk.LabelFrame(main_container, text=_(TranslationKeys.ALGORITHM_SETTINGS))
        frame_algorithm.pack(fill="x", padx=5, pady=5)
        
        # 算法选择
        tk.Label(frame_algorithm, text=_(TranslationKeys.ENCRYPTION_ALGORITHM)).grid(row=0, column=0, padx=5, pady=10, sticky="w")
        self.algorithm_combo = ttk.Combobox(
            frame_algorithm, 
            textvariable=self.algorithm_var,
            values=["OTP", "AES256"],
            state="readonly",
            width=10
        )
        self.algorithm_combo.grid(row=0, column=1, padx=5, pady=10)
        self.algorithm_combo.bind("<<ComboboxSelected>>", self.on_algorithm_changed)
        
        # 密钥类型选择
        tk.Label(frame_algorithm, text=_(TranslationKeys.KEY_TYPE)).grid(row=0, column=2, padx=5, pady=10, sticky="w")
        self.key_type_combo = ttk.Combobox(
            frame_algorithm,
            textvariable=self.key_type_var,
            values=["random", "password"],
            state="readonly",
            width=10
        )
        self.key_type_combo.grid(row=0, column=3, padx=5, pady=10)
        self.key_type_combo.bind("<<ComboboxSelected>>", self.on_key_type_changed)
        
        # 密码输入框（默认隐藏）
        tk.Label(frame_algorithm, text=_(TranslationKeys.PASSWORD)).grid(row=0, column=4, padx=5, pady=10, sticky="w")
        self.password_entry = tk.Entry(frame_algorithm, width=20, show="*")
        self.password_entry.grid(row=0, column=5, padx=5, pady=10)
        
        # 算法信息标签
        self.algorithm_info = tk.Label(frame_algorithm, text=_("Cipher文件加密工具 - 选择算法开始"), 
                                      font=("Arial", 10), fg="blue")
        self.algorithm_info.grid(row=1, column=0, columnspan=6, padx=5, pady=5)
        
        # 创建加密和解密框架的容器
        frames_container = ttk.Frame(main_container)
        frames_container.pack(fill="both", expand=True, pady=10)
        
        # 加密部分
        frame_encrypt = tk.LabelFrame(frames_container, text=_(TranslationKeys.ENCRYPTION))
        frame_encrypt.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self._setup_encrypt_frame(frame_encrypt)
        
        # 解密部分
        frame_decrypt = tk.LabelFrame(frames_container, text=_(TranslationKeys.DECRYPTION))
        frame_decrypt.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self._setup_decrypt_frame(frame_decrypt)
        
        # 状态栏
        self.status_bar = tk.Label(self.root, text=_(TranslationKeys.READY), bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始化事件绑定
        self.on_algorithm_changed()
    
    def _setup_encrypt_frame(self, frame):
        """设置加密部分的UI"""
        # 输入文件
        tk.Label(frame, text=_(TranslationKeys.INPUT_FILE_PATH)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_input_file = tk.Entry(frame, width=50)
        self.entry_input_file.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(frame, text=_(TranslationKeys.BROWSE), command=lambda: self.browse_file(self.entry_input_file), 
                 bg="#e0e0e0").grid(row=0, column=2, padx=10, pady=10)
        
        # 输出目录
        tk.Label(frame, text=_(TranslationKeys.OUTPUT_DIRECTORY_PATH)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_output_dir = tk.Entry(frame, width=50)
        self.entry_output_dir.grid(row=1, column=1, padx=10, pady=10)
        tk.Button(frame, text=_(TranslationKeys.BROWSE), command=lambda: self.browse_directory(self.entry_output_dir),
                 bg="#e0e0e0").grid(row=1, column=2, padx=10, pady=10)
        
        # 加密按钮
        tk.Button(frame, text=_(TranslationKeys.START_ENCRYPTION), command=self.encrypt, 
                 bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                 padx=20, pady=10).grid(row=2, column=0, columnspan=3, pady=20)
        
        # 添加一些提示信息
        tk.Label(frame, text=_(TranslationKeys.TIPS), font=("Arial", 10, "bold"), fg="#666").grid(row=3, column=0, sticky="w", padx=10)
        tk.Label(frame, text=_(TranslationKeys.TIPS_ENCRYPT), 
                justify="left", fg="#666").grid(row=3, column=1, columnspan=2, sticky="w", padx=10)
    
    def _setup_decrypt_frame(self, frame):
        """设置解密部分的UI"""
        # 输入密文文件
        tk.Label(frame, text=_(TranslationKeys.INPUT_CIPHER_PATH)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_input_cipher = tk.Entry(frame, width=50)
        self.entry_input_cipher.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(frame, text=_(TranslationKeys.BROWSE), command=lambda: self.browse_file(self.entry_input_cipher),
                 bg="#e0e0e0").grid(row=0, column=2, padx=10, pady=10)
        
        # 密钥文件（仅OTP和随机密钥AES）
        tk.Label(frame, text=_(TranslationKeys.KEY_FILE_PATH)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_key_file = tk.Entry(frame, width=50)
        self.entry_key_file.grid(row=1, column=1, padx=10, pady=10)
        tk.Button(frame, text=_(TranslationKeys.BROWSE), command=lambda: self.browse_file(self.entry_key_file),
                 bg="#e0e0e0").grid(row=1, column=2, padx=10, pady=10)
        
        # 解密密码（密码模式AES）
        tk.Label(frame, text=_(TranslationKeys.DECRYPTION_PASSWORD)).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_decrypt_password = tk.Entry(frame, width=50, show="*")
        self.entry_decrypt_password.grid(row=2, column=1, padx=10, pady=10)
        
        # 输出目录
        tk.Label(frame, text=_(TranslationKeys.DECRYPTION_OUTPUT_PATH)).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.entry_decrypt_output = tk.Entry(frame, width=50)
        self.entry_decrypt_output.grid(row=3, column=1, padx=10, pady=10)
        tk.Button(frame, text=_(TranslationKeys.BROWSE), command=lambda: self.browse_directory(self.entry_decrypt_output),
                 bg="#e0e0e0").grid(row=3, column=2, padx=10, pady=10)
        
        # 解密按钮
        tk.Button(frame, text=_(TranslationKeys.START_DECRYPTION), command=self.decrypt,
                 bg="#2196F3", fg="white", font=("Arial", 12, "bold"),
                 padx=20, pady=10).grid(row=4, column=0, columnspan=3, pady=20)
        
        # 添加一些提示信息
        tk.Label(frame, text=_(TranslationKeys.TIPS), font=("Arial", 10, "bold"), fg="#666").grid(row=5, column=0, sticky="w", padx=10)
        tk.Label(frame, text=_(TranslationKeys.TIPS_DECRYPT), 
                justify="left", fg="#666").grid(row=5, column=1, columnspan=2, sticky="w", padx=10)
    
    def on_algorithm_changed(self, event=None):
        """算法选择变更处理"""
        algorithm = self.algorithm_var.get()
        if algorithm == "OTP":
            self.algorithm_info.config(text=_(TranslationKeys.OTP_ALGORITHM_INFO))
            # OTP只支持随机密钥
            self.key_type_var.set("random")
            self.key_type_combo.config(state="disabled")
        else:  # AES256
            self.algorithm_info.config(text=_(TranslationKeys.AES_ALGORITHM_INFO))
            self.key_type_combo.config(state="readonly")
        
        self.update_ui_state()
    
    def on_key_type_changed(self, event=None):
        """密钥类型变更处理"""
        self.update_ui_state()
    
    def update_ui_state(self):
        """更新UI状态 - 改进版，确保组件安全访问"""
        try:
            algorithm = self.algorithm_var.get()
            key_type = self.key_type_var.get()
            
            # 更新密码输入框显示状态（安全地检查组件是否存在）
            if self.password_entry:
                if algorithm == "AES256" and key_type == "password":
                    self.password_entry.grid()
                else:
                    self.password_entry.grid_remove()
            
            if self.entry_decrypt_password:
                if algorithm == "AES256" and key_type == "password":
                    self.entry_decrypt_password.grid()
                else:
                    self.entry_decrypt_password.grid_remove()
            
            # 更新密钥文件输入框显示状态
            if self.entry_key_file:
                if algorithm == "AES256" and key_type == "password":
                    self.entry_key_file.grid_remove()
                else:
                    self.entry_key_file.grid()
            
            # 更新密钥类型组合框状态
            if self.key_type_combo:
                if algorithm == "OTP":
                    self.key_type_combo.config(state="disabled")
                else:
                    self.key_type_combo.config(state="readonly")
            
            # 更新算法信息
            if self.algorithm_info:
                if algorithm == "OTP":
                    self.algorithm_info.config(text=_(TranslationKeys.OTP_ALGORITHM_INFO))
                else:
                    self.algorithm_info.config(text=_(TranslationKeys.AES_ALGORITHM_INFO))
                    
        except Exception as e:
            # 安全地处理UI状态更新错误
            if self.status_bar:
                self.status_bar.config(text=f"UI状态更新错误: {str(e)}")
    
    def browse_file(self, entry):
        """文件选择对话框"""
        # 使用上次访问的文件夹（如果配置允许）
        initial_dir = None
        if self.config_manager.should_remember_last_folder():
            last_folder = self.config_manager.get_last_input_folder()
            if last_folder and os.path.exists(last_folder):
                initial_dir = last_folder
        
        file_path = filedialog.askopenfilename(initialdir=initial_dir)
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)
            
            # 保存文件夹路径
            if self.config_manager.should_remember_last_folder():
                folder_path = os.path.dirname(file_path)
                self.config_manager.set_last_input_folder(folder_path)
    
    def browse_directory(self, entry):
        """目录选择对话框"""
        # 使用上次访问的文件夹（如果配置允许）
        initial_dir = None
        if self.config_manager.should_remember_last_folder():
            last_folder = self.config_manager.get_last_output_folder()
            if last_folder and os.path.exists(last_folder):
                initial_dir = last_folder
        
        directory_path = filedialog.askdirectory(initialdir=initial_dir)
        if directory_path:
            entry.delete(0, tk.END)
            entry.insert(0, directory_path)
            
            # 保存文件夹路径
            if self.config_manager.should_remember_last_folder():
                self.config_manager.set_last_output_folder(directory_path)
    
    def _import_cipher_modules(self):
        """导入加密模块，使用缓存避免重复导入"""
        if not self._cipher_modules_imported:
            try:
                from cipher_algorithms import (
                    AlgorithmType, KeyType, get_algorithm, FileFormatHandler
                )
                self._AlgorithmType = AlgorithmType
                self._KeyType = KeyType
                self._get_algorithm = get_algorithm
                self._FileFormatHandler = FileFormatHandler
                self._cipher_modules_imported = True
                return True
            except ImportError as e:
                self._show_error_message(_(TranslationKeys.ERROR_ENCRYPTION_FAILED, message=str(e)))
                return False
        return True
    
    def _validate_password_strength(self, password):
        """验证密码强度"""
        if not password:
            return False, _(TranslationKeys.ERROR_INVALID_PASSWORD)
        
        min_length = self.config_manager.get_password_min_length()
        if len(password) < min_length:
            return False, _(TranslationKeys.ERROR_PASSWORD_TOO_SHORT, min_length=min_length)
        
        # 检查密码复杂度（如果配置要求）
        if self.config_manager.requires_strong_password():
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            
            if not (has_upper and has_lower and has_digit):
                return False, _(TranslationKeys.ERROR_PASSWORD_STRENGTH)
        
        return True, _(TranslationKeys.OK)
    
    def _show_error_message(self, message):
        """显示错误消息"""
        messagebox.showerror(_(TranslationKeys.ERROR), message)
        if self.status_bar:
            self.status_bar.config(text=f"{_(TranslationKeys.ERROR)}: {message[:50]}...")
    
    def _show_success_message(self, message):
        """显示成功消息"""
        messagebox.showinfo(_(TranslationKeys.OK), message)
        if self.status_bar:
            self.status_bar.config(text=_(TranslationKeys.ENCRYPTION_COMPLETED))
    
    def encrypt(self):
        """加密文件 - 改进版，增强错误处理和密码验证"""
        try:
            # 检查并导入加密模块
            if not self._import_cipher_modules():
                return
            
            # 获取输入参数
            input_file = self.entry_input_file.get().strip()
            output_dir = self.entry_output_dir.get().strip()
            algorithm = self.algorithm_var.get()
            key_type = self.key_type_var.get()
            password = self.password_entry.get().strip() if key_type == "password" else None
            
            # 验证输入
            if not input_file:
                self._show_error_message(_("请输入要加密的文件路径"))
                return
            
            if not output_dir:
                self._show_error_message(_("请输入输出目录路径"))
                return
            
            # 检查文件是否存在
            if not os.path.exists(input_file):
                self._show_error_message(_(TranslationKeys.ERROR_FILE_NOT_FOUND, path=input_file))
                return
            
            # 对于密码模式，验证密码强度
            if algorithm == "AES256" and key_type == "password":
                if not password:
                    self._show_error_message(_("密码模式需要输入密码"))
                    return
                
                # 验证密码强度
                is_valid, msg = self._validate_password_strength(password)
                if not is_valid:
                    self._show_error_message(msg)
                    return
            
            # 创建输出目录
            try:
                os.makedirs(output_dir, exist_ok=True)
            except PermissionError as e:
                self._show_error_message(_(TranslationKeys.ERROR_PERMISSION_DENIED))
                return
            
            # 读取文件
            try:
                with open(input_file, 'rb') as f:
                    plaintext = f.read()
            except IOError as e:
                self._show_error_message(_("读取文件失败: {error}", error=str(e)))
                return
            
            # 获取算法实例
            if algorithm == "OTP":
                algorithm_type = self._AlgorithmType.OTP
            else:
                algorithm_type = self._AlgorithmType.AES256
            
            cipher_algorithm = self._get_algorithm(algorithm_type)
            
            # 加密
            try:
                if algorithm_type == self._AlgorithmType.OTP:
                    result = cipher_algorithm.encrypt(plaintext)
                else:  # AES256
                    if key_type == "random":
                        result = cipher_algorithm.encrypt(plaintext, key_type=self._KeyType.RANDOM)
                    else:
                        result = cipher_algorithm.encrypt(
                            plaintext, 
                            key_type=self._KeyType.PASSWORD,
                            password=password
                        )
            except ValueError as e:
                self._show_error_message(_("加密过程出错: {error}", error=str(e)))
                return
            
            # 构建输出文件路径
            base_name = os.path.basename(input_file)
            
            # 保存密文
            if algorithm_type == self._AlgorithmType.OTP:
                output_file = os.path.join(output_dir, base_name + ".enc")
                self._FileFormatHandler.write_otp_file(output_file, result.ciphertext)
            else:
                output_file = os.path.join(output_dir, base_name + ".enc")
                if key_type == "password":
                    # 密码模式使用带盐值的文件格式
                    self._FileFormatHandler.write_aes_file_with_salt(
                        output_file,
                        result.ciphertext,
                        result.salt,
                        result.iv,
                        result.tag
                    )
                else:
                    # 随机密钥模式使用标准文件格式
                    self._FileFormatHandler.write_aes_file(
                        output_file,
                        result.ciphertext,
                        result.iv,
                        result.tag
                    )

            # 保存密钥（如果是随机密钥模式）
            if result.key_type == self._KeyType.RANDOM:
                if algorithm_type == self._AlgorithmType.OTP:
                    key_file = os.path.join(output_dir, f"key_{base_name}.txt")
                    with open(key_file, 'w') as f:
                        f.write(result.key.hex())
                else:  # AES256随机密钥
                    key_file = os.path.join(output_dir, f"key_{base_name}.key")
                    with open(key_file, 'wb') as f:
                        f.write(result.key)

            # 如果是密码模式，盐值已经包含在密文文件中，不需要额外保存
            if result.key_type == self._KeyType.PASSWORD:
                # 密码模式的盐值已包含在文件格式中，用户只需记住密码即可解密
                pass
            
            # 显示成功消息
            message = _(TranslationKeys.SUCCESS_ENCRYPTION,
                       cipher_file=output_file,
                       key_file=key_file if result.key_type == self._KeyType.RANDOM else _("密码模式：请妥善保管密码"),
                       algorithm=algorithm,
                       key_type=key_type)
            
            self._show_success_message(message)
            self.status_bar.config(text=_(TranslationKeys.ENCRYPTION_COMPLETED))
            
        except FileNotFoundError as e:
            self._show_error_message(_(TranslationKeys.ERROR_FILE_NOT_FOUND, path=str(e)))
        except PermissionError as e:
            self._show_error_message(_(TranslationKeys.ERROR_PERMISSION_DENIED))
        except IOError as e:
            self._show_error_message(_("文件读写错误: {error}", error=str(e)))
        except ValueError as e:
            self._show_error_message(_("参数错误: {error}", error=str(e)))
        except Exception as e:
            self._show_error_message(_(TranslationKeys.ERROR_ENCRYPTION_FAILED, error=str(e)))
    
    def decrypt(self):
        """解密文件 - 改进版，增强错误处理和验证"""
        try:
            # 检查并导入加密模块
            if not self._import_cipher_modules():
                return
            
            # 获取输入参数
            input_file = self.entry_input_cipher.get().strip()
            output_dir = self.entry_decrypt_output.get().strip()
            
            # 验证输入
            if not input_file:
                self._show_error_message(_("请输入要解密的密文文件路径"))
                return
            
            if not output_dir:
                self._show_error_message(_("请输入输出目录路径"))
                return
            
            # 检查文件是否存在
            if not os.path.exists(input_file):
                self._show_error_message(_(TranslationKeys.ERROR_FILE_NOT_FOUND, path=input_file))
                return
            
            # 检测算法
            try:
                algorithm_type = self._FileFormatHandler.detect_algorithm(input_file)
            except Exception as e:
                self._show_error_message(_("检测算法失败: {error}", error=str(e)))
                return
            
            # 读取文件
            if algorithm_type == self._AlgorithmType.OTP:
                # OTP解密
                try:
                    ciphertext, _ = self._FileFormatHandler.read_otp_file(input_file)
                except ValueError as e:
                    self._show_error_message(_("读取OTP文件失败: {error}", error=str(e)))
                    return
                
                # 获取密钥文件路径
                key_file = self.entry_key_file.get().strip()
                if not key_file:
                    self._show_error_message(_("OTP解密需要密钥文件"))
                    return
                
                # 检查密钥文件是否存在
                if not os.path.exists(key_file):
                    self._show_error_message(_(TranslationKeys.ERROR_FILE_NOT_FOUND, path=key_file))
                    return
                
                # 读取密钥
                try:
                    with open(key_file, 'r') as f:
                        key_hex = f.read().strip()
                        key = bytes.fromhex(key_hex)
                except (FileNotFoundError, ValueError) as e:
                    self._show_error_message(_("读取密钥文件失败: {error}", error=str(e)))
                    return
                
                # 解密
                cipher_algorithm = self._get_algorithm(algorithm_type)
                try:
                    result = cipher_algorithm.decrypt(ciphertext, key=key)
                except ValueError as e:
                    self._show_error_message(_("OTP解密失败: {error}", error=str(e)))
                    return
                
            else:  # AES256
                # 先读取文件头判断是哪种AES格式
                try:
                    with open(input_file, 'rb') as f:
                        header = f.read(4)
                except IOError as e:
                    self._show_error_message(_("读取文件失败: {error}", error=str(e)))
                    return
                
                if header == b'AES\x01':
                    # 密码模式格式（带盐值）
                    try:
                        ciphertext, salt, iv, tag, _ = self._FileFormatHandler.read_aes_file_with_salt(input_file)
                    except ValueError as e:
                        self._show_error_message(_("读取AES密码格式文件失败: {error}", error=str(e)))
                        return
                    
                    # 密码模式需要密码
                    password = self.entry_decrypt_password.get().strip()
                    if not password:
                        self._show_error_message(_("AES密码解密需要密码"))
                        return
                    
                    cipher_algorithm = self._get_algorithm(algorithm_type)
                    try:
                        result = cipher_algorithm.decrypt(
                            ciphertext,
                            key_type=self._KeyType.PASSWORD,
                            password=password,
                            salt=salt,
                            iv=iv,
                            tag=tag
                        )
                    except ValueError as e:
                        self._show_error_message(_("AES密码解密失败: {error}", error=str(e)))
                        return
                        
                else:
                    # 随机密钥模式格式（标准AES格式）
                    try:
                        ciphertext, iv, tag, _ = self._FileFormatHandler.read_aes_file(input_file)
                    except ValueError as e:
                        self._show_error_message(_("读取AES文件失败: {error}", error=str(e)))
                        return
                    
                    # 判断密钥类型（通过UI状态）
                    algorithm = self.algorithm_var.get()
                    key_type = self.key_type_var.get() if algorithm == "AES256" else "random"
                    
                    if key_type == "random":
                        # 随机密钥模式
                        key_file = self.entry_key_file.get().strip()
                        if not key_file:
                            self._show_error_message(_("AES随机密钥解密需要密钥文件"))
                            return
                        
                        # 检查密钥文件是否存在
                        if not os.path.exists(key_file):
                            self._show_error_message(_(TranslationKeys.ERROR_FILE_NOT_FOUND, path=key_file))
                            return
                        
                        try:
                            with open(key_file, 'rb') as f:
                                key = f.read()
                        except IOError as e:
                            self._show_error_message(_("读取密钥文件失败: {error}", error=str(e)))
                            return
                        
                        cipher_algorithm = self._get_algorithm(algorithm_type)
                        try:
                            result = cipher_algorithm.decrypt(
                                ciphertext, 
                                key_type=self._KeyType.RANDOM,
                                key=key,
                                iv=iv,
                                tag=tag
                            )
                        except ValueError as e:
                            self._show_error_message(_("AES随机密钥解密失败: {error}", error=str(e)))
                            return
                    else:
                        # 用户选择了密码模式，但文件是随机密钥格式
                        self._show_error_message(_("该文件是随机密钥格式，请使用密钥文件解密"))
                        return
            
            # 创建输出目录
            try:
                os.makedirs(output_dir, exist_ok=True)
            except PermissionError as e:
                self._show_error_message(_(TranslationKeys.ERROR_PERMISSION_DENIED))
                return
            
            # 构建输出文件名
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            if base_name.endswith('.enc'):
                base_name = base_name[:-4]
            
            output_file = os.path.join(output_dir, base_name)
            
            # 保存解密后的文件
            try:
                with open(output_file, 'wb') as f:
                    f.write(result.plaintext)
            except IOError as e:
                self._show_error_message(_("保存解密文件失败: {error}", error=str(e)))
                return
            
            # 显示成功消息
            message = _(TranslationKeys.SUCCESS_DECRYPTION,
                       plaintext_file=output_file,
                       algorithm=algorithm_type.value)
            
            self._show_success_message(message)
            self.status_bar.config(text=_(TranslationKeys.DECRYPTION_COMPLETED))
            
        except Exception as e:
            self._show_error_message(_(TranslationKeys.ERROR_DECRYPTION_FAILED, error=str(e)))
    
    def _open_settings(self):
        """打开设置对话框"""
        # 这是一个简化的设置对话框，实际项目中可以更复杂
        settings_window = tk.Toplevel(self.root)
        settings_window.title(_("设置"))
        settings_window.geometry("400x300")
        
        # 这里可以添加各种设置选项
        tk.Label(settings_window, text=_("设置功能正在开发中...")).pack(pady=20)
        
        # 关闭按钮
        tk.Button(settings_window, text=_("关闭"), command=settings_window.destroy).pack(pady=10)
    
    def _change_language(self, language_code):
        """更改界面语言"""
        try:
            self.translator.set_language(language_code)
            # 重新加载界面
            self._reload_ui()
        except Exception as e:
            self._show_error_message(_("更改语言失败: {error}", error=str(e)))
    
    def _reload_ui(self):
        """重新加载UI以应用新的语言设置"""
        # 销毁当前UI
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 重新创建菜单
        self._create_menu_bar()
        
        # 重新创建UI
        self._init_ui_variables(
            self.config_manager.get_default_algorithm(),
            self.config_manager.get_default_key_type()
        )
        self.setup_complete_ui()
        self._apply_configuration()
        self.update_ui_state()
        
        # 更新窗口标题
        self.root.title(_(TranslationKeys.APP_TITLE))
    
    def _show_about(self):
        """显示关于对话框"""
        about_text = f"""Cipher - 文件加密工具
版本: 1.0 (支持多语言和配置)
支持算法: OTP, AES256-GCM
语言: {self.translator.get_current_language_display_name()}
配置文件: {self.config_manager.config_file}
        
版权所有 © 2026 miniCipher项目"""
        
        messagebox.showinfo(_("关于"), about_text)
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()

def main():
    """主函数"""
    app = CipherGUI()
    app.run()

if __name__ == "__main__":
    main()