#!/usr/bin/env python3
"""
批量加密/解密处理器模块
基于现有FileCipher API提供批量文件处理功能
支持多线程、进度跟踪、错误处理和统计报告
"""

import os
import logging
import threading
import queue
import time
from typing import List, Dict, Tuple, Optional, Callable, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum

from cipher_algorithms import FileCipher, FileFormatHandler, AlgorithmType, KeyType
from config_manager import get_config_manager


class BatchOperationType(Enum):
    """批量操作类型"""
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"


class BatchProcessingMode(Enum):
    """批量处理模式"""
    FILES = "files"           # 处理多个文件
    FOLDER = "folder"         # 处理文件夹及其内容
    FOLDER_RECURSIVE = "folder_recursive"  # 递归处理文件夹


@dataclass
class BatchOperationResult:
    """批量操作结果"""
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_size_bytes: int = 0
    processed_size_bytes: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    
    @property
    def elapsed_time(self) -> float:
        """获取耗时（秒）"""
        return self.end_time - self.start_time if self.end_time > self.start_time else 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率（百分比）"""
        if self.total_files == 0:
            return 0.0
        return (self.successful_files / self.total_files) * 100
    
    @property
    def average_speed(self) -> float:
        """平均处理速度（字节/秒）"""
        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0.0
        return self.processed_size_bytes / elapsed


@dataclass
class FileOperationResult:
    """单个文件操作结果"""
    input_path: str
    output_path: str
    success: bool
    error_message: str = ""
    file_size: int = 0
    processing_time: float = 0.0


class BatchCipher:
    """批量加密/解密处理器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.file_cipher = FileCipher(self.config_manager)
        
        # 获取配置
        self.parallel_processing = self.config_manager.get("batch.parallel_processing", False)
        self.max_threads = self.config_manager.get("batch.max_threads", 4)
        self.preserve_structure = self.config_manager.get("batch.preserve_structure", True)
        
        # 状态跟踪
        self._is_processing = False
        self._progress_callbacks = []
        self._status_callbacks = []
        self._batch_progress_callbacks = []
        
        # 线程管理
        self._executor = None
        self._futures = []  # 跟踪所有Future对象
        self._lock = threading.Lock()  # 线程安全锁
    
    def add_progress_callback(self, callback: Callable[[int, int, str], None]):
        """添加进度回调函数
        
        参数:
            callback: 回调函数，接收(current, total, current_file)
        """
        self._progress_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable[[str], None]):
        """添加状态回调函数
        
        参数:
            callback: 回调函数，接收状态消息
        """
        self._status_callbacks.append(callback)
    
    def add_batch_progress_callback(self, callback: Callable[[Dict], None]):
        """添加批量处理进度回调函数
        
        参数:
            callback: 回调函数，接收进度信息字典
        """
        self._batch_progress_callbacks.append(callback)
    
    def _notify_progress(self, current: int, total: int, current_file: str):
        """通知进度更新"""
        for callback in self._progress_callbacks:
            try:
                callback(current, total, current_file)
            except Exception as e:
                logging.error(f"进度回调函数错误: {e}")
    
    def _notify_status(self, message: str):
        """通知状态更新"""
        for callback in self._status_callbacks:
            try:
                callback(message)
            except Exception as e:
                logging.error(f"状态回调函数错误: {e}")
    
    def _notify_batch_progress(self, progress_info: Dict):
        """通知批量处理进度更新"""
        for callback in self._batch_progress_callbacks:
            try:
                callback(progress_info)
            except Exception as e:
                logging.error(f"批量进度回调函数错误: {e}")
    
    def collect_files(self, source_paths: List[str], mode: BatchProcessingMode, 
                     operation_type: BatchOperationType = None) -> List[str]:
        """收集要处理的文件
        
        参数:
            source_paths: 源路径列表（文件或文件夹）
            mode: 处理模式
            operation_type: 操作类型（加密或解密），用于文件过滤
            
        返回:
            List[str]: 要处理的文件路径列表
        """
        files = []
        
        for source_path in source_paths:
            if not os.path.exists(source_path):
                self._notify_status(f"路径不存在: {source_path}")
                continue
            
            if os.path.isfile(source_path):
                # 单个文件
                files.append(source_path)
                self._notify_status(f"添加文件: {os.path.basename(source_path)}")
            elif os.path.isdir(source_path):
                # 文件夹
                if mode in [BatchProcessingMode.FOLDER, BatchProcessingMode.FOLDER_RECURSIVE]:
                    recursive = (mode == BatchProcessingMode.FOLDER_RECURSIVE)
                    for root, _, filenames in os.walk(source_path):
                        for filename in filenames:
                            file_path = os.path.join(root, filename)
                            files.append(file_path)
                        if not recursive:
                            break
                    self._notify_status(f"从文件夹添加 {len(files)} 个文件: {os.path.basename(source_path)}")
        
        # 根据操作类型过滤文件
        files = self._filter_files(files, operation_type)
        
        # 按大小排序，大文件优先（有助于并行处理）
        files.sort(key=lambda f: os.path.getsize(f) if os.path.exists(f) else 0, reverse=True)
        
        return files
    
    def _filter_files(self, files: List[str], operation_type: BatchOperationType = None) -> List[str]:
        """过滤文件列表，排除不需要的文件
        
        参数:
            files: 文件路径列表
            operation_type: 操作类型（加密或解密），用于文件过滤
        """
        filtered_files = []
        
        # 排除常见的不需要处理的文件
        exclude_extensions = {'.tmp', '.temp', '.swp', '.DS_Store', '.lnk'}
        exclude_names = {'thumbs.db', '.gitignore'}
        
        # 根据操作类型定义额外的排除条件
        if operation_type == BatchOperationType.DECRYPT:
            # 解密时排除密钥文件和其他非密文文件
            key_file_extensions = {'.key', '.txt', '.bin'}
            exclude_extensions.update(key_file_extensions)
        elif operation_type == BatchOperationType.ENCRYPT:
            # 加密时排除密文文件（避免重复加密）
            exclude_extensions.add('.enc')
        
        for file_path in files:
            try:
                if not os.path.isfile(file_path):
                    continue
                
                filename = os.path.basename(file_path)
                _, ext = os.path.splitext(filename)
                
                # 检查排除条件
                if ext.lower() in exclude_extensions:
                    if operation_type:
                        self._notify_status(f"跳过{operation_type.value}不需要的文件: {filename}")
                    continue
                if filename.lower() in exclude_names:
                    continue
                
                # 根据操作类型进行额外过滤
                if operation_type == BatchOperationType.DECRYPT:
                    # 解密时只处理.enc文件
                    if ext.lower() != '.enc' and not filename.lower().endswith('.enc'):
                        self._notify_status(f"解密时跳过非密文文件: {filename}")
                        continue
                elif operation_type == BatchOperationType.ENCRYPT:
                    # 加密时跳过已加密的文件（.enc）
                    if ext.lower() == '.enc' or filename.lower().endswith('.enc'):
                        self._notify_status(f"加密时跳过已加密文件: {filename}")
                        continue
                
                # 检查文件大小（跳过0字节文件）
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    self._notify_status(f"跳过空文件: {filename}")
                    continue
                
                filtered_files.append(file_path)
            except (OSError, PermissionError) as e:
                logging.warning(f"无法访问文件 {file_path}: {e}")
                self._notify_status(f"无法访问文件: {os.path.basename(file_path)}")
        
        logging.debug(f"文件过滤完成: 原始文件数={len(files)}, 过滤后={len(filtered_files)}, 操作类型={operation_type}")
        return filtered_files
    
    def _find_matching_key_file(self, input_path: str, output_dir: str, 
                              algorithm: str, key_type: str) -> Optional[str]:
        """查找与输入文件匹配的密钥文件
        
        参数:
            input_path: 输入文件路径（明文或密文文件）
            output_dir: 输出目录（解密文件的输出目录）
            algorithm: 算法名称
            key_type: 密钥类型
            
        返回:
            Optional[str]: 找到的密钥文件路径，如果未找到则返回None
        """
        # 获取输入文件的完整名称
        base_name = os.path.basename(input_path)
        
        # 处理文件名，提取原始文件名
        original_name = base_name
        # 如果文件名以.enc结尾，去除.enc扩展名
        if original_name.endswith('.enc'):
            original_name = original_name[:-4]
        
        logging.debug(f"查找密钥文件: 输入文件={base_name}, 原始名称={original_name}, 算法={algorithm}, 密钥类型={key_type}")
        
        # 获取输入文件所在目录（密钥文件可能在此目录中）
        input_dir = os.path.dirname(input_path)
        
        # 根据算法和密钥类型搜索可能的密钥文件名模式
        # 优先搜索输入文件所在目录，然后搜索输出目录
        search_dirs = [input_dir, output_dir]
        
        possible_key_files = []
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            if algorithm == "OTP":
                # OTP可能的密钥文件模式 - 新格式（包含完整文件名）
                possible_key_files.extend([
                    os.path.join(search_dir, f"key_{original_name}.txt"),    # 十六进制文本格式（新格式）
                    os.path.join(search_dir, f"key_{original_name}.bin"),    # 二进制格式（新格式）
                    os.path.join(search_dir, f"key_{original_name}.key"),    # 通用密钥格式（新格式）
                ])
                
                # 为了向后兼容，也尝试旧格式（不包含扩展名）
                # 提取基本名称（去除所有扩展名）
                base_name_no_ext = os.path.splitext(original_name)[0]
                possible_key_files.extend([
                    os.path.join(search_dir, f"key_{base_name_no_ext}.txt"),    # 旧格式十六进制文本
                    os.path.join(search_dir, f"key_{base_name_no_ext}.bin"),    # 旧格式二进制
                    os.path.join(search_dir, f"key_{base_name_no_ext}.key"),    # 旧格式通用密钥
                ])
                
                # 检查当前目录下所有可能的密钥文件
                for filename in os.listdir(search_dir):
                    file_lower = filename.lower()
                    # 新格式：key_<完整文件名>.*
                    if file_lower.startswith(f"key_{original_name.lower()}."):
                        possible_key_files.append(os.path.join(search_dir, filename))
                    # 旧格式：key_<基本名称>.*
                    elif file_lower.startswith(f"key_{base_name_no_ext.lower()}."):
                        possible_key_files.append(os.path.join(search_dir, filename))
                    # 其他可能的模式
                    elif f"_{original_name.lower()}." in file_lower and file_lower.endswith(('.txt', '.bin', '.key')):
                        possible_key_files.append(os.path.join(search_dir, filename))
            
            else:  # AES256
                if key_type == "random":
                    # AES随机密钥可能的文件模式 - 新格式（包含完整文件名）
                    possible_key_files.extend([
                        os.path.join(search_dir, f"key_{original_name}.key"),    # 新格式密钥文件
                    ])
                    
                    # 为了向后兼容，也尝试旧格式（不包含扩展名）
                    base_name_no_ext = os.path.splitext(original_name)[0]
                    possible_key_files.extend([
                        os.path.join(search_dir, f"key_{base_name_no_ext}.key"),    # 旧格式密钥文件
                    ])
                    
                    # 检查当前目录下所有可能的密钥文件
                    for filename in os.listdir(search_dir):
                        file_lower = filename.lower()
                        # 新格式：key_<完整文件名>.key
                        if file_lower == f"key_{original_name.lower()}.key":
                            possible_key_files.append(os.path.join(search_dir, filename))
                        # 旧格式：key_<基本名称>.key
                        elif file_lower == f"key_{base_name_no_ext.lower()}.key":
                            possible_key_files.append(os.path.join(search_dir, filename))
                        # 其他可能的匹配模式
                        elif file_lower.endswith('.key') and original_name.lower() in file_lower:
                            possible_key_files.append(os.path.join(search_dir, filename))
        
        # 去重并搜索可能的密钥文件（优先搜索输入目录中的文件）
        seen = set()
        for key_file in possible_key_files:
            if key_file in seen:
                continue
            seen.add(key_file)
            
            if os.path.exists(key_file) and os.path.isfile(key_file):
                logging.info(f"找到匹配的密钥文件: {key_file}")
                return key_file
        
        # 如果没有找到，尝试在父目录中搜索
        parent_dir = os.path.dirname(input_dir)
        if parent_dir and os.path.exists(parent_dir):
            logging.debug(f"尝试在父目录中搜索: {parent_dir}")
            
            if algorithm == "OTP":
                # 在父目录中搜索OTP密钥文件
                for filename in os.listdir(parent_dir):
                    file_lower = filename.lower()
                    if file_lower.startswith(f"key_{original_name.lower()}.") or \
                       file_lower.startswith(f"key_{base_name_no_ext.lower()}."):
                        key_file = os.path.join(parent_dir, filename)
                        if os.path.isfile(key_file):
                            logging.info(f"在父目录中找到匹配的密钥文件: {key_file}")
                            return key_file
            else:  # AES256
                if key_type == "random":
                    # 在父目录中搜索AES密钥文件
                    for filename in os.listdir(parent_dir):
                        file_lower = filename.lower()
                        if file_lower.endswith('.key') and (original_name.lower() in file_lower or base_name_no_ext.lower() in file_lower):
                            key_file = os.path.join(parent_dir, filename)
                            if os.path.isfile(key_file):
                                logging.info(f"在父目录中找到匹配的密钥文件: {key_file}")
                                return key_file
        
        logging.warning(f"未找到与文件 {base_name} 匹配的密钥文件")
        logging.debug(f"搜索了以下目录: {search_dirs}")
        logging.debug(f"搜索了以下模式: {list(seen)}")
        return None
    
    def _calculate_output_path(self, input_path: str, base_input_path: str, 
                              output_dir: str, operation_type: BatchOperationType) -> str:
        """计算输出文件路径
        
        参数:
            input_path: 输入文件路径
            base_input_path: 基础输入路径（用于保持目录结构）
            output_dir: 输出目录
            operation_type: 操作类型
            
        返回:
            str: 输出文件路径
        """
        # 获取文件名和扩展名
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        
        # 确定输出文件名
        if operation_type == BatchOperationType.ENCRYPT:
            output_filename = f"{name}{ext}.enc"
        else:  # DECRYPT
            # 尝试去除.enc扩展名
            if name.endswith('.enc'):
                output_filename = name[:-4] + ext
            elif ext == '.enc':
                output_filename = name
            else:
                output_filename = f"{name}_decrypted{ext}"
        
        # 如果保持目录结构，计算相对路径
        if self.preserve_structure and base_input_path:
            # 获取相对于基础路径的相对路径
            try:
                rel_path = os.path.relpath(os.path.dirname(input_path), base_input_path)
                # 如果相对路径不是当前目录，添加到输出路径
                if rel_path != '.':
                    output_subdir = os.path.join(output_dir, rel_path)
                    os.makedirs(output_subdir, exist_ok=True)
                    return os.path.join(output_subdir, output_filename)
            except ValueError:
                # 如果无法计算相对路径（跨磁盘），只使用文件名
                pass
        
        # 创建输出目录（如果不存在）
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, output_filename)
    
    def _process_single_file(self, input_path: str, output_path: str, 
                            operation_type: BatchOperationType, algorithm: str,
                            key_type: str, password: Optional[str] = None, 
                            key_path: Optional[str] = None) -> FileOperationResult:
        """处理单个文件
        
        参数:
            input_path: 输入文件路径
            output_path: 输出文件路径
            operation_type: 操作类型
            algorithm: 算法
            key_type: 密钥类型
            password: 密码（密码模式）
            key_path: 密钥文件路径（随机密钥模式）
            
        返回:
            FileOperationResult: 操作结果
        """
        start_time = time.time()
        file_size = os.path.getsize(input_path)
        
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 调用FileCipher API
            if operation_type == BatchOperationType.ENCRYPT:
                result = self.file_cipher.encrypt_file(
                    input_path=input_path,
                    output_path=output_path,
                    algorithm=algorithm,
                    key_type=key_type,
                    password=password
                )
            else:  # DECRYPT
                result = self.file_cipher.decrypt_file(
                    input_path=input_path,
                    output_path=output_path,
                    algorithm=algorithm,
                    key_type=key_type,
                    key_path=key_path,
                    password=password
                )
            
            processing_time = time.time() - start_time
            
            return FileOperationResult(
                input_path=input_path,
                output_path=output_path,
                success=True,
                file_size=file_size,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            logging.error(f"处理文件失败 {input_path}: {error_msg}")
            
            return FileOperationResult(
                input_path=input_path,
                output_path=output_path,
                success=False,
                error_message=error_msg,
                file_size=file_size,
                processing_time=processing_time
            )
    
    def _process_single_file_with_cipher(self, cipher_instance, input_path: str, output_path: str, 
                            operation_type: BatchOperationType, algorithm: str,
                            key_type: str, password: Optional[str] = None, 
                            key_path: Optional[str] = None) -> FileOperationResult:
        """使用指定的cipher实例处理单个文件"""
        start_time = time.time()
        file_size = os.path.getsize(input_path)
        
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 调用FileCipher API
            if operation_type == BatchOperationType.ENCRYPT:
                result = cipher_instance.encrypt_file(
                    input_path=input_path,
                    output_path=output_path,
                    algorithm=algorithm,
                    key_type=key_type,
                    password=password
                )
                
                # 保存密钥文件（如果需要）
                if result.get('key_file_needed', False) and result.get('key'):
                    key_dir = os.path.dirname(output_path)
                    base_name = os.path.basename(input_path)  # 完整的文件名，包括扩展名
                    
                    # 保存密钥文件（使用完整的文件名，包含扩展名）
                    key_file_path = cipher_instance.save_key(
                        key=result['key'],
                        output_dir=key_dir,
                        base_name=base_name,
                        algorithm=algorithm,
                        key_type=key_type
                    )
                    
                    if key_file_path:
                        logging.debug(f"密钥文件已保存: {key_file_path}")
            else:  # DECRYPT
                result = cipher_instance.decrypt_file(
                    input_path=input_path,
                    output_path=output_path,
                    algorithm=algorithm,
                    key_type=key_type,
                    key_path=key_path,
                    password=password
                )
            
            processing_time = time.time() - start_time
            
            return FileOperationResult(
                input_path=input_path,
                output_path=output_path,
                success=True,
                file_size=file_size,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            logging.error(f"处理文件失败 {input_path}: {error_msg}")
            
            return FileOperationResult(
                input_path=input_path,
                output_path=output_path,
                success=False,
                error_message=error_msg,
                file_size=file_size,
                processing_time=processing_time
            )
    
    def process_batch(self, source_paths: List[str], output_dir: str,
                     operation_type: BatchOperationType, algorithm: str,
                     key_type: str, password: Optional[str] = None,
                     key_path: Optional[str] = None,
                     mode: BatchProcessingMode = BatchProcessingMode.FILES) -> BatchOperationResult:
        """批量处理文件
        
        参数:
            source_paths: 源路径列表
            output_dir: 输出目录
            operation_type: 操作类型
            algorithm: 算法
            key_type: 密钥类型
            password: 密码（密码模式）
            key_path: 密钥文件路径（随机密钥模式）
            mode: 处理模式
            
        返回:
            BatchOperationResult: 批量操作结果
        """
        if self._is_processing:
            raise RuntimeError("批量处理器已在运行中")
        
        # 重置状态
        with self._lock:
            self._is_processing = True
            self._futures.clear()
        
        start_time = time.time()
        
        try:
            # 收集文件
            self._notify_status("正在收集文件...")
            files = self.collect_files(source_paths, mode, operation_type)
            
            if not files:
                self._notify_status("未找到要处理的文件")
                return BatchOperationResult()
            
            total_files = len(files)
            self._notify_status(f"找到 {total_files} 个文件待处理")
            
            # 计算总大小
            total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
            
            # 确定基础路径（用于保持目录结构）
            base_input_path = None
            if self.preserve_structure and source_paths:
                # 如果有多个源路径，使用第一个文件夹作为基础
                for source_path in source_paths:
                    if os.path.isdir(source_path):
                        base_input_path = source_path
                        break
            
            # 准备结果跟踪
            batch_result = BatchOperationResult(
                total_files=total_files,
                total_size_bytes=total_size,
                start_time=start_time
            )
            
            # 创建结果队列
            results_queue = queue.Queue()
            
            # 定义处理函数
            def process_file_wrapper(file_path: str, index: int):
                """包装处理函数，用于并行处理"""
                try:
                    # 检查是否已取消
                    with self._lock:
                        if not self._is_processing:
                            return None
                    
                    output_path = self._calculate_output_path(
                        file_path, base_input_path, output_dir, operation_type
                    )
                    
                    # 通知进度
                    self._notify_progress(index, total_files, os.path.basename(file_path))
                    
                    # 对于解密操作，自动查找密钥文件
                    actual_key_path = key_path
                    if operation_type == BatchOperationType.DECRYPT and not actual_key_path:
                        actual_key_path = self._find_matching_key_file(
                            file_path, output_dir, algorithm, key_type
                        )
                        if actual_key_path:
                            logging.debug(f"自动找到密钥文件: {actual_key_path}")
                        else:
                            # 如果没有找到密钥文件，记录错误但继续处理其他文件
                            logging.warning(f"未找到密钥文件用于解密: {file_path}")
                    
                    # 为每个线程创建独立的FileCipher实例（线程安全）
                    thread_local_cipher = self._create_thread_safe_file_cipher()
                    
                    # 处理文件
                    result = self._process_single_file_with_cipher(
                        thread_local_cipher, file_path, output_path, operation_type, 
                        algorithm, key_type, password, actual_key_path
                    )
                    
                    results_queue.put(result)
                    
                except Exception as e:
                    logging.error(f"处理文件时发生错误 {file_path}: {e}")
                    result = FileOperationResult(
                        input_path=file_path,
                        output_path="",
                        success=False,
                        error_message=str(e),
                        file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    )
                    results_queue.put(result)
            
            # 并行或串行处理
            if self.parallel_processing and total_files > 1:
                self._notify_status(f"使用多线程处理（最大 {self.max_threads} 个线程）...")
                with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                    self._executor = executor
                    
                    # 提交所有任务
                    for i, file_path in enumerate(files, 1):
                        with self._lock:
                            if not self._is_processing:
                                break
                        
                        future = executor.submit(process_file_wrapper, file_path, i)
                        with self._lock:
                            self._futures.append(future)
                    
                    # 收集结果
                    for future in as_completed(self._futures):
                        try:
                            # 检查是否已取消
                            with self._lock:
                                if not self._is_processing:
                                    break
                            
                            result = results_queue.get(timeout=30)  # 增加超时时间
                            if result:
                                self._update_batch_result(batch_result, result)
                        except queue.Empty:
                            logging.warning("获取结果超时")
                        except Exception as e:
                            logging.error(f"收集结果时出错: {e}")
                    
                    # 清理Future列表
                    with self._lock:
                        self._futures.clear()
                    
                    self._executor = None
            else:
                self._notify_status("使用串行处理...")
                for i, file_path in enumerate(files, 1):
                    # 检查是否已取消
                    with self._lock:
                        if not self._is_processing:
                            break
                    
                    process_file_wrapper(file_path, i)
                    
                    # 收集结果
                    while not results_queue.empty():
                        try:
                            result = results_queue.get(timeout=5)
                            if result:
                                self._update_batch_result(batch_result, result)
                        except queue.Empty:
                            break
            
            # 收集剩余结果
            while not results_queue.empty():
                try:
                    result = results_queue.get(timeout=5)
                    if result:
                        self._update_batch_result(batch_result, result)
                except queue.Empty:
                    break
            
            # 完成
            batch_result.end_time = time.time()
            
            # 生成统计报告
            self._generate_statistics_report(batch_result)
            
            return batch_result
            
        finally:
            with self._lock:
                self._is_processing = False
                self._futures.clear()
                self._executor = None
    
    def _update_batch_result(self, batch_result: BatchOperationResult, 
                            file_result: FileOperationResult):
        """更新批量结果"""
        if file_result.success:
            batch_result.successful_files += 1
            batch_result.processed_size_bytes += file_result.file_size
        else:
            batch_result.failed_files += 1
            
        # 记录详细错误
        if not file_result.success:
            self._notify_status(f"文件处理失败: {os.path.basename(file_result.input_path)} - {file_result.error_message}")
    
    def _generate_statistics_report(self, batch_result: BatchOperationResult):
        """生成统计报告"""
        elapsed_time = batch_result.elapsed_time
        minutes, seconds = divmod(elapsed_time, 60)
        
        report = (
            f"\n=== 批量处理统计报告 ===\n"
            f"总文件数: {batch_result.total_files}\n"
            f"成功: {batch_result.successful_files}\n"
            f"失败: {batch_result.failed_files}\n"
            f"跳过: {batch_result.skipped_files}\n"
            f"成功率: {batch_result.success_rate:.1f}%\n"
            f"总大小: {batch_result.total_size_bytes:,} 字节 ({batch_result.total_size_bytes / 1024 / 1024:.2f} MB)\n"
            f"处理大小: {batch_result.processed_size_bytes:,} 字节 ({batch_result.processed_size_bytes / 1024 / 1024:.2f} MB)\n"
            f"耗时: {int(minutes)}分{seconds:.1f}秒\n"
            f"平均速度: {batch_result.average_speed / 1024 / 1024:.2f} MB/秒\n"
            f"========================\n"
        )
        
        logging.info(report)
        self._notify_status(report)
    
    def _create_thread_safe_file_cipher(self):
        """创建线程安全的FileCipher实例"""
        return FileCipher(self.config_manager)
    
    def cancel_processing(self):
        """取消正在进行的处理"""
        with self._lock:
            self._is_processing = False
            
            # 取消所有Future对象
            for future in self._futures:
                try:
                    future.cancel()
                except Exception as e:
                    logging.error(f"取消Future时出错: {e}")
            
            # 如果使用线程池执行器，尝试关闭它
            if self._executor:
                try:
                    self._executor.shutdown(wait=False, cancel_futures=True)
                except Exception as e:
                    logging.error(f"关闭线程池时出错: {e}")
            
            # 清空Future列表
            self._futures.clear()
        
        self._notify_status("批量处理已取消")
    
    def is_processing(self) -> bool:
        """检查是否正在处理"""
        return self._is_processing


# 便捷函数
def create_batch_cipher() -> BatchCipher:
    """创建批量处理器实例"""
    return BatchCipher()


if __name__ == "__main__":
    # 测试代码
    import tempfile
    
    print("=== 测试批量处理器 ===")
    
    # 创建测试目录和文件
    test_dir = tempfile.mkdtemp()
    print(f"测试目录: {test_dir}")
    
    # 创建测试文件
    test_files = []
    for i in range(3):
        test_file = os.path.join(test_dir, f"test_file_{i}.txt")
        with open(test_file, 'w') as f:
            f.write(f"这是测试文件 {i} 的内容")
        test_files.append(test_file)
        print(f"创建测试文件: {test_file}")
    
    # 创建批量处理器
    batch_cipher = create_batch_cipher()
    
    # 添加简单的回调函数
    def progress_callback(current, total, current_file):
        print(f"进度: {current}/{total} - {current_file}")
    
    def status_callback(message):
        print(f"状态: {message}")
    
    batch_cipher.add_progress_callback(progress_callback)
    batch_cipher.add_status_callback(status_callback)
    
    # 测试批量加密
    print("\n=== 测试批量加密 ===")
    output_dir = os.path.join(test_dir, "output")
    
    # 禁用并行处理进行测试
    batch_cipher.parallel_processing = False
    
    try:
        result = batch_cipher.process_batch(
            source_paths=[test_dir],
            output_dir=output_dir,
            operation_type=BatchOperationType.ENCRYPT,
            algorithm="AES256",
            key_type="password",
            password="testpassword123",
            mode=BatchProcessingMode.FOLDER
        )
        
        print(f"批量加密完成: {result.successful_files}/{result.total_files} 成功")
        
    except Exception as e:
        print(f"批量加密测试失败: {e}")
    
    print("\n=== 测试完成 ===")