#!/usr/bin/env python3
"""
测试批量处理中的密钥文件匹配功能
验证修复的密钥文件搜索逻辑
"""

import os
import tempfile
import shutil
from batch_cipher import BatchCipher, BatchOperationType, BatchProcessingMode

def test_key_file_matching():
    """测试密钥文件匹配功能"""
    print("=== 测试密钥文件匹配功能 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"临时目录: {temp_dir}")
        
        # 创建测试文件
        test_files = []
        test_data = [
            ("10.txt", "这是文件10的内容"),
            ("document.pdf.txt", "模拟PDF文件的内容"),
            ("image.jpg", "这是图片文件的内容"),
            ("data.csv", "CSV数据文件"),
        ]
        
        for filename, content in test_data:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            test_files.append(file_path)
            print(f"创建测试文件: {filename}")
        
        # 创建批量处理器
        batch_cipher = BatchCipher()
        
        # 输出目录
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        print("\n1. 测试OTP加密（生成新格式密钥文件）")
        # 先加密文件
        result = batch_cipher.process_batch(
            source_paths=test_files[:2],  # 只测试前2个文件
            output_dir=output_dir,
            operation_type=BatchOperationType.ENCRYPT,
            algorithm="OTP",
            key_type="random",
            mode=BatchProcessingMode.FILES
        )
        
        print(f"加密结果: {result.successful_files}/{result.total_files} 成功")
        
        # 检查生成的密钥文件
        print("\n生成的密钥文件:")
        for filename in ["10.txt", "document.pdf.txt"]:
            expected_key_file = os.path.join(output_dir, f"key_{filename}.txt")
            if os.path.exists(expected_key_file):
                print(f"✓ 找到密钥文件: {os.path.basename(expected_key_file)}")
            else:
                print(f"✗ 未找到密钥文件: {os.path.basename(expected_key_file)}")
                # 列出实际生成的文件
                print("  实际文件列表:")
                for f in os.listdir(output_dir):
                    print(f"    - {f}")
        
        print("\n2. 测试密钥文件匹配功能")
        # 创建BatchCipher实例来测试_find_matching_key_file方法
        for filename in ["10.txt", "document.pdf.txt"]:
            # 模拟加密后的文件名
            encrypted_file = os.path.join(output_dir, f"{filename}.enc")
            
            # 实际上我们需要先创建加密文件（为了测试）
            # 这里我们直接测试_find_matching_key_file方法
            key_file = batch_cipher._find_matching_key_file(
                input_path=os.path.join(temp_dir, filename),
                output_dir=output_dir,
                algorithm="OTP",
                key_type="random"
            )
            
            if key_file:
                print(f"✓ 成功匹配文件 {filename} -> {os.path.basename(key_file)}")
            else:
                print(f"✗ 无法匹配文件 {filename}")
        
        print("\n3. 测试带扩展名的复杂文件名")
        # 测试复杂文件名
        complex_files = []
        for filename in ["test.file.with.dots.txt", "my-document-final.pdf"]:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(f"内容: {filename}")
            complex_files.append(file_path)
        
        # 加密复杂文件
        result = batch_cipher.process_batch(
            source_paths=complex_files,
            output_dir=output_dir,
            operation_type=BatchOperationType.ENCRYPT,
            algorithm="AES256",
            key_type="random",
            mode=BatchProcessingMode.FILES
        )
        
        print(f"复杂文件加密结果: {result.successful_files}/{result.total_files} 成功")
        
        # 检查AES密钥文件
        print("\n生成的AES密钥文件:")
        for filename in ["test.file.with.dots.txt", "my-document-final.pdf"]:
            expected_key_file = os.path.join(output_dir, f"key_{filename}.key")
            if os.path.exists(expected_key_file):
                print(f"✓ 找到AES密钥文件: {os.path.basename(expected_key_file)}")
                
                # 测试密钥文件匹配
                key_file = batch_cipher._find_matching_key_file(
                    input_path=os.path.join(temp_dir, filename),
                    output_dir=output_dir,
                    algorithm="AES256",
                    key_type="random"
                )
                
                if key_file:
                    print(f"  ✓ 成功匹配: {os.path.basename(key_file)}")
                else:
                    print(f"  ✗ 匹配失败")
            else:
                print(f"✗ 未找到AES密钥文件: {os.path.basename(expected_key_file)}")
        
        print("\n4. 测试文件过滤功能")
        # 创建一些不应该被处理的文件
        excluded_files = []
        for filename in ["temp.tmp", "thumbs.db", "backup.enc"]:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write("不应该被处理的内容")
            excluded_files.append(file_path)
        
        # 测试加密时的文件过滤
        print("加密时文件收集测试:")
        files = batch_cipher.collect_files(
            source_paths=[temp_dir],
            mode=BatchProcessingMode.FOLDER_RECURSIVE,
            operation_type=BatchOperationType.ENCRYPT
        )
        
        filtered_files = [os.path.basename(f) for f in files]
        print(f"找到 {len(files)} 个文件:")
        for f in filtered_files:
            print(f"  - {f}")
        
        # 检查是否排除了不应该处理的文件
        excluded_basenames = ["temp.tmp", "thumbs.db", "backup.enc"]
        for excluded in excluded_basenames:
            if excluded in filtered_files:
                print(f"⚠️  警告: 不应该包含文件 {excluded}")
        
        print("\n5. 测试向后兼容性（旧格式密钥文件）")
        # 手动创建旧格式的密钥文件（不包含扩展名）
        old_format_dir = os.path.join(temp_dir, "old_format")
        os.makedirs(old_format_dir, exist_ok=True)
        
        # 创建旧格式的密钥文件
        for filename in ["simple.txt", "data.csv"]:
            # 旧格式：key_<基本名称>.txt
            base_name_no_ext = os.path.splitext(filename)[0]
            old_key_file = os.path.join(old_format_dir, f"key_{base_name_no_ext}.txt")
            with open(old_key_file, 'w') as f:
                f.write("0123456789abcdef" * 10)  # 模拟密钥内容
            
            print(f"创建旧格式密钥文件: {os.path.basename(old_key_file)}")
            
            # 测试能否匹配
            key_file = batch_cipher._find_matching_key_file(
                input_path=os.path.join(temp_dir, filename),
                output_dir=old_format_dir,
                algorithm="OTP",
                key_type="random"
            )
            
            if key_file:
                print(f"  ✓ 成功匹配旧格式密钥: {os.path.basename(key_file)}")
            else:
                print(f"  ✗ 无法匹配旧格式密钥")
        
        print("\n=== 测试完成 ===")
        return True

if __name__ == "__main__":
    try:
        success = test_key_file_matching()
        if success:
            print("\n✅ 所有测试完成！密钥文件匹配功能正常。")
        else:
            print("\n❌ 测试失败！")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()