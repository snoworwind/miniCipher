#!/usr/bin/env python3
"""
文件加密/解密GUI工具 - 支持多语言和配置文件
支持多种加密算法：OTP和AES256-GCM
改进版：解决UI稳定性问题，增强错误处理，支持国际化，集成日志系统
"""

import os
import tkinter as tk
import logging
import secrets
from tkinter import filedialog, ttk
from config_manager import get_config_manager
from translations import TranslationKeys, get_translator, _
from theme_manager import get_theme_manager, apply_theme_to_window, apply_theme_to_toplevel, CustomMessageBox
from custom_menu_bar import CustomMenuBarBuilder

class CipherGUI:
    """加密工具GUI主类 - 支持多语言和配置"""
    
    def __init__(self):
        # 初始化配置和翻译
        self.config_manager = get_config_manager()
        self.translator = get_translator()
        self.theme_manager = get_theme_manager()
        
        # 自定义消息框
        self.message_box = CustomMessageBox()
        
        # 设置默认值
        default_algorithm = self.config_manager.get_default_algorithm()
        default_key_type = self.config_manager.get_default_key_type()
        
        self.root = tk.Tk()
        self.root.title(_(TranslationKeys.APP_TITLE))
        
        # 设置窗口最小尺寸
        self.root.minsize(800, 600)
        
        # 应用主题
        apply_theme_to_window(self.root)
        
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
        
        # 设置消息框的父窗口
        self.message_box.parent = self.root
        
        # 初始化日志记录
        logging.info("CipherGUI 初始化完成")
    
    def _create_menu_bar(self):
        """创建自定义菜单栏"""
        # 使用自定义菜单栏替换原生菜单
        self.menu_bar = CustomMenuBarBuilder.create_for_cipher_gui(self.root, self)
        self.menu_bar.pack(fill="x", side="top")
        
        # 应用主题到自定义菜单栏
        self.theme_manager.apply_to_widget(self.menu_bar)
        
        # 移除原生菜单配置（如果存在）
        try:
            self.root.config(menu=None)
        except:
            pass
    
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
        logging.debug("配置已应用到界面")
    
    def setup_complete_ui(self):
        """设置完整的用户界面（一次性构建）"""
        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 算法选择部分
        frame_algorithm = ttk.LabelFrame(main_container, text=_(TranslationKeys.ALGORITHM_SETTINGS))
        frame_algorithm.pack(fill="x", padx=5, pady=5)
        
        # 算法选择
        ttk.Label(frame_algorithm, text=_(TranslationKeys.ENCRYPTION_ALGORITHM)).grid(row=0, column=0, padx=5, pady=10, sticky="w")
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
        ttk.Label(frame_algorithm, text=_(TranslationKeys.KEY_TYPE)).grid(row=0, column=2, padx=5, pady=10, sticky="w")
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
        ttk.Label(frame_algorithm, text=_(TranslationKeys.PASSWORD)).grid(row=0, column=4, padx=5, pady=10, sticky="w")
        self.password_entry = ttk.Entry(frame_algorithm, width=20, show="*")
        self.password_entry.grid(row=0, column=5, padx=5, pady=10)
        
        # 算法信息标签
        self.algorithm_info = ttk.Label(frame_algorithm, text=_("Cipher文件加密工具 - 选择算法开始"), 
                                      font=("Segoe UI", 10))
        self.algorithm_info.grid(row=1, column=0, columnspan=6, padx=5, pady=5)
        
        # 创建加密和解密框架的容器
        frames_container = ttk.Frame(main_container)
        frames_container.pack(fill="both", expand=True, pady=10)
        
        # 加密部分
        frame_encrypt = ttk.LabelFrame(frames_container, text=_(TranslationKeys.ENCRYPTION))
        frame_encrypt.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self._setup_encrypt_frame(frame_encrypt)
        
        # 解密部分
        frame_decrypt = ttk.LabelFrame(frames_container, text=_(TranslationKeys.DECRYPTION))
        frame_decrypt.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self._setup_decrypt_frame(frame_decrypt)
        
        # 状态栏
        self.status_bar = tk.Label(self.root, text=_(TranslationKeys.READY), bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        # 应用主题到状态栏
        self.theme_manager.apply_to_widget(self.status_bar)
        
        # 初始化事件绑定
        self.on_algorithm_changed()
    
    def _setup_encrypt_frame(self, frame):
        """设置加密部分的UI"""
        # 输入文件
        ttk.Label(frame, text=_(TranslationKeys.INPUT_FILE_PATH)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_input_file = ttk.Entry(frame, width=50)
        self.entry_input_file.grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(frame, text=_(TranslationKeys.BROWSE), command=lambda: self.browse_file(self.entry_input_file, is_input=True)).grid(row=0, column=2, padx=10, pady=10)
        
        # 输出目录
        ttk.Label(frame, text=_(TranslationKeys.OUTPUT_DIRECTORY_PATH)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_output_dir = ttk.Entry(frame, width=50)
        self.entry_output_dir.grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(frame, text=_(TranslationKeys.BROWSE), command=lambda: self.browse_directory(self.entry_output_dir, is_output=True)).grid(row=1, column=2, padx=10, pady=10)
        
        # 加密按钮
        ttk.Button(frame, text=_(TranslationKeys.START_ENCRYPTION), command=self.encrypt,
                 style="Success.TButton").grid(row=2, column=0, columnspan=3, pady=20)
        
        # 添加一些提示信息
        ttk.Label(frame, text=_(TranslationKeys.TIPS), font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", padx=10)
        ttk.Label(frame, text=_(TranslationKeys.TIPS_ENCRYPT), 
                justify="left").grid(row=3, column=1, columnspan=2, sticky="w", padx=10)
    
    def _setup_decrypt_frame(self, frame):
        """设置解密部分的UI"""
        # 输入密文文件
        ttk.Label(frame, text=_(TranslationKeys.INPUT_CIPHER_PATH)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_input_cipher = ttk.Entry(frame, width=50)
        self.entry_input_cipher.grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(frame, text=_(TranslationKeys.BROWSE), command=lambda: self.browse_file(self.entry_input_cipher, is_input=True)).grid(row=0, column=2, padx=10, pady=10)
        
        # 密钥文件（仅OTP和随机密钥AES）
        ttk.Label(frame, text=_(TranslationKeys.KEY_FILE_PATH)).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_key_file = ttk.Entry(frame, width=50)
        self.entry_key_file.grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(frame, text=_(TranslationKeys.BROWSE), command=lambda: self.browse_file(self.entry_key_file, is_input=True)).grid(row=1, column=2, padx=10, pady=10)
        
        # 解密密码（密码模式AES）
        ttk.Label(frame, text=_(TranslationKeys.DECRYPTION_PASSWORD)).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_decrypt_password = ttk.Entry(frame, width=50, show="*")
        self.entry_decrypt_password.grid(row=2, column=1, padx=10, pady=10)
        
        # 输出目录
        ttk.Label(frame, text=_(TranslationKeys.DECRYPTION_OUTPUT_PATH)).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.entry_decrypt_output = ttk.Entry(frame, width=50)
        self.entry_decrypt_output.grid(row=3, column=1, padx=10, pady=10)
        ttk.Button(frame, text=_(TranslationKeys.BROWSE), command=lambda: self.browse_directory(self.entry_decrypt_output, is_output=True)).grid(row=3, column=2, padx=10, pady=10)
        
        # 解密按钮
        ttk.Button(frame, text=_(TranslationKeys.START_DECRYPTION), command=self.decrypt,
                 style="Primary.TButton").grid(row=4, column=0, columnspan=3, pady=20)
        
        # 添加一些提示信息
        ttk.Label(frame, text=_(TranslationKeys.TIPS), font=("Segoe UI", 10, "bold")).grid(row=5, column=0, sticky="w", padx=10)
        ttk.Label(frame, text=_(TranslationKeys.TIPS_DECRYPT), 
                justify="left").grid(row=5, column=1, columnspan=2, sticky="w", padx=10)
    
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
            logging.error(f"UI状态更新错误: {e}")
    
    def browse_file(self, entry, is_input=True):
        """文件选择对话框"""
        # 优先级：当前输入框内容 > 默认目录 > 上次文件夹
        initial_dir = None
        
        # 1. 先检查当前输入框是否有路径
        current_text = entry.get().strip()
        if current_text and os.path.exists(os.path.dirname(current_text) if os.path.isfile(current_text) else current_text):
            initial_dir = os.path.dirname(current_text) if os.path.isfile(current_text) else current_text
        # 2. 检查默认目录
        elif is_input:
            default_input_dir = self.config_manager.get_default_input_dir()
            if default_input_dir and os.path.exists(default_input_dir):
                initial_dir = default_input_dir
        else:
            default_output_dir = self.config_manager.get_default_output_dir()
            if default_output_dir and os.path.exists(default_output_dir):
                initial_dir = default_output_dir
        
        # 3. 检查上次使用的文件夹（如果配置允许）
        if not initial_dir and self.config_manager.should_remember_last_folder():
            if is_input:
                last_folder = self.config_manager.get_last_input_folder()
                if last_folder and os.path.exists(last_folder):
                    initial_dir = last_folder
            else:
                last_folder = self.config_manager.get_last_output_folder()
                if last_folder and os.path.exists(last_folder):
                    initial_dir = last_folder
        
        file_path = filedialog.askopenfilename(initialdir=initial_dir)
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)
            
            # 保存文件夹路径（如果配置允许）
            if self.config_manager.should_remember_last_folder():
                folder_path = os.path.dirname(file_path)
                if is_input:
                    self.config_manager.set_last_input_folder(folder_path)
                else:
                    self.config_manager.set_last_output_folder(folder_path)
            
            logging.debug(f"选择了文件: {file_path}")
    
    def browse_directory(self, entry, is_output=True):
        """目录选择对话框"""
        # 优先级：当前输入框内容 > 默认目录 > 上次文件夹
        initial_dir = None
        
        # 1. 先检查当前输入框是否有路径
        current_text = entry.get().strip()
        if current_text and os.path.exists(current_text):
            initial_dir = current_text
        # 2. 检查默认目录
        elif is_output:
            default_output_dir = self.config_manager.get_default_output_dir()
            if default_output_dir and os.path.exists(default_output_dir):
                initial_dir = default_output_dir
        else:
            default_input_dir = self.config_manager.get_default_input_dir()
            if default_input_dir and os.path.exists(default_input_dir):
                initial_dir = default_input_dir
        
        # 3. 检查上次使用的文件夹（如果配置允许）
        if not initial_dir and self.config_manager.should_remember_last_folder():
            if is_output:
                last_folder = self.config_manager.get_last_output_folder()
                if last_folder and os.path.exists(last_folder):
                    initial_dir = last_folder
            else:
                last_folder = self.config_manager.get_last_input_folder()
                if last_folder and os.path.exists(last_folder):
                    initial_dir = last_folder
        
        directory_path = filedialog.askdirectory(initialdir=initial_dir)
        if directory_path:
            entry.delete(0, tk.END)
            entry.insert(0, directory_path)
            
            # 保存文件夹路径（如果配置允许）
            if self.config_manager.should_remember_last_folder():
                if is_output:
                    self.config_manager.set_last_output_folder(directory_path)
                else:
                    self.config_manager.set_last_input_folder(directory_path)
            
            logging.debug(f"选择了目录: {directory_path}")
    
    def _import_cipher_modules(self):
        """导入加密模块，使用缓存避免重复导入 - 避免污染全局作用域"""
        if not self._cipher_modules_imported:
            try:
                # 导入FileCipher高级API
                import cipher_algorithms as ca
                self._AlgorithmType = ca.AlgorithmType
                self._KeyType = ca.KeyType
                self._FileFormatHandler = ca.FileFormatHandler
                self._FileCipher = ca.FileCipher
                self._get_algorithm = ca.get_algorithm
                self._EncryptionResult = ca.EncryptionResult
                self._cipher_modules_imported = True
                logging.debug("加密模块导入成功")
                return True
            except ImportError as e:
                # 使用硬编码字符串避免翻译依赖问题
                error_msg = f"导入加密模块失败: {str(e)}"
                logging.error(error_msg)
                # 直接显示错误消息，避免使用翻译函数
                if hasattr(self, 'message_box') and self.message_box:
                    self.message_box.show_error("错误", error_msg)
                return False
        return True
    
    def _validate_password_strength(self, password):
        """验证密码强度 - 使用FileCipher的验证方法"""
        # 创建FileCipher实例进行密码验证
        if not self._import_cipher_modules():
            return False, "无法加载加密模块"
        
        file_cipher = self._FileCipher(self.config_manager)
        return file_cipher.validate_password(password)
    
    def _safe_translate(self, key, **kwargs):
        """安全地获取翻译，处理_函数不可用或被错误赋值的情况"""
        try:
            # 尝试从translations模块重新导入_函数
            from translations import _ as translate_func
            if callable(translate_func):
                return translate_func(key, **kwargs)
        except (ImportError, AttributeError, TypeError):
            pass
        
        # 使用硬编码的fallback文本
        fallback_texts = {
            TranslationKeys.SUCCESS_DECRYPTION: "解密成功！文件已保存到: {plaintext_file}，算法: {algorithm}",
            TranslationKeys.ERROR_DECRYPTION_FAILED: "解密失败: {error}",
            TranslationKeys.SUCCESS_ENCRYPTION: "加密成功！密文文件: {cipher_file}，密钥文件: {key_file}，算法: {algorithm}，密钥类型: {key_type}",
            TranslationKeys.ERROR_ENCRYPTION_FAILED: "加密失败: {error}",
            TranslationKeys.ERROR_INVALID_PASSWORD: "无效的密码",
            TranslationKeys.ERROR_PASSWORD_TOO_SHORT: "密码太短，至少需要{min_length}个字符",
            TranslationKeys.ERROR_PASSWORD_STRENGTH: "密码强度不足，需要包含大小写字母和数字",
            TranslationKeys.OK: "正常",
        }
        
        text = fallback_texts.get(key, str(key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except:
                return text
        return text
    
    
    def _show_error_message(self, message):
        """显示错误消息 - 安全版本，处理翻译函数不可用的情况"""
        try:
            # 尝试使用翻译，失败时使用默认文本
            title = _(TranslationKeys.ERROR)
        except (NameError, AttributeError):
            title = "错误"
        
        self.message_box.show_error(title, message)
        
        # 状态栏显示也使用安全版本
        if self.status_bar:
            try:
                error_text = _(TranslationKeys.ERROR)
                status_text = f"{error_text}: {message[:50]}..."
            except (NameError, AttributeError):
                status_text = f"错误: {message[:50]}..."
            self.status_bar.config(text=status_text)
        
        logging.error(f"错误消息: {message}")
    
    def _show_success_message(self, message):
        """显示成功消息 - 完全安全的版本，确保任何UI异常都不会传播"""
        # 尝试显示消息框，但如果失败，不影响成功状态
        try:
            try:
                title = _(TranslationKeys.OK)
            except (NameError, AttributeError):
                title = "成功"
            
            self.message_box.show_success(title, message)
        except Exception as e:
            # 即使显示消息框失败，也不影响解密成功的状态
            # 记录警告，但不传播异常
            logging.warning(f"显示成功消息框时出错: {e}")
        
        # 安全地设置状态栏文本
        if self.status_bar:
            try:
                status_text = _(TranslationKeys.ENCRYPTION_COMPLETED)
            except (NameError, AttributeError):
                status_text = "加密完成"
            try:
                self.status_bar.config(text=status_text)
            except Exception as e:
                logging.warning(f"更新状态栏时出错: {e}")
        
        logging.info(f"成功消息: {message}")
    
    
    def _decrypt_file_chunked(self, input_file, output_file, algorithm_type, key_type, key=None, password=None, salt=None, iv=None, tag=None):
        """分块解密文件"""
        # 获取缓冲区大小（MB）并转换为字节
        buffer_size_mb = self.config_manager.get_buffer_size()
        chunk_size = buffer_size_mb * 1024 * 1024  # 转换为字节
        
        # 获取文件大小用于日志记录
        total_file_size = os.path.getsize(input_file)
        
        logging.info(f"开始分块解密，块大小: {buffer_size_mb}MB ({chunk_size}字节), 文件总大小: {total_file_size:,}字节")
        logging.info(f"算法类型: {algorithm_type.value}, 密钥类型: {key_type.value}")
        
        # 获取算法实例
        cipher_algorithm = self._get_algorithm(algorithm_type)
        
        if algorithm_type == self._AlgorithmType.OTP:
            # OTP算法分块解密
            if not key:
                raise ValueError("OTP解密需要密钥")
            
            # 检查密钥长度是否匹配文件大小
            file_size = os.path.getsize(input_file)
            logging.info(f"OTP解密参数: 密钥长度={len(key)}字节, 文件大小={file_size}字节")
            
            if len(key) != file_size:
                raise ValueError(f"密钥长度({len(key)})与文件大小({file_size})不匹配")
            
            # 分块读取、解密、写入
            block_count = 0
            with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
                total_read = 0
                while True:
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    
                    block_count += 1
                    # 获取对应的密钥块
                    key_chunk = key[total_read:total_read + len(chunk)]
                    
                    # OTP解密：异或操作
                    plain_chunk = bytes([a ^ b for a, b in zip(chunk, key_chunk)])
                    f_out.write(plain_chunk)
                    
                    total_read += len(chunk)
                    
                    # 详细日志：每块处理情况
                    if block_count % 10 == 0 or total_read % (5 * 1024 * 1024) == 0:
                        logging.debug(f"OTP解密块 #{block_count}: 块大小={len(chunk)}字节, 已处理={total_read:,}/{file_size:,}字节")
                    
                    # 更新状态栏显示进度
                    if self.status_bar and total_read % (10 * 1024 * 1024) == 0:  # 每10MB更新一次
                        progress = (total_read / file_size) * 100
                        self.status_bar.config(text=f"解密进度: {progress:.1f}%")
                        self.root.update_idletasks()
            
            logging.info(f"OTP分块解密完成: 共处理{block_count}个块, 总处理{total_read:,}字节")
            
            # 验证输出文件
            try:
                if not os.path.exists(output_file):
                    raise ValueError(f"解密文件不存在: {output_file}")
                
                output_size = os.path.getsize(output_file)
                logging.info(f"解密输出文件验证: 文件存在, 大小={output_size:,}字节")
                
                if output_size == 0:
                    logging.warning(f"解密文件为空: {output_file}")
                
                # 直接返回解密结果，不调用cipher_algorithm.decrypt以避免长度检查
                from cipher_algorithms import DecryptionResult
                return DecryptionResult(
                    plaintext=b'',  # 对于大文件，不需要实际内容
                    algorithm=algorithm_type
                )
            except Exception as e:
                logging.error(f"验证解密文件时出错: {e}")
                # 如果验证失败，重新抛出异常
                raise
        
        else:  # AES256
            # AES256-GCM算法分块解密
            if key_type == self._KeyType.RANDOM:
                if not all([key, iv, tag]):
                    raise ValueError("AES256随机密钥解密需要key、iv和tag")
                
                # 在解密开始前验证标签长度
                if len(tag) != 16:
                    raise ValueError(f"认证标签长度不正确，应为16字节，实际为{len(tag)}字节。请检查密钥文件是否正确。")
                
                # 添加详细日志记录
                logging.info(f"AES256随机密钥分块解密参数:")
                logging.info(f"  输入文件: {input_file}")
                logging.info(f"  输出文件: {output_file}")
                logging.info(f"  密钥长度: {len(key)}字节")
                logging.info(f"  IV (前16位): {iv.hex()[:32]}...")
                logging.info(f"  标签 (前16位): {tag.hex()[:32]}...")
                
                # 检查文件格式：如果是标准格式（包含文件头），需要先读取文件头和IV
                with open(input_file, 'rb') as f:
                    header = f.read(4)
                
                logging.info(f"文件头: {header.hex() if header else '空'}")
                
                # 如果是标准AES格式（b'AES\x00'），需要跳过文件头和IV
                if header == b'AES\x00':
                    # 读取IV（应该与提供的iv匹配）
                    try:
                        with open(input_file, 'rb') as f:
                            f.read(4)  # 跳过文件头
                            file_iv = f.read(12)  # 读取文件中的IV
                        
                        # 验证文件中的IV是否与提供的IV匹配
                        logging.info(f"文件中的IV: {file_iv.hex()[:24]}...")
                        logging.info(f"提供的IV: {iv.hex()[:24]}...")
                        
                        if file_iv != iv:
                            raise ValueError(f"文件中的IV({file_iv.hex()[:24]}...)与提供的IV({iv.hex()[:24]}...)不匹配")
                        
                        logging.info("IV验证通过")
                    except Exception as e:
                        logging.error(f"读取和验证IV时出错: {e}")
                        raise
                    
                    # 计算需要跳过的字节数：文件头(4字节) + IV(12字节) = 16字节
                    header_skip = 16
                    # 标签在文件末尾16字节，密文在中间
                    try:
                        ciphertext_size = os.path.getsize(input_file) - header_skip - 16
                        logging.info(f"密文大小计算: 文件大小={os.path.getsize(input_file)}字节, header_skip={header_skip}, 标签大小=16, ciphertext_size={ciphertext_size}字节")
                        
                        if ciphertext_size <= 0:
                            raise ValueError(f"密文大小无效: {ciphertext_size}字节")
                    except Exception as e:
                        logging.error(f"计算密文大小时出错: {e}")
                        raise
                    
                    # 创建解密器
                    try:
                        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                        from cryptography.hazmat.backends import default_backend
                        cipher = Cipher(
                            algorithms.AES(key),
                            modes.GCM(iv, tag),
                            backend=default_backend()
                        )
                        decryptor = cipher.decryptor()
                        logging.info("解密器创建成功")
                    except Exception as e:
                        logging.error(f"创建解密器时出错: {e}")
                        raise
                    
                    # 分块读取、解密、写入（跳过文件头和IV）
                    try:
                        block_count = 0
                        total_written = 0
                        
                        with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
                            # 跳过文件头和IV
                            f_in.seek(header_skip)
                            
                            # 计算需要读取的密文大小
                            bytes_remaining = ciphertext_size
                            
                            while bytes_remaining > 0:
                                # 读取块，但不能超过剩余密文大小
                                read_size = min(chunk_size, bytes_remaining)
                                chunk = f_in.read(read_size)
                                if not chunk:
                                    logging.warning(f"读取到空块，但仍有{bytes_remaining}字节剩余")
                                    break
                                
                                # 解密块
                                try:
                                    plain_chunk = decryptor.update(chunk)
                                    f_out.write(plain_chunk)
                                    total_written += len(plain_chunk)
                                except Exception as e:
                                    logging.error(f"解密块失败: 块偏移量={ciphertext_size-bytes_remaining}字节, 块大小={len(chunk)}字节, 错误: {e}")
                                    raise
                                
                                bytes_remaining -= len(chunk)
                                block_count += 1
                                
                                # 每10个块或每10MB记录一次进度
                                if block_count % 10 == 0 or bytes_remaining % (10 * 1024 * 1024) == 0:
                                    progress = ((ciphertext_size - bytes_remaining) / ciphertext_size) * 100
                                    logging.info(f"解密进度: {progress:.1f}% ({ciphertext_size - bytes_remaining}/{ciphertext_size}字节)")
                                
                                # 更新状态栏显示进度
                                if self.status_bar:
                                    progress = ((ciphertext_size - bytes_remaining) / ciphertext_size) * 100
                                    self.status_bar.config(text=f"解密进度: {progress:.1f}%")
                                    self.root.update_idletasks()
                        
                        logging.info(f"分块解密完成: 共处理{block_count}个块, 总写入{total_written}字节")
                        
                        # 完成解密
                        final_chunk = decryptor.finalize()
                        if final_chunk:
                            with open(output_file, 'ab') as f_out:
                                f_out.write(final_chunk)
                                logging.info(f"写入最终块: {len(final_chunk)}字节")
                        
                        # 验证输出文件大小
                        output_size = os.path.getsize(output_file)
                        expected_size = ciphertext_size  # AES-GCM不增加填充
                        if output_size != expected_size:
                            logging.warning(f"输出文件大小({output_size}字节)与预期大小({expected_size}字节)不匹配")
                        else:
                            logging.info(f"输出文件大小验证通过: {output_size}字节")
                        
                    except Exception as e:
                        logging.error(f"分块解密过程中出错: {e}")
                        raise
                    
                else:
                    # 原始格式（纯密文，无文件头）
                    # 创建解密器
                    try:
                        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                        from cryptography.hazmat.backends import default_backend
                        cipher = Cipher(
                            algorithms.AES(key),
                            modes.GCM(iv, tag),
                            backend=default_backend()
                        )
                        decryptor = cipher.decryptor()
                        logging.info("原始格式解密器创建成功")
                    except Exception as e:
                        logging.error(f"创建原始格式解密器时出错: {e}")
                        raise
                    
                    # 分块读取、解密、写入
                    try:
                        block_count = 0
                        total_written = 0
                        file_size = os.path.getsize(input_file)
                        
                        with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
                            while True:
                                chunk = f_in.read(chunk_size)
                                if not chunk:
                                    break
                                
                                # 解密块
                                try:
                                    plain_chunk = decryptor.update(chunk)
                                    f_out.write(plain_chunk)
                                    total_written += len(plain_chunk)
                                except Exception as e:
                                    current_pos = f_in.tell()
                                    logging.error(f"解密块失败: 位置={current_pos-len(chunk)}字节, 块大小={len(chunk)}字节, 错误: {e}")
                                    raise
                                
                                block_count += 1
                                
                                # 每10个块或每10MB记录一次进度
                                if block_count % 10 == 0 or f_in.tell() % (10 * 1024 * 1024) == 0:
                                    progress = (f_in.tell() / file_size) * 100
                                    logging.info(f"原始格式解密进度: {progress:.1f}% ({f_in.tell()}/{file_size}字节)")
                                
                                # 更新状态栏显示进度
                                if self.status_bar:
                                    progress = (f_in.tell() / file_size) * 100
                                    self.status_bar.config(text=f"解密进度: {progress:.1f}%")
                                    self.root.update_idletasks()
                        
                        logging.info(f"原始格式分块解密完成: 共处理{block_count}个块, 总写入{total_written}字节")
                        
                        # 完成解密
                        final_chunk = decryptor.finalize()
                        if final_chunk:
                            with open(output_file, 'ab') as f_out:
                                f_out.write(final_chunk)
                                logging.info(f"写入原始格式最终块: {len(final_chunk)}字节")
                        
                    except Exception as e:
                        logging.error(f"原始格式分块解密过程中出错: {e}")
                        raise
                
                # 读取整个明文以返回结果 - 对于大文件可能内存不足，改为检查文件存在性
                try:
                    # 只检查文件是否存在，不读取整个文件
                    if not os.path.exists(output_file):
                        raise ValueError(f"解密文件不存在: {output_file}")
                    
                    # 获取文件大小用于验证
                    file_size = os.path.getsize(output_file)
                    if file_size == 0:
                        logging.warning(f"解密文件为空: {output_file}")
                    
                    # 直接返回解密结果
                    from cipher_algorithms import DecryptionResult
                    return DecryptionResult(
                        plaintext=b'',  # 对于大文件，不需要实际内容
                        algorithm=algorithm_type
                    )
                except Exception as e:
                    logging.error(f"验证解密文件时出错: {e}")
                    # 如果验证失败，重新抛出异常
                    raise
            
            else:  # 密码模式
                if not all([password, salt, iv, tag]):
                    raise ValueError("AES256密码解密需要password、salt、iv和tag")
                
                # 在开始解密前添加标签验证
                if len(tag) != 16:
                    raise ValueError(f"认证标签长度不正确，应为16字节，实际为{len(tag)}字节")
                
                # 使用新的分块解密方法
                buffer_size_mb = self.config_manager.get_buffer_size()
                chunk_size = buffer_size_mb * 1024 * 1024  # 转换为字节
                
                result = cipher_algorithm.decrypt_with_password_chunked_from_file(
                    input_file,
                    output_file,
                    password,
                    salt,
                    iv,
                    tag,
                    chunk_size=chunk_size
                )
                
                return result
    
    def encrypt(self):
        """加密文件 - 使用FileCipher高级API"""
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
            
            # 构建输出文件路径
            base_name = os.path.basename(input_file)
            output_file = os.path.join(output_dir, base_name + ".enc")
            
            # 创建FileCipher实例
            file_cipher = self._FileCipher(self.config_manager)
            
            # 进度回调函数
            def progress_callback(progress, message):
                self.status_bar.config(text=f"{message} ({progress:.1f}%)")
                self.root.update_idletasks()
            
            # 使用FileCipher加密文件
            result = file_cipher.encrypt_file(
                input_path=input_file,
                output_path=output_file,
                algorithm=algorithm,
                key_type=key_type,
                password=password,
                progress_callback=progress_callback
            )
            
            # 保存密钥（如果需要）
            key_file = None
            if result.get('key_file_needed'):
                if algorithm == "OTP":
                    key_file = file_cipher.save_key(
                        result['key'],
                        output_dir,
                        base_name,
                        algorithm,
                        key_type
                    )
                else:  # AES256 random key
                    key_file = file_cipher.save_key(
                        result['key'],
                        output_dir,
                        base_name,
                        algorithm,
                        key_type
                    )
            
            # 显示成功消息
            message = self._safe_translate(TranslationKeys.SUCCESS_ENCRYPTION,
                       cipher_file=output_file,
                       key_file=key_file if key_file else self._safe_translate("密码模式：请妥善保管密码"),
                       algorithm=algorithm,
                       key_type=key_type)
            
            self._show_success_message(message)
            
            return  # 立即返回，避免后续异常被捕获
            
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
        """解密文件 - 支持分块处理"""
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
            
            # 检查文件大小，决定是否使用分块处理
            file_size = os.path.getsize(input_file)
            buffer_size_mb = self.config_manager.get_buffer_size()
            buffer_size_bytes = buffer_size_mb * 1024 * 1024
            
            # 构建输出文件名
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            if base_name.endswith('.enc'):
                base_name = base_name[:-4]
            
            output_file = os.path.join(output_dir, base_name)
            
            # 创建输出目录
            try:
                os.makedirs(output_dir, exist_ok=True)
            except PermissionError as e:
                self._show_error_message(_(TranslationKeys.ERROR_PERMISSION_DENIED))
                return
            
            # 如果文件小于缓冲区大小，使用完整读取（向后兼容）
            if file_size <= buffer_size_bytes:
                logging.info(f"文件较小({file_size}字节)，使用完整读取模式")
                # 使用完整读取模式
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
                    
                    # 读取密钥 - 使用FileCipher
                    try:
                        if not self._import_cipher_modules():
                            self._show_error_message(_("无法加载加密模块"))
                            return
                        file_cipher = self._FileCipher(self.config_manager)
                        key = file_cipher.load_key(key_file, "OTP")
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
                    
                    # 保存解密后的文件
                    with open(output_file, 'wb') as f:
                        f.write(result.plaintext)
                    
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
                        
                        # 保存解密后的文件
                        with open(output_file, 'wb') as f:
                            f.write(result.plaintext)
                            
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
                            
                            # 保存解密后的文件
                            with open(output_file, 'wb') as f:
                                f.write(result.plaintext)
                        else:
                            # 用户选择了密码模式，但文件是随机密钥格式
                            self._show_error_message(_("该文件是随机密钥格式，请使用密钥文件解密"))
                            return
                
            else:
                # 大文件使用分块解密
                logging.info(f"文件较大({file_size}字节)，使用分块解密模式")
                # 安全地设置状态栏文本，处理翻译函数不可用的情况
                try:
                    status_text = _("开始分块解密...")
                except (NameError, AttributeError):
                    status_text = "开始分块解密..."
                self.status_bar.config(text=status_text)
                self.root.update_idletasks()
                
                if algorithm_type == self._AlgorithmType.OTP:
                    # OTP分块解密
                    # 获取密钥文件路径
                    key_file = self.entry_key_file.get().strip()
                    if not key_file:
                        self._show_error_message(_("OTP解密需要密钥文件"))
                        return
                    
                    # 检查密钥文件是否存在
                    if not os.path.exists(key_file):
                        self._show_error_message(_(TranslationKeys.ERROR_FILE_NOT_FOUND, path=key_file))
                        return
                    
                    # 读取密钥 - 使用FileCipher
                    try:
                        if not self._import_cipher_modules():
                            self._show_error_message(_("无法加载加密模块"))
                            return
                        file_cipher = self._FileCipher(self.config_manager)
                        key = file_cipher.load_key(key_file, "OTP")
                    except (FileNotFoundError, ValueError) as e:
                        self._show_error_message(_("读取密钥文件失败: {error}", error=str(e)))
                        return
                    
                    # 分块解密
                    try:
                        self._decrypt_file_chunked(
                            input_file,
                            output_file,
                            algorithm_type,
                            self._KeyType.RANDOM,
                            key=key
                        )
                    except Exception as e:
                        self._show_error_message(_("OTP分块解密失败: {error}", error=str(e)))
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
                            _, salt, iv, tag, _ = self._FileFormatHandler.read_aes_file_with_salt(input_file)
                        except ValueError as e:
                            self._show_error_message(_("读取AES密码格式文件失败: {error}", error=str(e)))
                            return
                        
                        # 密码模式需要密码
                        password = self.entry_decrypt_password.get().strip()
                        if not password:
                            self._show_error_message(_("AES密码解密需要密码"))
                            return
                        
                        # 密码模式分块解密
                        try:
                            self._decrypt_file_chunked(
                                input_file,
                                output_file,
                                algorithm_type,
                                self._KeyType.PASSWORD,
                                password=password,
                                salt=salt,
                                iv=iv,
                                tag=tag
                            )
                        except Exception as e:
                            self._show_error_message(_("AES密码分块解密失败: {error}", error=str(e)))
                            return
                            
                    else:
                        # 随机密钥模式格式（标准AES格式）
                        try:
                            _, iv, tag, _ = self._FileFormatHandler.read_aes_file(input_file)
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
                            
                            # 分块解密
                            try:
                                self._decrypt_file_chunked(
                                    input_file,
                                    output_file,
                                    algorithm_type,
                                    self._KeyType.RANDOM,
                                    key=key,
                                    iv=iv,
                                    tag=tag
                                )
                            except Exception as e:
                                # 使用安全的翻译方法，避免_函数被污染
                                error_msg = self._safe_translate(TranslationKeys.ERROR_DECRYPTION_FAILED, error=str(e))
                                # 对于特定的InvalidTag异常，提供更明确的错误信息
                                if hasattr(e, '__class__') and e.__class__.__name__ == 'InvalidTag':
                                    error_msg = "解密失败：认证标签验证失败。请检查密钥和认证标签是否正确。"
                                self._show_error_message(error_msg)
                                return
                        else:
                            # 用户选择了密码模式，但文件是随机密钥格式
                            self._show_error_message(_("该文件是随机密钥格式，请使用密钥文件解密"))
                            return
            
            # 文件解密成功，安全地显示成功消息
            try:
                # 安全地构建成功消息 - 确保参数安全
                plaintext_file_safe = str(output_file) if output_file else "未知文件"
                algorithm_safe = str(algorithm_type.value) if hasattr(algorithm_type, 'value') else str(algorithm_type)
                
                # 使用绝对安全的翻译方法
                try:
                    message = self._safe_translate(TranslationKeys.SUCCESS_DECRYPTION,
                               plaintext_file=plaintext_file_safe,
                               algorithm=algorithm_safe)
                except Exception as translate_error:
                    # 如果翻译失败，使用硬编码消息
                    logging.warning(f"翻译成功消息失败，使用默认消息: {translate_error}")
                    message = f"解密成功！文件已保存到: {plaintext_file_safe}，算法: {algorithm_safe}"
                
                # 尝试显示成功消息，但不让失败影响解密成功状态
                self._show_success_message(message)
                
            except Exception as display_error:
                # 即使显示消息失败，也不影响解密成功的状态
                # 记录警告，但不传播异常
                logging.warning(f"显示成功消息时出错，但文件解密成功: {display_error}")
                # 尝试更新状态栏，表示解密完成
                if self.status_bar:
                    try:
                        self.status_bar.config(text="解密完成")
                    except:
                        pass
            
            # 安全返回
            logging.info(f"解密成功: {output_file}")
            return
            
        except Exception as e:
            # 记录完整的异常信息，包括堆栈跟踪
            import traceback
            full_error = traceback.format_exc()
            logging.error(f"解密失败，完整异常信息:\n{full_error}")
            
            # 安全地获取错误消息，处理翻译函数不可用的情况
            try:
                # 确保错误消息包含具体异常信息
                error_str = str(e) if str(e) else type(e).__name__
                error_msg = self._safe_translate(TranslationKeys.ERROR_DECRYPTION_FAILED, error=error_str)
                self._show_error_message(error_msg)
            except Exception as translate_error:
                # 如果连错误消息都显示失败，使用默认消息并记录详细错误
                logging.error(f"显示错误消息时出错: {translate_error}")
                logging.error(f"原始解密异常: {e}")
                if self.status_bar:
                    try:
                        self.status_bar.config(text=f"解密失败: {error_str[:100]}")
                    except:
                        pass
    
    def _open_settings(self):
        """打开设置对话框"""
        # 导入设置对话框类
        try:
            from settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.root, self)
            dialog.run()
        except ImportError as e:
            # 如果导入失败，显示错误消息
            self._show_error_message(_("无法加载设置模块: {error}", error=str(e)))
        except Exception as e:
            self._show_error_message(_("打开设置时出错: {error}", error=str(e)))
    
    def _change_theme(self, theme):
        """更改主题 - 安全版本，避免影响其他窗口（如设置对话框）"""
        try:
            # 设置主题管理器
            self.theme_manager.set_theme(theme)
            
            # 应用主题到主窗口（不递归到其他窗口）
            apply_theme_to_window(self.root)
            
            # 特别处理自定义菜单栏：更新菜单颜色
            if hasattr(self, 'menu_bar') and self.menu_bar:
                try:
                    # 调用自定义菜单栏的颜色更新方法
                    self.menu_bar.update_colors()
                    
                    # 同时应用主题管理器到菜单栏组件（安全地）
                    self.theme_manager.apply_to_widget(self.menu_bar)
                except Exception as e:
                    logging.error(f"更新菜单栏颜色时出错: {e}")
            
            # 更新UI状态（只影响主窗口的部件）
            self.update_ui_state()
            
            # 记录主题变更
            logging.info(f"主题已切换到: {theme}")
            
        except Exception as e:
            # 安全地显示错误消息，避免进一步异常
            try:
                error_msg = f"更改主题失败: {str(e)}"
                self._show_error_message(_("更改主题失败: {error}", error=str(e)))
            except Exception as inner_e:
                logging.error(f"显示主题更改错误消息时出错: {inner_e}")
    
    def _change_language(self, language_code):
        """更改界面语言"""
        try:
            self.translator.set_language(language_code)
            # 重新加载界面
            self._reload_ui()
        except Exception as e:
            self._show_error_message(_("更改语言失败: {error}", error=str(e)))
    
    def _reload_ui(self):
        """重新加载UI以应用新的语言设置 - 安全版本，不会销毁Toplevel窗口（如设置对话框）"""
        try:
            # 记录当前打开的Toplevel窗口
            toplevel_windows = []
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Toplevel):
                    toplevel_windows.append(widget)
                    logging.debug(f"检测到Toplevel窗口: {widget}")
            
            # 只销毁非Toplevel的子部件
            for widget in self.root.winfo_children():
                if not isinstance(widget, tk.Toplevel):
                    try:
                        widget.destroy()
                    except tk.TclError as e:
                        logging.debug(f"销毁部件时出错（可能已销毁）: {e}")
            
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
            
            # 记录重新加载完成
            logging.info(f"UI重新加载完成，保留了 {len(toplevel_windows)} 个Toplevel窗口")
            
        except Exception as e:
            logging.error(f"重新加载UI时出错: {e}")
            # 尝试恢复，即使出错也继续运行
            try:
                self._show_error_message(_("重新加载UI时出错: {error}", error=str(e)))
            except:
                pass
    
    def _show_about(self):
        """显示关于对话框"""
        # 安全地获取标题
        try:
            title = _("关于")
        except (NameError, AttributeError):
            title = "关于"
            
        # 尝试从version_info模块获取版本信息
        try:
            from version_info import get_version_string, get_version_info
            version_string = get_version_string()
            version_info = get_version_info()
        except ImportError:
            # 如果version_info模块不可用，使用默认值
            version_string = "1.0"
            version_info = {"version": version_string}
        
        # 获取构建信息（如果可用）
        build_date = version_info.get('build_date', 'Unknown')
        commit_hash = version_info.get('commit_hash', 'Unknown')
        
        about_text = f"""Cipher - 文件加密工具
版本: {version_string}
支持算法: OTP, AES256-GCM
语言: {self.translator.get_current_language_display_name()}
配置文件: {self.config_manager.config_file}
构建日期: {build_date}
提交哈希: {commit_hash}
        
版权所有 © 2026 miniCipher项目"""
        
        self.message_box.show_info(title, about_text)
    
    def restart_ui(self):
        """重启UI界面，应用新的语言和主题设置
        
        此方法由设置对话框调用，用于在更改语言或主题后重启界面
        """
        try:
            # 记录重启开始
            logging.info("开始重启UI界面...")
            
            # 获取当前配置
            current_language = self.config_manager.get_language()
            current_theme = self.config_manager.get_theme()
            
            # 记录当前设置
            logging.info(f"重启UI设置 - 语言: {current_language}, 主题: {current_theme}")
            
            # 首先更改语言设置，这会更新翻译器并重新加载界面
            # _change_language方法会调用_translator.set_language()然后_reload_ui()
            self._change_language(current_language)
            
            # 然后应用主题更改（_change_language中的_reload_ui可能不会重新应用主题到所有组件）
            self._change_theme(current_theme)
            
            # 记录重启完成
            logging.info("UI界面重启完成")
            
            # 显示成功消息（可选，但可能干扰用户体验）
            # self._show_success_message("界面重启完成")
            
        except Exception as e:
            # 记录错误，但不显示错误消息避免干扰用户
            logging.error(f"重启UI界面时出错: {e}")
            import traceback
            traceback.print_exc()
            # 尝试恢复：至少重新加载界面
            try:
                # 尝试使用传统方式恢复：重新加载界面和应用主题
                self._reload_ui()
                self._change_theme(current_theme)
            except Exception as inner_e:
                logging.error(f"恢复界面时也出错: {inner_e}")
    
    def run(self):
        """运行GUI"""
        logging.info("启动CipherGUI主窗口")
        self.root.mainloop()

def main():
    """主函数"""
    app = CipherGUI()
    app.run()

if __name__ == "__main__":
    main()