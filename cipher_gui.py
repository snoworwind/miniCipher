"""
文件加密/解密GUI工具 - 稳定版
支持多种加密算法：OTP和AES256-GCM
改进版：解决UI稳定性问题，增强错误处理
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class CipherGUI:
    """加密工具GUI主类 - 稳定版本"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("文件加密/解密工具 - Cipher")
        
        # 设置窗口最小尺寸
        self.root.minsize(800, 600)
        
        # 初始化所有UI组件变量
        self._init_ui_variables()
        
        # 一次性构建完整UI，避免延迟加载导致的闪烁
        self.setup_complete_ui()
        
        # 初始UI状态更新
        self.update_ui_state()
    
    def _init_ui_variables(self):
        """初始化所有UI组件变量，确保安全引用"""
        # 算法选择相关
        self.algorithm_var = tk.StringVar(value="OTP")
        self.key_type_var = tk.StringVar(value="random")
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
    
    def setup_complete_ui(self):
        """设置完整的用户界面（一次性构建）"""
        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 算法选择部分
        frame_algorithm = tk.LabelFrame(main_container, text="算法设置")
        frame_algorithm.pack(fill="x", padx=5, pady=5)
        
        # 算法选择
        tk.Label(frame_algorithm, text="加密算法：").grid(row=0, column=0, padx=5, pady=10, sticky="w")
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
        tk.Label(frame_algorithm, text="密钥类型：").grid(row=0, column=2, padx=5, pady=10, sticky="w")
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
        tk.Label(frame_algorithm, text="密码：").grid(row=0, column=4, padx=5, pady=10, sticky="w")
        self.password_entry = tk.Entry(frame_algorithm, width=20, show="*")
        self.password_entry.grid(row=0, column=5, padx=5, pady=10)
        
        # 算法信息标签
        self.algorithm_info = tk.Label(frame_algorithm, text="Cipher文件加密工具 - 选择算法开始", 
                                      font=("Arial", 10), fg="blue")
        self.algorithm_info.grid(row=1, column=0, columnspan=6, padx=5, pady=5)
        
        # 创建加密和解密框架的容器
        frames_container = ttk.Frame(main_container)
        frames_container.pack(fill="both", expand=True, pady=10)
        
        # 加密部分
        frame_encrypt = tk.LabelFrame(frames_container, text="加密")
        frame_encrypt.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self._setup_encrypt_frame(frame_encrypt)
        
        # 解密部分
        frame_decrypt = tk.LabelFrame(frames_container, text="解密")
        frame_decrypt.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self._setup_decrypt_frame(frame_decrypt)
        
        # 状态栏
        self.status_bar = tk.Label(self.root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始化事件绑定
        self.on_algorithm_changed()
    
    def _setup_encrypt_frame(self, frame):
        """设置加密部分的UI"""
        # 输入文件
        tk.Label(frame, text="输入文件路径：").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_input_file = tk.Entry(frame, width=50)
        self.entry_input_file.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(frame, text="浏览", command=lambda: self.browse_file(self.entry_input_file), 
                 bg="#e0e0e0").grid(row=0, column=2, padx=10, pady=10)
        
        # 输出目录
        tk.Label(frame, text="输出目录路径：").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_output_dir = tk.Entry(frame, width=50)
        self.entry_output_dir.grid(row=1, column=1, padx=10, pady=10)
        tk.Button(frame, text="浏览", command=lambda: self.browse_directory(self.entry_output_dir),
                 bg="#e0e0e0").grid(row=1, column=2, padx=10, pady=10)
        
        # 加密按钮
        tk.Button(frame, text="开始加密", command=self.encrypt, 
                 bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                 padx=20, pady=10).grid(row=2, column=0, columnspan=3, pady=20)
        
        # 添加一些提示信息
        tk.Label(frame, text="提示：", font=("Arial", 10, "bold"), fg="#666").grid(row=3, column=0, sticky="w", padx=10)
        tk.Label(frame, text="• 支持所有文件类型\n• 输出文件为.enc格式\n• 密钥文件与密文文件一同保存", 
                justify="left", fg="#666").grid(row=3, column=1, columnspan=2, sticky="w", padx=10)
    
    def _setup_decrypt_frame(self, frame):
        """设置解密部分的UI"""
        # 输入密文文件
        tk.Label(frame, text="输入密文路径：").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_input_cipher = tk.Entry(frame, width=50)
        self.entry_input_cipher.grid(row=0, column=1, padx=10, pady=10)
        tk.Button(frame, text="浏览", command=lambda: self.browse_file(self.entry_input_cipher),
                 bg="#e0e0e0").grid(row=0, column=2, padx=10, pady=10)
        
        # 密钥文件（仅OTP和随机密钥AES）
        tk.Label(frame, text="密钥文件路径：").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_key_file = tk.Entry(frame, width=50)
        self.entry_key_file.grid(row=1, column=1, padx=10, pady=10)
        tk.Button(frame, text="浏览", command=lambda: self.browse_file(self.entry_key_file),
                 bg="#e0e0e0").grid(row=1, column=2, padx=10, pady=10)
        
        # 解密密码（密码模式AES）
        tk.Label(frame, text="解密密码：").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_decrypt_password = tk.Entry(frame, width=50, show="*")
        self.entry_decrypt_password.grid(row=2, column=1, padx=10, pady=10)
        
        # 输出目录
        tk.Label(frame, text="输出目录路径：").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.entry_decrypt_output = tk.Entry(frame, width=50)
        self.entry_decrypt_output.grid(row=3, column=1, padx=10, pady=10)
        tk.Button(frame, text="浏览", command=lambda: self.browse_directory(self.entry_decrypt_output),
                 bg="#e0e0e0").grid(row=3, column=2, padx=10, pady=10)
        
        # 解密按钮
        tk.Button(frame, text="开始解密", command=self.decrypt,
                 bg="#2196F3", fg="white", font=("Arial", 12, "bold"),
                 padx=20, pady=10).grid(row=4, column=0, columnspan=3, pady=20)
        
        # 添加一些提示信息
        tk.Label(frame, text="提示：", font=("Arial", 10, "bold"), fg="#666").grid(row=5, column=0, sticky="w", padx=10)
        tk.Label(frame, text="• 支持OTP和AES256-GCM算法\n• 密码模式无需密钥文件\n• 输出为原始文件格式", 
                justify="left", fg="#666").grid(row=5, column=1, columnspan=2, sticky="w", padx=10)
    
    
    def on_algorithm_changed(self, event=None):
        """算法选择变更处理"""
        algorithm = self.algorithm_var.get()
        if algorithm == "OTP":
            self.algorithm_info.config(text="OTP: 一次性密码本，密钥长度等于文件长度")
            # OTP只支持随机密钥
            self.key_type_var.set("random")
            self.key_type_combo.config(state="disabled")
        else:  # AES256
            self.algorithm_info.config(text="AES256-GCM: 高级加密标准，256位密钥，GCM模式")
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
                    self.algorithm_info.config(text="OTP: 一次性密码本，密钥长度等于文件长度")
                else:
                    self.algorithm_info.config(text="AES256-GCM: 高级加密标准，256位密钥，GCM模式")
                    
        except Exception as e:
            # 安全地处理UI状态更新错误
            if self.status_bar:
                self.status_bar.config(text=f"UI状态更新错误: {str(e)}")
    
    def browse_file(self, entry):
        """文件选择对话框"""
        file_path = filedialog.askopenfilename()
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)
    
    def browse_directory(self, entry):
        """目录选择对话框"""
        directory_path = filedialog.askdirectory()
        if directory_path:
            entry.delete(0, tk.END)
            entry.insert(0, directory_path)
    
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
                self._show_error_message(f"导入加密模块失败: {e}")
                return False
        return True
    
    def _validate_password_strength(self, password):
        """验证密码强度"""
        if not password:
            return False, "密码不能为空"
        
        if len(password) < 8:
            return False, "密码至少需要8个字符"
        
        # 检查密码复杂度
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "密码应包含大小写字母和数字"
        
        return True, "密码强度合格"
    
    def _show_error_message(self, message):
        """显示错误消息"""
        messagebox.showerror("错误", message)
        if self.status_bar:
            self.status_bar.config(text=f"错误: {message[:50]}...")
    
    def _show_success_message(self, message):
        """显示成功消息"""
        messagebox.showinfo("成功", message)
        if self.status_bar:
            self.status_bar.config(text="操作成功完成")
    
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
                self._show_error_message("请输入要加密的文件路径")
                return
            
            if not output_dir:
                self._show_error_message("请输入输出目录路径")
                return
            
            # 检查文件是否存在
            if not os.path.exists(input_file):
                self._show_error_message(f"文件不存在: {input_file}")
                return
            
            # 对于密码模式，验证密码强度
            if algorithm == "AES256" and key_type == "password":
                if not password:
                    self._show_error_message("密码模式需要输入密码")
                    return
                
                # 验证密码强度
                is_valid, msg = self._validate_password_strength(password)
                if not is_valid:
                    self._show_error_message(f"密码强度不足: {msg}")
                    return
            
            # 创建输出目录
            try:
                os.makedirs(output_dir, exist_ok=True)
            except PermissionError as e:
                self._show_error_message(f"无法创建输出目录: {e}")
                return
            
            # 读取文件
            try:
                with open(input_file, 'rb') as f:
                    plaintext = f.read()
            except IOError as e:
                self._show_error_message(f"读取文件失败: {e}")
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
                self._show_error_message(f"加密过程出错: {e}")
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
            message = f"加密完成！\n密文文件：{output_file}\n"
            if result.key_type == self._KeyType.RANDOM:
                message += f"密钥文件：{key_file}\n"
            else:
                message += "密码模式：请妥善保管密码\n"

            message += f"算法：{algorithm}\n密钥类型：{key_type}"
            self._show_success_message(message)
            self.status_bar.config(text=f"加密完成：{base_name}")
            
        except FileNotFoundError as e:
            messagebox.showerror("错误", f"文件未找到：{str(e)}")
            self.status_bar.config(text=f"文件未找到：{os.path.basename(str(e))}")
        except PermissionError as e:
            messagebox.showerror("错误", f"权限错误：{str(e)}")
            self.status_bar.config(text="权限错误，无法访问文件")
        except IOError as e:
            messagebox.showerror("错误", f"文件读写错误：{str(e)}")
            self.status_bar.config(text="文件读写错误")
        except ValueError as e:
            messagebox.showerror("错误", f"参数错误：{str(e)}")
            self.status_bar.config(text=f"参数错误：{str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"加密失败：{str(e)}")
            self.status_bar.config(text=f"加密失败：{str(e)}")
    
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
                self._show_error_message("请输入要解密的密文文件路径")
                return
            
            if not output_dir:
                self._show_error_message("请输入输出目录路径")
                return
            
            # 检查文件是否存在
            if not os.path.exists(input_file):
                self._show_error_message(f"文件不存在: {input_file}")
                return
            
            # 检测算法
            try:
                algorithm_type = self._FileFormatHandler.detect_algorithm(input_file)
            except Exception as e:
                self._show_error_message(f"检测算法失败: {e}")
                return
            
            # 读取文件
            if algorithm_type == self._AlgorithmType.OTP:
                # OTP解密
                try:
                    ciphertext, _ = self._FileFormatHandler.read_otp_file(input_file)
                except ValueError as e:
                    self._show_error_message(f"读取OTP文件失败: {e}")
                    return
                
                # 获取密钥文件路径
                key_file = self.entry_key_file.get().strip()
                if not key_file:
                    self._show_error_message("OTP解密需要密钥文件")
                    return
                
                # 检查密钥文件是否存在
                if not os.path.exists(key_file):
                    self._show_error_message(f"密钥文件不存在: {key_file}")
                    return
                
                # 读取密钥
                try:
                    with open(key_file, 'r') as f:
                        key_hex = f.read().strip()
                        key = bytes.fromhex(key_hex)
                except (FileNotFoundError, ValueError) as e:
                    self._show_error_message(f"读取密钥文件失败: {e}")
                    return
                
                # 解密
                cipher_algorithm = self._get_algorithm(algorithm_type)
                try:
                    result = cipher_algorithm.decrypt(ciphertext, key=key)
                except ValueError as e:
                    self._show_error_message(f"OTP解密失败: {e}")
                    return
                
            else:  # AES256
                # 先读取文件头判断是哪种AES格式
                try:
                    with open(input_file, 'rb') as f:
                        header = f.read(4)
                except IOError as e:
                    self._show_error_message(f"读取文件失败: {e}")
                    return
                
                if header == b'AES\x01':
                    # 密码模式格式（带盐值）
                    try:
                        ciphertext, salt, iv, tag, _ = self._FileFormatHandler.read_aes_file_with_salt(input_file)
                    except ValueError as e:
                        self._show_error_message(f"读取AES密码格式文件失败: {e}")
                        return
                    
                    # 密码模式需要密码
                    password = self.entry_decrypt_password.get().strip()
                    if not password:
                        self._show_error_message("AES密码解密需要密码")
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
                        self._show_error_message(f"AES密码解密失败: {e}")
                        return
                        
                else:
                    # 随机密钥模式格式（标准AES格式）
                    try:
                        ciphertext, iv, tag, _ = self._FileFormatHandler.read_aes_file(input_file)
                    except ValueError as e:
                        self._show_error_message(f"读取AES文件失败: {e}")
                        return
                    
                    # 判断密钥类型（通过UI状态）
                    algorithm = self.algorithm_var.get()
                    key_type = self.key_type_var.get() if algorithm == "AES256" else "random"
                    
                    if key_type == "random":
                        # 随机密钥模式
                        key_file = self.entry_key_file.get().strip()
                        if not key_file:
                            self._show_error_message("AES随机密钥解密需要密钥文件")
                            return
                        
                        # 检查密钥文件是否存在
                        if not os.path.exists(key_file):
                            self._show_error_message(f"密钥文件不存在: {key_file}")
                            return
                        
                        try:
                            with open(key_file, 'rb') as f:
                                key = f.read()
                        except IOError as e:
                            self._show_error_message(f"读取密钥文件失败: {e}")
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
                            self._show_error_message(f"AES随机密钥解密失败: {e}")
                            return
                    else:
                        # 用户选择了密码模式，但文件是随机密钥格式
                        self._show_error_message("该文件是随机密钥格式，请使用密钥文件解密")
                        return
            
            # 创建输出目录
            try:
                os.makedirs(output_dir, exist_ok=True)
            except PermissionError as e:
                self._show_error_message(f"无法创建输出目录: {e}")
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
                self._show_error_message(f"保存解密文件失败: {e}")
                return
            
            # 显示成功消息
            message = f"解密完成！\n明文文件：{output_file}\n算法：{algorithm_type.value}"
            self._show_success_message(message)
            self.status_bar.config(text=f"解密完成：{base_name}")
            
        except Exception as e:
            self._show_error_message(f"解密失败: {e}")
            if self.status_bar:
                self.status_bar.config(text=f"解密失败: {str(e)[:50]}...")
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()

def main():
    """主函数"""
    app = CipherGUI()
    app.run()

if __name__ == "__main__":
    main()