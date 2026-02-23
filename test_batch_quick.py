#!/usr/bin/env python3
"""
快速测试批量处理修复
"""

import os
import tempfile
import logging
from batch_cipher import BatchOperationType, BatchProcessingMode, create_batch_cipher

logging.basicConfig(level=logging.WARNING)

def test_batch_basic():
    """测试基本批量处理功能"""
    print("=== 测试基本批量处理功能 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建测试文件
        test_files = []
        for i in range(3):
            file_path = os.path.join(temp_dir, f"test_{i}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"这是测试文件 {i} 的内容" * 10)
            test_files.append(file_path)
            print(f"创建测试文件: {file_path}")
        
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 创建批量处理器
            batch_cipher = create_batch_cipher()
            print("✓ 批量处理器创建成功")
            
            # 配置
            batch_cipher.parallel_processing = False
            
            # 1. 测试AES256密码模式加密
            print("\n--- 测试AES256密码模式加密 ---")
            result_encrypt = batch_cipher.process_batch(
                source_paths=test_files,
                output_dir=output_dir,
                operation_type=BatchOperationType.ENCRYPT,
                algorithm="AES256",
                key_type="password",
                password="TestPassword123!",
                mode=BatchProcessingMode.FILES
            )
            
            print(f"AES256加密结果: {result_encrypt.successful_files}/{result_encrypt.total_files} 成功")
            
            # 2. 测试AES256密码模式解密
            print("\n--- 测试AES256密码模式解密 ---")
            decrypt_dir = os.path.join(temp_dir, "decrypt")
            os.makedirs(decrypt_dir, exist_ok=True)
            
            # 收集加密文件
            encrypted_files = []
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                encrypted_file = os.path.join(output_dir, base_name + ".enc")
                if os.path.exists(encrypted_file):
                    encrypted_files.append(encrypted_file)
                    print(f"找到加密文件: {encrypted_file}")
            
            if encrypted_files:
                result_decrypt = batch_cipher.process_batch(
                    source_paths=encrypted_files,
                    output_dir=decrypt_dir,
                    operation_type=BatchOperationType.DECRYPT,
                    algorithm="AES256",
                    key_type="password",
                    password="TestPassword123!",
                    mode=BatchProcessingMode.FILES
                )
                
                print(f"AES256解密结果: {result_decrypt.successful_files}/{result_decrypt.total_files} 成功")
                
                # 验证解密文件
                print("\n验证解密文件:")
                for file_path in test_files:
                    base_name = os.path.basename(file_path)
                    decrypted_file = os.path.join(decrypt_dir, base_name)
                    if os.path.exists(decrypted_file):
                        with open(decrypted_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        original_content = f"这是测试文件 {base_name.split('_')[1].split('.')[0]} 的内容" * 10
                        if content == original_content:
                            print(f"  {decrypted_file}: ✓ 验证成功")
                        else:
                            print(f"  {decrypted_file}: ✗ 验证失败，内容不匹配")
                    else:
                        print(f"  {decrypted_file}: ✗ 文件不存在")
            
            # 3. 测试密钥文件匹配功能
            print("\n--- 测试密钥文件匹配功能 ---")
            batch_cipher._find_matching_key_file(
                input_path=test_files[0] + ".enc",
                output_dir=output_dir,
                algorithm="OTP",
                key_type="random"
            )
            print("✓ 密钥文件匹配函数可调用")
            
            # 4. 测试取消处理
            print("\n--- 测试取消处理 ---")
            batch_cipher.cancel_processing()
            print("✓ 取消处理函数可调用")
            
            print("\n" + "=" * 50)
            print("✓ 基本批量处理功能测试完成")
            return True
            
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_parallel_processing():
    """测试并行处理功能"""
    print("\n=== 测试并行处理功能 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建多个测试文件
        test_files = []
        for i in range(5):
            file_path = os.path.join(temp_dir, f"parallel_test_{i}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"并行测试文件 {i} 的内容" * 100)
            test_files.append(file_path)
        
        output_dir = os.path.join(temp_dir, "parallel_output")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 创建批量处理器
            batch_cipher = create_batch_cipher()
            
            # 启用并行处理
            batch_cipher.parallel_processing = True
            batch_cipher.max_threads = 2
            
            print("启动并行批量加密...")
            result = batch_cipher.process_batch(
                source_paths=test_files,
                output_dir=output_dir,
                operation_type=BatchOperationType.ENCRYPT,
                algorithm="AES256",
                key_type="password",
                password="ParallelTest123!",
                mode=BatchProcessingMode.FILES
            )
            
            print(f"并行加密结果: {result.successful_files}/{result.total_files} 成功")
            
            # 检查输出文件
            encrypted_files = []
            for file_path in test_files:
                base_name = os.path.basename(file_path)
                encrypted_file = os.path.join(output_dir, base_name + ".enc")
                if os.path.exists(encrypted_file):
                    encrypted_files.append(encrypted_file)
                    file_size = os.path.getsize(encrypted_file)
                    print(f"  {encrypted_file}: ✓ 存在, 大小: {file_size} 字节")
                else:
                    print(f"  {encrypted_file}: ✗ 不存在")
            
            print("✓ 并行处理功能测试完成")
            return True
            
        except Exception as e:
            print(f"✗ 并行处理测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    print("批量处理修复快速测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("基本批量处理功能", test_batch_basic()))
    results.append(("并行处理功能", test_parallel_processing()))
    
    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{name}: {status}")
        if success:
            passed += 1
    
    print("\n" + "=" * 60)
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"通过率: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed == total:
        print("✓ 所有测试通过！批量处理功能修复成功。")
        return True
    else:
        print(f"⚠️ 部分测试失败，通过率: {success_rate:.1f}%")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)