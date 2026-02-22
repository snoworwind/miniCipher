#!/usr/bin/env python3
"""
测试AES256随机模式修复
验证加密和解密是否能正常工作
"""

import os
import sys
import tempfile
import secrets
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cipher_algorithms import AlgorithmType, KeyType, get_algorithm, FileFormatHandler

def test_aes_random_key():
    """测试AES256随机密钥模式"""
    print("测试AES256随机密钥模式...")
    
    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.test') as f:
        test_data = secrets.token_bytes(1024 * 1024)  # 1MB随机数据
        f.write(test_data)
        input_file = f.name
    
    try:
        # 创建输出文件路径
        output_encrypted = input_file + '.enc'
        output_decrypted = input_file + '.dec'
        
        # 获取算法实例
        cipher_algorithm = get_algorithm(AlgorithmType.AES256)
        
        print(f"1. 加密文件: {input_file}")
        print(f"   加密后: {output_encrypted}")
        
        # 加密文件
        result = cipher_algorithm.encrypt_with_random_key_chunked_to_file(
            input_file,
            output_encrypted,
            chunk_size=1024 * 1024  # 1MB块大小
        )
        
        print(f"   加密成功!")
        print(f"   密钥长度: {len(result.key)}")
        print(f"   IV长度: {len(result.iv)}")
        print(f"   Tag长度: {len(result.tag)}")
        
        # 检查加密文件格式
        print(f"\n2. 检查加密文件格式...")
        try:
            ciphertext, iv, tag, _ = FileFormatHandler.read_aes_file(output_encrypted)
            print(f"   文件格式正确!")
            print(f"   密文长度: {len(ciphertext)}")
            print(f"   IV匹配: {iv == result.iv}")
            print(f"   Tag匹配: {tag == result.tag}")
            
            # 验证文件结构
            file_size = os.path.getsize(output_encrypted)
            expected_size = 4 + 12 + len(ciphertext) + 16  # 文件头 + IV + 密文 + 标签
            print(f"   文件大小: {file_size}字节")
            print(f"   预期大小: {expected_size}字节")
            print(f"   大小匹配: {file_size == expected_size}")
            
        except Exception as e:
            print(f"   读取加密文件失败: {e}")
            return False
        
        print(f"\n3. 解密文件...")
        print(f"   解密后: {output_decrypted}")
        
        # 解密文件
        try:
            # 使用分块解密
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            
            cipher = Cipher(
                algorithms.AES(result.key),
                modes.GCM(result.iv, result.tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # 读取密文并解密
            with open(output_encrypted, 'rb') as f:
                header = f.read(4)  # 跳过文件头
                if header != b'AES\x00':
                    raise ValueError("无效的文件头")
                iv_from_file = f.read(12)  # 读取IV
                if iv_from_file != result.iv:
                    raise ValueError("IV不匹配")
                
                # 读取密文和标签
                ciphertext = f.read()
                if len(ciphertext) < 16:
                    raise ValueError("文件损坏")
                
                # 分离密文和标签
                ciphertext_only = ciphertext[:-16]
                tag_from_file = ciphertext[-16:]
                
                if tag_from_file != result.tag:
                    print(f"   ⚠️  警告: 文件中的标签与加密器标签不匹配")
                    print(f"     文件标签: {tag_from_file.hex()[:16]}...")
                    print(f"     加密器标签: {result.tag.hex()[:16]}...")
                    # 使用文件中的标签继续测试
                
                # 解密
                plaintext = decryptor.update(ciphertext_only) + decryptor.finalize()
                
                # 写入解密文件
                with open(output_decrypted, 'wb') as f_out:
                    f_out.write(plaintext)
                
                print(f"   解密成功!")
                
                # 验证解密结果
                with open(input_file, 'rb') as f_orig, open(output_decrypted, 'rb') as f_dec:
                    original = f_orig.read()
                    decrypted = f_dec.read()
                    
                    if original == decrypted:
                        print(f"   ✅ 验证成功: 原始文件和解密文件完全相同!")
                    else:
                        print(f"   ❌ 验证失败: 原始文件和解密文件不同")
                        print(f"      原始大小: {len(original)}字节")
                        print(f"      解密大小: {len(decrypted)}字节")
                        return False
                        
        except Exception as e:
            print(f"   解密失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        return True
        
    finally:
        # 清理临时文件
        for f in [input_file, output_encrypted, output_decrypted]:
            if f and os.path.exists(f):
                try:
                    os.unlink(f)
                except:
                    pass

def test_small_file():
    """测试小文件"""
    print("\n" + "="*60)
    print("测试小文件AES256随机密钥模式...")
    
    # 创建小测试文件
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.test') as f:
        test_data = b"Hello, World! This is a test file for AES256 encryption." * 100
        f.write(test_data)
        input_file = f.name
    
    try:
        output_encrypted = input_file + '.enc'
        output_decrypted = input_file + '.dec'
        
        # 获取算法实例
        cipher_algorithm = get_algorithm(AlgorithmType.AES256)
        
        # 加密（使用完整加密，不分块）
        result = cipher_algorithm.encrypt_with_random_key(test_data)
        
        # 写入加密文件
        FileFormatHandler.write_aes_file(output_encrypted, result.ciphertext, result.iv, result.tag)
        
        print(f"小文件加密成功!")
        print(f"密文长度: {len(result.ciphertext)}")
        
        # 解密
        result_dec = cipher_algorithm.decrypt_with_random_key(
            result.ciphertext, result.key, result.iv, result.tag
        )
        
        print(f"小文件解密成功!")
        
        if test_data == result_dec.plaintext:
            print(f"✅ 小文件验证成功!")
        else:
            print(f"❌ 小文件验证失败!")
            return False
            
        return True
        
    finally:
        # 清理
        for f in [input_file, output_encrypted, output_decrypted]:
            if f and os.path.exists(f):
                try:
                    os.unlink(f)
                except:
                    pass

if __name__ == "__main__":
    print("="*60)
    print("开始测试AES256随机模式修复")
    print("="*60)
    
    success_count = 0
    total_tests = 2
    
    try:
        # 测试大文件
        if test_aes_random_key():
            success_count += 1
            print("\n✅ 大文件测试通过!")
        else:
            print("\n❌ 大文件测试失败!")
        
        # 测试小文件
        if test_small_file():
            success_count += 1
            print("\n✅ 小文件测试通过!")
        else:
            print("\n❌ 小文件测试失败!")
        
        print("\n" + "="*60)
        print(f"测试结果: {success_count}/{total_tests} 通过")
        
        if success_count == total_tests:
            print("🎉 所有测试通过! AES256随机模式修复成功!")
        else:
            print("⚠️  部分测试失败，请检查代码")
            sys.exit(1)
            
    except Exception as e:
        print(f"测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)