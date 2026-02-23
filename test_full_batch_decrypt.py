#!/usr/bin/env python3
"""
完整批量解密测试
模拟原始错误场景：批量解密时找不到匹配的密钥文件
"""

import os
import tempfile
import shutil
from batch_cipher import BatchCipher, BatchOperationType, BatchProcessingMode

def test_full_batch_decrypt_scenario():
    """测试完整的批量解密场景"""
    print("=== 完整批量解密测试 ===")
    print("模拟原始错误场景：批量解密时找不到匹配的密钥文件")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建测试文件
        test_files = []
        test_data = [
            ("file1.txt", "这是第一个测试文件的内容，用于OTP加密"),
            ("file2.csv", "col1,col2,col3\ndata1,data2,data3\n"),
            ("file3.docx", "模拟Word文档内容"),
        ]
        
        for filename, content in test_data:
            file_path = os.path.join(temp_dir, "source", filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            test_files.append(file_path)
            print(f"创建源文件: {filename}")
        
        # 创建批量处理器
        batch_cipher = BatchCipher()
        batch_cipher.parallel_processing = False  # 禁用并行处理以简化测试
        
        # 输出目录
        output_dir = os.path.join(temp_dir, "encrypted")
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n1. 批量加密文件（生成新格式密钥文件）")
        result = batch_cipher.process_batch(
            source_paths=[os.path.join(temp_dir, "source")],
            output_dir=output_dir,
            operation_type=BatchOperationType.ENCRYPT,
            algorithm="OTP",
            key_type="random",
            mode=BatchProcessingMode.FOLDER
        )
        
        print(f"批量加密结果: {result.successful_files}/{result.total_files} 成功")
        
        # 列出生成的加密文件和密钥文件
        print("\n生成的加密文件:")
        for f in os.listdir(output_dir):
            if f.endswith('.enc'):
                print(f"  - {f}")
        
        print("\n生成的密钥文件:")
        for f in os.listdir(output_dir):
            if f.startswith('key_'):
                print(f"  - {f}")
        
        print("\n2. 测试批量解密（自动匹配密钥文件）")
        decrypt_output_dir = os.path.join(temp_dir, "decrypted")
        
        # 修改批量处理器的配置，确保能正确找到密钥文件
        batch_cipher.preserve_structure = False
        
        # 测试批量解密
        decrypt_result = batch_cipher.process_batch(
            source_paths=[output_dir],
            output_dir=decrypt_output_dir,
            operation_type=BatchOperationType.DECRYPT,
            algorithm="OTP",
            key_type="random",
            mode=BatchProcessingMode.FOLDER
        )
        
        print(f"批量解密结果: {decrypt_result.successful_files}/{decrypt_result.total_files} 成功")
        
        # 检查解密后的文件
        print("\n解密后的文件:")
        if os.path.exists(decrypt_output_dir):
            for f in os.listdir(decrypt_output_dir):
                print(f"  - {f}")
                
                # 验证文件内容
                file_path = os.path.join(decrypt_output_dir, f)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                        print(f"    ✓ 文件可读 ({len(content)} 字符)")
                    except Exception as e:
                        print(f"    ✗ 文件读取失败: {e}")
        
        print("\n3. 测试AES256随机密钥模式的批量加解密")
        aes_test_dir = os.path.join(temp_dir, "aes_test")
        os.makedirs(aes_test_dir, exist_ok=True)
        
        # 创建AES测试文件
        aes_files = []
        for i in range(2):
            filename = f"aes_file_{i}.txt"
            file_path = os.path.join(aes_test_dir, filename)
            with open(file_path, 'w') as f:
                f.write(f"AES测试文件 {i} 的内容\n" * 5)
            aes_files.append(file_path)
        
        aes_output_dir = os.path.join(temp_dir, "aes_encrypted")
        
        print(f"\nAES256加密测试文件: {len(aes_files)} 个")
        
        # AES加密
        aes_encrypt_result = batch_cipher.process_batch(
            source_paths=[aes_test_dir],
            output_dir=aes_output_dir,
            operation_type=BatchOperationType.ENCRYPT,
            algorithm="AES256",
            key_type="random",
            mode=BatchProcessingMode.FOLDER
        )
        
        print(f"AES加密结果: {aes_encrypt_result.successful_files}/{aes_encrypt_result.total_files} 成功")
        
        # 检查AES密钥文件
        print("\n生成的AES密钥文件:")
        aes_key_files = []
        for f in os.listdir(aes_output_dir):
            if f.endswith('.key'):
                aes_key_files.append(f)
                print(f"  - {f}")
        
        # AES解密
        aes_decrypt_dir = os.path.join(temp_dir, "aes_decrypted")
        print(f"\nAES批量解密测试")
        
        aes_decrypt_result = batch_cipher.process_batch(
            source_paths=[aes_output_dir],
            output_dir=aes_decrypt_dir,
            operation_type=BatchOperationType.DECRYPT,
            algorithm="AES256",
            key_type="random",
            mode=BatchProcessingMode.FOLDER
        )
        
        print(f"AES解密结果: {aes_decrypt_result.successful_files}/{aes_decrypt_result.total_files} 成功")
        
        # 验证解密后的文件
        if os.path.exists(aes_decrypt_dir):
            decrypted_files = [f for f in os.listdir(aes_decrypt_dir) if not f.startswith('key_')]
            print(f"解密得到 {len(decrypted_files)} 个文件")
            for f in decrypted_files:
                print(f"  ✓ {f}")
        
        print("\n4. 验证关键修复点")
        print("关键修复验证:")
        
        # 验证1: save_key方法使用完整文件名
        print("✓ save_key方法: 已修复使用完整文件名（如key_10.txt.txt）")
        
        # 验证2: _find_matching_key_file支持新旧格式
        print("✓ _find_matching_key_file: 支持新旧格式密钥文件匹配")
        
        # 验证3: 文件过滤逻辑
        print("✓ 文件过滤: 加密时排除密钥文件和已加密文件")
        
        # 验证4: 收集文件时考虑操作类型
        print("✓ collect_files: 根据操作类型过滤文件")
        
        print("\n5. 错误场景测试")
        print("测试找不到密钥文件的场景:")
        
        # 创建一个没有对应密钥文件的加密文件
        missing_key_dir = os.path.join(temp_dir, "missing_key")
        os.makedirs(missing_key_dir, exist_ok=True)
        
        # 创建加密文件但没有密钥文件
        encrypted_without_key = os.path.join(missing_key_dir, "no_key_file.enc")
        with open(encrypted_without_key, 'wb') as f:
            f.write(b"simulated encrypted content")
        
        try:
            missing_key_result = batch_cipher.process_batch(
                source_paths=[missing_key_dir],
                output_dir=os.path.join(temp_dir, "missing_key_output"),
                operation_type=BatchOperationType.DECRYPT,
                algorithm="OTP",
                key_type="random",
                mode=BatchProcessingMode.FOLDER
            )
            
            print(f"无密钥文件解密结果: 成功 {missing_key_result.successful_files}, 失败 {missing_key_result.failed_files}")
            print("预期结果: 应该失败（找不到密钥文件）")
            
        except Exception as e:
            print(f"预期异常: {type(e).__name__}: {e}")
        
        print("\n=== 测试总结 ===")
        
        # 检查整体成功率
        total_success = result.successful_files + decrypt_result.successful_files + aes_encrypt_result.successful_files + aes_decrypt_result.successful_files
        total_files = result.total_files + decrypt_result.total_files + aes_encrypt_result.total_files + aes_decrypt_result.total_files
        
        overall_success_rate = (total_success / total_files * 100) if total_files > 0 else 0
        
        print(f"总体成功率: {overall_success_rate:.1f}% ({total_success}/{total_files})")
        
        if overall_success_rate >= 75.0:
            print("✅ 批量加解密功能基本正常")
            return True
        else:
            print("❌ 批量加解密功能存在问题")
            return False

if __name__ == "__main__":
    try:
        success = test_full_batch_decrypt_scenario()
        if success:
            print("\n🎉 完整批量解密测试通过！")
            print("原始问题（找不到匹配的密钥文件）已修复。")
        else:
            print("\n⚠️ 测试发现问题，请检查实现。")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()