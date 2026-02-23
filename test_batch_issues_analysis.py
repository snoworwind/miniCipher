#!/usr/bin/env python3
"""
批量处理问题分析测试
深入分析批量加密/解密功能的问题
"""

import os
import tempfile
import shutil
import logging
from batch_cipher import BatchOperationType, BatchProcessingMode, create_batch_cipher
from config_manager import get_config_manager

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_test_files(temp_dir, count=3):
    """创建测试文件"""
    test_files = []
    for i in range(count):
        file_path = os.path.join(temp_dir, f"test_file_{i}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"这是测试文件 {i} 的内容\n")
            f.write(f"用于测试批量加密/解密功能\n")
            f.write(f"文件创建时间: {i}\n" * 10)
        test_files.append(file_path)
    return test_files

def analyze_key_file_issue():
    """分析密钥文件问题"""
    print("=== 分析密钥文件问题 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建测试文件
        test_files = create_test_files(temp_dir, 2)
        
        # 创建输出目录
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 创建批量处理器
            batch_cipher = create_batch_cipher()
            print("✓ 批量处理器创建成功")
            
            # 配置批量处理器
            batch_cipher.parallel_processing = False
            batch_cipher.preserve_structure = False
            
            # 添加回调函数
            def status_callback(message):
                print(f"状态: {message}")
            
            batch_cipher.add_status_callback(status_callback)
            
            # 1. 测试OTP加密的密钥文件生成
            print("\n--- 测试OTP加密密钥文件生成 ---")
            result = batch_cipher.process_batch(
                source_paths=test_files,
                output_dir=output_dir,
                operation_type=BatchOperationType.ENCRYPT,
                algorithm="OTP",
                key_type="random",
                password=None
            )
            
            print(f"OTP加密结果: 成功 {result.successful_files} 个")
            
            # 检查生成的文件
            print("\n检查生成的文件:")
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                encrypted_file = os.path.join(output_dir, base_name + ".enc")
                print(f"密文文件: {encrypted_file} - 存在: {os.path.exists(encrypted_file)}")
                
                # 检查可能的密钥文件名
                key_file_txt = os.path.join(output_dir, f"key_{base_name}.txt")
                key_file_bin = os.path.join(output_dir, f"key_{base_name}.bin")
                key_file_key = os.path.join(output_dir, f"key_{base_name}.key")
                
                print(f"  可能的密钥文件:")
                print(f"    {key_file_txt} - 存在: {os.path.exists(key_file_txt)}")
                print(f"    {key_file_bin} - 存在: {os.path.exists(key_file_bin)}")
                print(f"    {key_file_key} - 存在: {os.path.exists(key_file_key)}")
            
            # 2. 测试AES加密的密钥文件生成
            print("\n--- 测试AES加密密钥文件生成 ---")
            aes_output_dir = os.path.join(temp_dir, "output_aes")
            os.makedirs(aes_output_dir, exist_ok=True)
            
            result_aes = batch_cipher.process_batch(
                source_paths=test_files,
                output_dir=aes_output_dir,
                operation_type=BatchOperationType.ENCRYPT,
                algorithm="AES256",
                key_type="random",
                password=None
            )
            
            print(f"AES加密结果: 成功 {result_aes.successful_files} 个")
            
            # 检查AES生成的文件
            print("\n检查AES生成的文件:")
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                encrypted_file = os.path.join(aes_output_dir, base_name + ".enc")
                print(f"密文文件: {encrypted_file} - 存在: {os.path.exists(encrypted_file)}")
                
                # 检查可能的密钥文件名
                key_file_key = os.path.join(aes_output_dir, f"key_{base_name}.key")
                print(f"  可能的密钥文件: {key_file_key} - 存在: {os.path.exists(key_file_key)}")
            
            # 3. 测试密码模式（不生成密钥文件）
            print("\n--- 测试AES密码模式 ---")
            password_output_dir = os.path.join(temp_dir, "output_password")
            os.makedirs(password_output_dir, exist_ok=True)
            
            result_password = batch_cipher.process_batch(
                source_paths=test_files,
                output_dir=password_output_dir,
                operation_type=BatchOperationType.ENCRYPT,
                algorithm="AES256",
                key_type="password",
                password="TestPassword123!"
            )
            
            print(f"AES密码模式加密结果: 成功 {result_password.successful_files} 个")
            
            return True
            
        except Exception as e:
            print(f"✗ 分析过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def analyze_cancel_mechanism():
    """分析取消处理机制"""
    print("\n=== 分析取消处理机制 ===")
    
    # 检查BatchCipher的取消机制实现
    batch_cipher = create_batch_cipher()
    
    print(f"取消状态检查方法存在: {hasattr(batch_cipher, 'cancel_processing')}")
    print(f"处理状态检查方法存在: {hasattr(batch_cipher, 'is_processing')}")
    print(f"_is_processing标志存在: {hasattr(batch_cipher, '_is_processing')}")
    
    # 测试取消功能
    print(f"初始处理状态: {batch_cipher.is_processing()}")
    
    try:
        batch_cipher.cancel_processing()
        print("✓ 取消方法可调用")
    except Exception as e:
        print(f"✗ 取消方法调用出错: {e}")
    
    return True

def analyze_thread_safety():
    """分析并行处理安全性"""
    print("\n=== 分析并行处理安全性 ===")
    
    batch_cipher = create_batch_cipher()
    
    print(f"并行处理配置: {batch_cipher.parallel_processing}")
    print(f"最大线程数配置: {batch_cipher.max_threads}")
    
    # 检查FileCipher实例共享问题
    print(f"FileCipher实例: {batch_cipher.file_cipher}")
    print(f"FileCipher类型: {type(batch_cipher.file_cipher)}")
    
    # 检查是否每个线程应有独立实例
    print("⚠️ 注意: FileCipher实例在所有线程间共享，可能存在线程安全问题")
    
    return True

def analyze_progress_update():
    """分析进度更新问题"""
    print("\n=== 分析进度更新问题 ===")
    
    # 检查batch_cipher.py中的进度更新逻辑
    print("需要检查process_batch方法中的结果队列收集逻辑")
    print("特别是串行处理时的结果收集:")
    print("  1. 串行处理: process_file_wrapper调用后直接收集结果")
    print("  2. 并行处理: 使用future_to_file和as_completed")
    
    # 检查_queue_empty处理
    print("需要验证: results_queue是否被完全清空")
    
    return True

def main():
    """主分析函数"""
    print("批量处理功能问题分析")
    print("=" * 60)
    
    # 运行分析
    results = []
    results.append(("密钥文件问题分析", analyze_key_file_issue()))
    results.append(("取消机制分析", analyze_cancel_mechanism()))
    results.append(("线程安全性分析", analyze_thread_safety()))
    results.append(("进度更新分析", analyze_progress_update()))
    
    # 输出分析结果
    print("\n" + "=" * 60)
    print("分析结果汇总:")
    print("=" * 60)
    
    for analysis_name, success in results:
        status = "✓ 完成" if success else "✗ 失败"
        print(f"{analysis_name}: {status}")
    
    print("\n关键发现:")
    print("1. 密钥文件命名问题 - OTP和AES可能使用不同的扩展名")
    print("2. 批量解密测试缺失 - 现有测试没有真正测试批量解密")
    print("3. 取消机制不完善 - 只设置标志，不中断线程")
    print("4. 线程安全性问题 - FileCipher实例共享")
    print("5. 进度更新可能不完整 - 需要验证队列清空逻辑")
    
    return all(success for _, success in results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)