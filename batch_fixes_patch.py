#!/usr/bin/env python3
"""
批量处理功能修复补丁
这个文件包含修复代码，可以直接应用到batch_cipher.py
"""

import os
import logging
import threading
from typing import List, Optional
from pathlib import Path

def apply_find_matching_key_file_fix():
    """为BatchCipher类添加_find_matching_key_file方法"""
    
    fix_code = '''
    def _find_matching_key_file(self, input_path: str, output_dir: str, 
                              algorithm: str, key_type: str) -> Optional[str]:
        """查找与输入文件匹配的密钥文件
        
        参数:
            input_path: 输入文件路径（明文或密文文件）
            output_dir: 输出目录（加密文件保存的目录）
            algorithm: 算法名称
            key_type: 密钥类型
            
        返回:
            Optional[str]: 找到的密钥文件路径，如果未找到则返回None
        """
        # 获取输入文件的基本名称（不带扩展名）
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        
        # 如果是密文文件，尝试去除.enc扩展名
        if name.endswith('.enc'):
            name = name[:-4]
        elif ext == '.enc':
            name = name  # 保持原样
        
        # 根据算法和密钥类型搜索可能的密钥文件名模式
        possible_key_files = []
        
        if algorithm == "OTP":
            # OTP可能的密钥文件模式
            possible_key_files.extend([
                os.path.join(output_dir, f"key_{name}.txt"),    # 十六进制文本格式
                os.path.join(output_dir, f"key_{name}.bin"),    # 二进制格式
                os.path.join(output_dir, f"key_{name}.key"),    # 通用密钥格式
                os.path.join(output_dir, f"{name}.key"),        # 简化的密钥文件名
                os.path.join(os.path.dirname(input_path), f"key_{name}.txt"),  # 输入文件目录
                os.path.join(os.path.dirname(input_path), f"key_{name}.bin"),  # 输入文件目录
            ])
            
            # 检查当前目录（output_dir）下所有可能的密钥文件
            for filename in os.listdir(output_dir):
                # 模式匹配：key_<name>.* 或 <name>.*.key
                if filename.startswith(f"key_{name}."):
                    possible_key_files.append(os.path.join(output_dir, filename))
                elif f"_{name}." in filename and filename.endswith('.key'):
                    possible_key_files.append(os.path.join(output_dir, filename))
        
        else:  # AES256
            if key_type == "random":
                # AES随机密钥可能的文件模式
                possible_key_files.extend([
                    os.path.join(output_dir, f"key_{name}.key"),    # 标准密钥文件
                    os.path.join(output_dir, f"{name}.key"),        # 简化的密钥文件名
                    os.path.join(os.path.dirname(input_path), f"key_{name}.key"),  # 输入文件目录
                ])
                
                # 检查当前目录下所有可能的密钥文件
                for filename in os.listdir(output_dir):
                    if filename.endswith('.key') and name in filename:
                        possible_key_files.append(os.path.join(output_dir, filename))
        
        # 搜索可能的密钥文件
        for key_file in possible_key_files:
            if os.path.exists(key_file) and os.path.isfile(key_file):
                logging.debug(f"找到匹配的密钥文件: {key_file}")
                return key_file
        
        # 如果没有找到，尝试在父目录中搜索
        parent_dir = os.path.dirname(output_dir)
        if parent_dir and os.path.exists(parent_dir):
            # 搜索父目录中的密钥文件
            for filename in os.listdir(parent_dir):
                if algorithm == "OTP":
                    if filename.startswith(f"key_{name}.") or (f"_{name}." in filename and filename.endswith(('.txt', '.bin', '.key'))):
                        possible_key_files.append(os.path.join(parent_dir, filename))
                else:  # AES256
                    if filename.endswith('.key') and name in filename:
                        possible_key_files.append(os.path.join(parent_dir, filename))
        
        # 再次检查
        for key_file in possible_key_files:
            if os.path.exists(key_file) and os.path.isfile(key_file):
                logging.debug(f"在父目录中找到匹配的密钥文件: {key_file}")
                return key_file
        
        logging.warning(f"未找到与文件 {base_name} 匹配的密钥文件")
        return None
    '''
    
    return fix_code

def apply_cancel_processing_fix():
    """改进取消处理机制"""
    
    fix_code = '''
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
            files = self.collect_files(source_paths, mode)
            
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
    '''
    
    return fix_code

