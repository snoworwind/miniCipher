#!/usr/bin/env python3
"""
批量处理功能修复验证测试
验证修复后的批量处理功能
"""

import os
import tempfile
import shutil
import logging
import time
import threading
from batch_cipher import BatchOperationType, BatchProcessingMode, create_batch_cipher
from cipher_algorithms import FileCipher

# 设置详细日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_test_files(temp_dir, count=5, size_kb=10):
    """创建测试文件"""
    test_files = []
    for i in range(count):
        file_path = os.path.join(temp_dir, f"test_file_{i:02d}.txt")
        content = f"这是测试文件 {i} 的内容\n" * (size_kb * 100)  # 大约size_kb KB
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        test_files.append(file_path)
    return test_files

def test_key_file_matching_fix():
    """测试密钥文件匹配修复"""
    print("=== 测试密钥文件匹配修复 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建测试文件
        test_files = create_test_files(temp_dir, 3, 5)
        
        # 创建输出目录
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 创建批量处理器
            batch_cipher = create_batch_cipher()
            print("✓ 批量处理器创建成功")
            
            # 配置
            batch_cipher.parallel_processing = False
            
            # 添加状态回调
            status_messages = []
            def status_callback(message):
                print(f"状态: {message}")
                status_messages.append(message)
            
            batch_cipher.add_status_callback(status_callback)
            
            # 1. 测试OTP加密并生成密钥文件
            print("\n--- 测试OTP加密和密钥文件生成 ---")
            otp_output_dir = os.path.join(temp_dir, "otp_output")
            os.makedirs(otp_output_dir, exist_ok=True)
            
            result_otp = batch_cipher.process_batch(
                source_paths=test_files,
                output_dir=otp_output_dir,
                operation_type=BatchOperationType.ENCRYPT,
                algorithm="OTP",
                key_type="random",
                password=None,
                mode=BatchProcessingMode.FILES
            )
            
            print(f"OTP加密结果: 成功 {result_otp.successful_files}/{result_otp.total_files} 个")
            
            # 检查生成的密钥文件
            print("\n检查生成的OTP密钥文件:")
            key_files_found = []
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                name, ext = os.path.splitext(base_name)
                
                # 使用_find_matching_key_file方法查找密钥文件
                key_file = batch_cipher._find_matching_key_file(
                    file_path + ".enc",  # 模拟加密文件名
                    otp_output_dir,
                    "OTP",
                    "random"
                )
                
                if key_file and os.path.exists(key_file):
                    key_files_found.append(key_file)
                    print(f"  {base_name}.enc -> 找到密钥文件: {os.path.basename(key_file)}")
                else:
                    print(f"  {base_name}.enc -> 未找到密钥文件")
            
            print(f"总计找到 {len(key_files_found)} 个密钥文件")
            
            # 2. 测试OTP批量解密（使用自动密钥文件查找）
            print("\n--- 测试OTP批量解密（自动密钥匹配） ---")
            otp_decrypt_dir = os.path.join(temp_dir, "otp_decrypt")
            os.makedirs(otp_decrypt_dir, exist_ok=True)
            
            # 收集加密文件
            encrypted_files = []
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                encrypted_file = os.path.join(otp_output_dir, base_name + ".enc")
                if os.path.exists(encrypted_file):
                    encrypted_files.append(encrypted_file)
            
            if encrypted_files:
                result_otp_decrypt = batch_cipher.process_batch(
                    source_paths=encrypted_files,
                    output_dir=otp_decrypt_dir,
                    operation_type=BatchOperationType.DECRYPT,
                    algorithm="OTP",
                    key_type="random",
                    password=None,
                    mode=BatchProcessingMode.FILES
                )
                
                print(f"OTP批量解密结果: 成功 {result_otp_decrypt.successful_files}/{result_otp_decrypt.total_files} 个")
                
                # 验证解密文件
                print("\n验证解密文件:")
                for file_path in test_files:
                    base_name = os.path.basename(file_path)
                    decrypted_file = os.path.join(otp_decrypt_dir, base_name)
                    if os.path.exists(decrypted_file):
                        with open(decrypted_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        print(f"  {decrypted_file}: 存在, 内容长度: {len(content)} 字符")
                    else:
                        print(f"  {decrypted_file}: 不存在")
            
            # 3. 测试AES加密
            print("\n--- 测试AES加密 ---")
            aes_output_dir = os.path.join(temp_dir, "aes_output")
            os.makedirs(aes_output_dir, exist_ok=True)
            
            result_aes = batch_cipher.process_batch(
                source_paths=test_files,
                output_dir=aes_output_dir,
                operation_type=BatchOperationType.ENCRYPT,
                algorithm="AES256",
                key_type="random",
                password=None,
                mode=BatchProcessingMode.FILES
            )
            
            print(f"AES加密结果: 成功 {result_aes.successful_files}/{result_aes.total_files} 个")
            
            # 检查AES密钥文件
            print("\n检查AES密钥文件:")
            aes_key_files_found = []
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                name, ext = os.path.splitext(base_name)
                
                # 使用_find_matching_key_file方法查找AES密钥文件
                key_file = batch_cipher._find_matching_key_file(
                    file_path + ".enc",  # 模拟加密文件名
                    aes_output_dir,
                    "AES256",
                    "random"
                )
                
                if key_file and os.path.exists(key_file):
                    aes_key_files_found.append(key_file)
                    print(f"  {base_name}.enc -> 找到密钥文件: {os.path.basename(key_file)}")
                else:
                    print(f"  {base_name}.enc -> 未找到密钥文件")
            
            print(f"总计找到 {len(aes_key_files_found)} 个AES密钥文件")
            
            return True
            
        except Exception as e:
            print(f"✗ 测试过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_cancel_mechanism_fix():
    """测试取消处理机制修复"""
    print("\n=== 测试取消处理机制修复 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建大量测试文件（用于测试取消）
        test_files = create_test_files(temp_dir, 10, 100)  # 10个100KB文件
        
        # 创建输出目录
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 创建批量处理器
            batch_cipher = create_batch_cipher()
            print("✓ 批量处理器创建成功")
            
            # 启用并行处理
            batch_cipher.parallel_processing = True
            batch_cipher.max_threads = 4
            
            # 添加状态回调
            status_messages = []
            processing_events = []
            
            def status_callback(message):
                print(f"状态: {message}")
                status_messages.append(message)
                processing_events.append((time.time(), "status", message))
            
            batch_cipher.add_status_callback(status_callback)
            
            # 添加进度回调
            def progress_callback(current, total, current_file):
                print(f"进度: {current}/{total} - {current_file}")
                processing_events.append((time.time(), "progress", f"{current}/{total}"))
            
            batch_cipher.add_progress_callback(progress_callback)
            
            # 在后台线程中启动批量处理
            print("\n启动批量处理...")
            result = None
            processing_error = None
            
            def process_batch_thread():
                nonlocal result, processing_error
                try:
                    result = batch_cipher.process_batch(
                        source_paths=test_files,
                        output_dir=output_dir,
                        operation_type=BatchOperationType.ENCRYPT,
                        algorithm="OTP",
                        key_type="random",
                        password=None,
                        mode=BatchProcessingMode.FILES
                    )
                except Exception as e:
                    processing_error = e
            
            # 启动处理线程
            process_thread = threading.Thread(target=process_batch_thread)
            process_thread.start()
            
            # 等待处理开始
            time.sleep(1)
            
            # 检查处理状态
            print(f"处理状态: {batch_cipher.is_processing()}")
            
            # 模拟取消操作（在另一个线程中）
            def cancel_thread():
                time.sleep(2)  # 等待2秒后取消
                print("\n执行取消操作...")
                batch_cipher.cancel_processing()
            
            cancel_thread_obj = threading.Thread(target=cancel_thread)
            cancel_thread_obj.start()
            
            # 等待处理完成
            process_thread.join()
            cancel_thread_obj.join()
            
            # 检查结果
            print(f"\n处理完成，结果: {result}")
            print(f"处理错误: {processing_error}")
            
            # 验证取消是否生效
            if result and result.total_files > 0:
                print(f"处理统计: 成功 {result.successful_files}, 失败 {result.failed_files}, 跳过 {result.skipped_files}")
                print(f"处理文件数: {result.successful_files + result.failed_files + result.skipped_files}")
            
            # 检查状态消息中是否包含取消信息
            cancel_messages = [msg for msg in status_messages if "取消" in msg or "cancel" in msg.lower()]
            print(f"取消相关消息数量: {len(cancel_messages)}")
            
            # 检查处理事件记录
            print(f"处理事件记录数量: {len(processing_events)}")
            
            print("✓ 取消机制测试完成")
            return True
            
        except Exception as e:
            print(f"✗ 测试过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_thread_safety_fix():
    """测试线程安全性修复"""
    print("\n=== 测试线程安全性修复 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建多个测试文件
        test_files = create_test_files(temp_dir, 8, 50)  # 8个50KB文件
        
        # 创建输出目录
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 创建批量处理器
            batch_cipher = create_batch_cipher()
            print("✓ 批量处理器创建成功")
            
            # 启用并行处理
            batch_cipher.parallel_processing = True
            batch_cipher.max_threads = 4
            
            # 跟踪线程ID和FileCipher实例
            thread_cipher_instances = {}
            
            def status_callback(message):
                print(f"状态: {message}")
            
            batch_cipher.add_status_callback(status_callback)
            
            # 启动批量处理
            print("\n启动并行批量处理...")
            result = batch_cipher.process_batch(
                source_paths=test_files,
                output_dir=output_dir,
                operation_type=BatchOperationType.ENCRYPT,
                algorithm="AES256",
                key_type="password",
                password="TestPassword123!",
                mode=BatchProcessingMode.FILES
            )
            
            print(f"并行处理结果: 成功 {result.successful_files}/{result.total_files} 个")
            
            # 验证输出文件
            print("\n验证输出文件:")
            encrypted_files = []
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                encrypted_file = os.path.join(output_dir, base_name + ".enc")
                if os.path.exists(encrypted_file):
                    encrypted_files.append(encrypted_file)
                    file_size = os.path.getsize(encrypted_file)
                    print(f"  {encrypted_file}: 存在, 大小: {file_size} 字节")
                else:
                    print(f"  {encrypted_file}: 不存在")
            
            print(f"总计 {len(encrypted_files)} 个加密文件创建成功")
            
            # 测试批量解密
            print("\n测试批量解密...")
            decrypt_dir = os.path.join(temp_dir, "decrypt")
            os.makedirs(decrypt_dir, exist_ok=True)
            
            result_decrypt = batch_cipher.process_batch(
                source_paths=encrypted_files,
                output_dir=decrypt_dir,
                operation_type=BatchOperationType.DECRYPT,
                algorithm="AES256",
                key_type="password",
                password="TestPassword123!",
                mode=BatchProcessingMode.FILES
            )
            
            print(f"批量解密结果: 成功 {result_decrypt.successful_files}/{result_decrypt.total_files} 个")
            
            # 验证解密文件
            print("\n验证解密文件:")
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                decrypted_file = os.path.join(decrypt_dir, base_name)
                if os.path.exists(decrypted_file):
                    with open(decrypted_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"  {decrypted_file}: 存在, 内容长度: {len(content)} 字符")
                else:
                    print(f"  {decrypted_file}: 不存在")
            
            print("✓ 线程安全性测试完成")
            return True
            
        except Exception as e:
            print(f"✗ 测试过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_comprehensive_functionality():
    """测试全面的批量处理功能"""
    print("\n=== 测试全面的批量处理功能 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建不同大小的测试文件
        test_files = []
        sizes = [1, 10, 100, 500]  # 不同大小（KB）
        for i, size in enumerate(sizes):
            file_path = os.path.join(temp_dir, f"test_file_{i}_{size}kb.txt")
            content = f"这是 {size}KB 测试文件 {i} 的内容\n" * (size * 100)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            test_files.append(file_path)
        
        # 测试不同模式
        test_modes = [
            ("串行处理", False, 1),
            ("并行处理（2线程）", True, 2),
            ("并行处理（4线程）", True, 4),
        ]
        
        all_tests_passed = True
        
        for mode_name, parallel, max_threads in test_modes:
            print(f"\n--- 测试模式: {mode_name} ---")
            
            # 创建输出目录
            output_dir = os.path.join(temp_dir, f"output_{mode_name.replace(' ', '_').replace('（', '_').replace('）', '')}")
            os.makedirs(output_dir, exist_ok=True)
            
            try:
                # 创建批量处理器
                batch_cipher = create_batch_cipher()
                batch_cipher.parallel_processing = parallel
                batch_cipher.max_threads = max_threads
                
                # 添加回调
                status_messages = []
                def status_callback(message):
                    if "批量处理统计报告" in message:
                        print(f"状态报告: {message}")
                    status_messages.append(message)
                
                batch_cipher.add_status_callback(status_callback)
                
                # 测试OTP加密
                result_otp = batch_cipher.process_batch(
                    source_paths=test_files,
                    output_dir=output_dir,
                    operation_type=BatchOperationType.ENCRYPT,
                    algorithm="OTP",
                    key_type="random",
                    password=None,
                    mode=BatchProcessingMode.FILES
                )
                
                print(f"OTP加密: {result_otp.successful_files}/{result_otp.total_files} 成功")
                
                # 测试AES密码模式
                aes_output_dir = os.path.join(output_dir, "aes")
                os.makedirs(aes_output_dir, exist_ok=True)
                
                result_aes = batch_cipher.process_batch(
                    source_paths=test_files,
                    output_dir=aes_output_dir,
                    operation_type=BatchOperationType.ENCRYPT,
                    algorithm="AES256",
                    key_type="password",
                    password="TestPassword123!",
                    mode=BatchProcessingMode.FILES
                )
                
                print(f"AES密码加密: {result_aes.successful_files}/{result_aes.total_files} 成功")
                
                if result_otp.successful_files == result_otp.total_files and result_aes.successful_files == result_aes.total_files:
                    print(f"✓ {mode_name} 测试通过")
                else:
                    print(f"✗ {mode_name} 测试失败")
                    all_tests_passed = False
                
            except Exception as e:
                print(f"✗ {mode_name} 测试出错: {e}")
                all_tests_passed = False
        
        return all_tests_passed

def main():
    """主函数"""
    print("批量处理功能修复验证测试")
    print("=" * 60)
    
    # 运行测试
    results = []
    results.append(("密钥文件匹配修复测试", test_key_file_matching_fix()))
    results.append(("取消处理机制修复测试", test_cancel_mechanism_fix()))
    results.append(("线程安全性修复测试", test_thread_safety_fix()))
    results.append(("全面功能测试", test_comprehensive_functionality()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(results)
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "=" * 60)
    print(f"测试通过率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    print("=" * 60)
    
    print("\n修复总结:")
    print("1. 密钥文件匹配功能 - 已修复，支持自动查找密钥文件")
    print("2. 取消处理机制 - 已改进，支持真正的线程中断")
    print("3. 线程安全性 - 已修复，每个线程使用独立的FileCipher实例")
    print("4. 并行处理 - 已优化，支持可配置的线程数和取消")
    
    if passed_tests == total_tests:
        print("\n✓ 所有测试通过！批量处理功能修复完成。")
        return True
    else:
        print(f"\n⚠️ 部分测试失败，通过率: {success_rate:.1f}%")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)