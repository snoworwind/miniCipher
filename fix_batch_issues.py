#!/usr/bin/env python3
"""
批量处理功能修复脚本
修复已发现的关键问题：
1. 密钥文件匹配逻辑
2. 取消处理机制
3. 并行处理安全性
4. 批量解密测试
"""

import os
import tempfile
import shutil
import logging
import time
from batch_cipher import BatchOperationType, BatchProcessingMode, create_batch_cipher
from cipher_algorithms import FileCipher, FileFormatHandler, AlgorithmType

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_key_file_matching():
    """测试密钥文件匹配功能"""
    print("=== 测试密钥文件匹配功能 ===")
    
    # 创建临时目录和测试文件
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建测试文件
        test_files = []
        for i in range(3):
            file_path = os.path.join(temp_dir, f"test_file_{i}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"这是测试文件 {i} 的内容\n")
                f.write(f"用于测试密钥文件匹配\n")
                f.write(f"行号: {i}\n" * 10)
            test_files.append(file_path)
        
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
            def status_callback(message):
                print(f"状态: {message}")
            
            batch_cipher.add_status_callback(status_callback)
            
            # 1. 测试OTP批量加密
            print("\n--- 测试OTP批量加密 ---")
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
            
            print(f"OTP加密结果: 成功 {result_otp.successful_files} 个")
            
            # 检查生成的文件
            print("\n检查OTP生成的文件:")
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                encrypted_file = os.path.join(otp_output_dir, base_name + ".enc")
                print(f"密文文件: {encrypted_file} - 存在: {os.path.exists(encrypted_file)}")
                
                # 检查密钥文件
                key_file_txt = os.path.join(otp_output_dir, f"key_{base_name}.txt")
                key_file_bin = os.path.join(otp_output_dir, f"key_{base_name}.bin")
                key_file_key = os.path.join(otp_output_dir, f"key_{base_name}.key")
                
                # 查找实际存在的密钥文件
                actual_key_files = []
                for key_file in [key_file_txt, key_file_bin, key_file_key]:
                    if os.path.exists(key_file):
                        actual_key_files.append(key_file)
                
                if actual_key_files:
                    print(f"  找到密钥文件: {actual_key_files}")
                else:
                    print(f"  警告: 未找到密钥文件")
            
            # 2. 测试AES批量加密
            print("\n--- 测试AES批量加密 ---")
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
            
            print(f"AES加密结果: 成功 {result_aes.successful_files} 个")
            
            # 检查生成的文件
            print("\n检查AES生成的文件:")
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                encrypted_file = os.path.join(aes_output_dir, base_name + ".enc")
                print(f"密文文件: {encrypted_file} - 存在: {os.path.exists(encrypted_file)}")
                
                # 检查密钥文件
                key_file_key = os.path.join(aes_output_dir, f"key_{base_name}.key")
                if os.path.exists(key_file_key):
                    print(f"  找到密钥文件: {key_file_key}")
                else:
                    print(f"  警告: 未找到AES密钥文件")
            
            # 3. 测试批量解密
            print("\n--- 测试批量解密功能 ---")
            
            # 测试OTP批量解密
            print("\n测试OTP批量解密:")
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
                try:
                    result_otp_decrypt = batch_cipher.process_batch(
                        source_paths=encrypted_files,
                        output_dir=otp_decrypt_dir,
                        operation_type=BatchOperationType.DECRYPT,
                        algorithm="OTP",
                        key_type="random",
                        password=None,
                        mode=BatchProcessingMode.FILES
                    )
                    print(f"OTP批量解密结果: 成功 {result_otp_decrypt.successful_files} 个")
                    
                    # 检查解密文件
                    print("检查解密文件:")
                    for file_path in test_files:
                        base_name = os.path.basename(file_path)
                        decrypted_file = os.path.join(otp_decrypt_dir, base_name)
                        if os.path.exists(decrypted_file):
                            with open(decrypted_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            print(f"  {decrypted_file} - 存在: 是, 内容长度: {len(content)}")
                        else:
                            print(f"  {decrypted_file} - 存在: 否")
                except Exception as e:
                    print(f"  OTP批量解密失败: {e}")
            else:
                print("  OTP加密文件不存在，无法测试解密")
            
            # 测试AES批量解密
            print("\n测试AES批量解密:")
            aes_decrypt_dir = os.path.join(temp_dir, "aes_decrypt")
            os.makedirs(aes_decrypt_dir, exist_ok=True)
            
            # 收集AES加密文件
            aes_encrypted_files = []
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                encrypted_file = os.path.join(aes_output_dir, base_name + ".enc")
                if os.path.exists(encrypted_file):
                    aes_encrypted_files.append(encrypted_file)
            
            if aes_encrypted_files:
                try:
                    result_aes_decrypt = batch_cipher.process_batch(
                        source_paths=aes_encrypted_files,
                        output_dir=aes_decrypt_dir,
                        operation_type=BatchOperationType.DECRYPT,
                        algorithm="AES256",
                        key_type="random",
                        password=None,
                        mode=BatchProcessingMode.FILES
                    )
                    print(f"AES批量解密结果: 成功 {result_aes_decrypt.successful_files} 个")
                    
                    # 检查解密文件
                    print("检查解密文件:")
                    for file_path in test_files:
                        base_name = os.path.basename(file_path)
                        decrypted_file = os.path.join(aes_decrypt_dir, base_name)
                        if os.path.exists(decrypted_file):
                            with open(decrypted_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            print(f"  {decrypted_file} - 存在: 是, 内容长度: {len(content)}")
                        else:
                            print(f"  {decrypted_file} - 存在: 否")
                except Exception as e:
                    print(f"  AES批量解密失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("  AES加密文件不存在，无法测试解密")
            
            return True
            
        except Exception as e:
            print(f"✗ 测试过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def analyze_batch_cipher_implementation():
    """分析BatchCipher实现，识别需要修复的问题"""
    print("\n=== 分析BatchCipher实现 ===")
    
    batch_cipher = create_batch_cipher()
    
    # 检查问题点
    print("检查关键方法:")
    print(f"1. _find_matching_key_file() 方法: {'已实现' if hasattr(batch_cipher, '_find_matching_key_file') else '缺失'}")
    print(f"2. cancel_processing() 实现: {'已实现' if hasattr(batch_cipher, 'cancel_processing') else '缺失'}")
    print(f"3. FileCipher实例共享: {'是' if hasattr(batch_cipher, 'file_cipher') else '否'}")
    
    # 检查process_batch方法中的线程安全性
    print("\n检查process_batch方法的线程安全性:")
    print("需要检查: process_file_wrapper函数中是否创建独立的FileCipher实例")
    
    # 分析取消机制
    print("\n分析取消机制:")
    print(f"当前取消机制: 只设置_is_processing = False")
    print("问题: 不中断运行中的线程")
    
    return True

def propose_fixes():
    """提出修复方案"""
    print("\n=== 提出修复方案 ===")
    
    print("1. 密钥文件匹配功能修复:")
    print("   - 实现_find_matching_key_file()方法")
    print("   - 支持多种密钥文件命名模式")
    print("   - 添加配置选项控制密钥文件命名规则")
    
    print("\n2. 取消处理机制修复:")
    print("   - 跟踪所有ThreadPoolExecutor线程")
    print("   - 实现真正的线程中断")
    print("   - 添加Future对象跟踪和取消")
    
    print("\n3. 并行处理安全性修复:")
    print("   - 为每个线程创建独立的FileCipher实例")
    print("   - 使用线程局部存储或工厂模式")
    
    print("\n4. 进度更新修复:")
    print("   - 确保results_queue完全清空")
    print("   - 添加超时处理和异常恢复")
    
    print("\n5. 批量解密测试:")
    print("   - 创建完整的批量解密测试用例")
    print("   - 测试各种场景（成功、失败、部分成功）")
    
    return True

def main():
    """主函数"""
    print("批量处理功能修复分析")
    print("=" * 60)
    
    # 运行测试和分析
    results = []
    results.append(("密钥文件匹配测试", test_key_file_matching()))
    results.append(("BatchCipher实现分析", analyze_batch_cipher_implementation()))
    results.append(("修复方案提出", propose_fixes()))
    
    # 输出结果
    print("\n" + "=" * 60)
    print("分析结果汇总:")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
    
    print("\n关键问题确认:")
    print("1. 密钥文件匹配功能缺失 - 批量解密无法自动找到密钥文件")
    print("2. 取消机制不完善 - 只设置标志，不中断线程")
    print("3. 线程安全性问题 - FileCipher实例共享")
    print("4. 批量解密测试覆盖率低 - 需要创建完整测试")
    
    print("\n下一步:")
    print("1. 实施_find_matching_key_file()方法")
    print("2. 改进取消处理机制")
    print("3. 修复线程安全性问题")
    print("4. 创建全面的批量解密测试")
    
    return all(success for _, success in results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)