def create_test_key_file_handling():
    """创建密钥文件处理测试"""
    
    test_code = '''
def test_key_file_handling():
    """测试密钥文件处理功能"""
    import tempfile
    import shutil
    
    print("=== 测试密钥文件处理 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试文件
        test_files = []
        for i in range(2):
            file_path = os.path.join(temp_dir, f"test_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Test content {i}")
            test_files.append(file_path)
        
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建批量处理器
        batch_cipher = create_batch_cipher()
        
        # 测试密钥文件查找
        print("\\n1. 测试_find_matching_key_file方法:")
        
        # 创建测试密钥文件
        test_key_file = os.path.join(output_dir, "key_test_0.txt")
        with open(test_key_file, 'w') as f:
            f.write("test key content")
        
        # 测试查找
        found_key = batch_cipher._find_matching_key_file(
            test_files[0], output_dir, "OTP", "random"
        )
        print(f"找到密钥文件: {found_key}")
        assert found_key == test_key_file, f"密钥文件查找失败: {found_key}"
        
        # 测试加密时保存密钥文件
        print("\\n2. 测试加密时保存密钥文件:")
        batch_cipher.parallel_processing = False
        
        # 添加状态回调
        def status_callback(msg):
            if "批量处理统计报告" in msg:
                print(msg)
        
        batch_cipher.add_status_callback(status_callback)
        
        # 执行OTP加密
        result = batch_cipher.process_batch(
            source_paths=test_files,
            output_dir=output_dir,
            operation_type=BatchOperationType.ENCRYPT,
            algorithm="OTP",
            key_type="random"
        )
        
        print(f"OTP加密结果: {result.successful_files}/{result.total_files} 成功")
        
        # 检查是否生成了密钥文件
        print("\\n3. 检查生成的密钥文件:")
        key_files_found = 0
        for filename in os.listdir(output_dir):
            if filename.startswith("key_") and filename.endswith(('.txt', '.bin', '.key')):
                key_files_found += 1
                print(f"找到密钥文件: {filename}")
        
        print(f"总共找到 {key_files_found} 个密钥文件")
        
        # 测试批量解密
        print("\\n4. 测试批量解密:")
        decrypt_dir = os.path.join(temp_dir, "decrypt")
        os.makedirs(decrypt_dir, exist_ok=True)
        
        # 收集加密文件
        encrypted_files = []
        for file_path in test_files:
            base_name = os.path.basename(file_path)
            encrypted_file = os.path.join(output_dir, base_name + ".enc")
            if os.path.exists(encrypted_file):
                encrypted_files.append(encrypted_file)
        
        if encrypted_files:
            result = batch_cipher.process_batch(
                source_paths=encrypted_files,
                output_dir=decrypt_dir,
                operation_type=BatchOperationType.DECRYPT,
                algorithm="OTP",
                key_type="random"
            )
            
            print(f"OTP解密结果: {result.successful_files}/{result.total_files} 成功")
            
            # 检查解密文件
            print("\\n5. 检查解密文件:")
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                decrypted_file = os.path.join(decrypt_dir, base_name)
                if os.path.exists(decrypted_file):
                    with open(decrypted_file, 'r') as f:
                        content = f.read()
                    print(f"{decrypted_file}: 存在, 内容长度: {len(content)}")
                else:
                    print(f"{decrypted_file}: 不存在")
        
        print("\\n✓ 密钥文件处理测试完成")
        return True

if __name__ == "__main__":
    # 运行密钥文件处理测试
    try:
        test_key_file_handling()
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    '''
    
    return test_code

def main():
    """主函数"""
    print("批量处理功能修复补丁")
    print("=" * 60)
    
    print("修复内容:")
    print("1. 添加_find_matching_key_file()方法")
    print("2. 改进取消处理机制")
    print("3. 修复线程安全性问题")
    print("4. 创建密钥文件处理测试")
    
    print("\n使用方法:")
    print("1. 将_find_matching_key_file()方法添加到BatchCipher类")
    print("2. 更新__init__、cancel_processing和process_batch方法")
    print("3. 添加_process_single_file_with_cipher方法")
    print("4. 运行测试验证修复效果")
    
    print("\n生成的修复代码已保存到相应的变量中。")
    
    return True

if __name__ == "__main__":
    main()