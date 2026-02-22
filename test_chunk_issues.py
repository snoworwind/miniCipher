#!/usr/bin/env python3
"""
测试分块加密解密的具体问题
重点验证标签不匹配和文件格式处理问题
"""

import os
import sys
import tempfile
import secrets
import logging
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cipher_algorithms import AlgorithmType, KeyType, get_algorithm, FileFormatHandler
from cipher_algorithms import AES256Algorithm

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)

def test_aes_chunked_tag_issue():
    """详细测试AES分块加密的标签问题"""
    print("=" * 80)
    print("详细测试AES分块加密的标签问题")
    print("=" * 80)
    
    # 创建不同大小的测试文件
    test_sizes = [
        1024,          # 小文件 - 小于块大小
        1024 * 1024,   # 1MB - 等于块大小  
        2 * 1024 * 1024,  # 2MB - 大于块大小
        5 * 1024 * 1024,  # 5MB - 明显大于块大小
    ]
    
    chunk_size = 1024 * 1024  # 1MB块大小
    
    for file_size in test_sizes:
        print(f"\n{'='*60}")
        print(f"测试文件大小: {file_size:,} 字节")
        print(f"{'='*60}")
        
        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.test') as f:
            test_data = secrets.token_bytes(file_size)
            f.write(test_data)
            input_file = f.name
        
        try:
            output_encrypted = input_file + '.enc'
            output_decrypted = input_file + '.dec'
            
            # 获取算法实例
            aes_algo = AES256Algorithm()
            
            # 1. 加密文件
            print(f"1. 加密文件...")
            encrypt_result = aes_algo.encrypt_with_random_key_chunked_to_file(
                input_file,
                output_encrypted,
                chunk_size=chunk_size
            )
            
            # 2. 读取加密文件并验证格式
            print(f"2. 检查加密文件格式...")
            try:
                ciphertext, file_iv, file_tag, _ = FileFormatHandler.read_aes_file(output_encrypted)
                
                # 比较标签
                encryptor_tag = encrypt_result.tag
                file_tag_hex = file_tag.hex()[:16] + "..."
                encryptor_tag_hex = encryptor_tag.hex()[:16] + "..."
                
                print(f"   文件中的标签: {file_tag_hex}")
                print(f"   加密器标签: {encryptor_tag_hex}")
                
                if file_tag != encryptor_tag:
                    print(f"   ❌ 标签不匹配!")
                    print(f"      文件标签长度: {len(file_tag)}")
                    print(f"      加密器标签长度: {len(encryptor_tag)}")
                    
                    # 打印完整标签进行比较
                    if len(file_tag) == len(encryptor_tag):
                        for i in range(0, min(32, len(file_tag)), 8):
                            file_part = file_tag[i:i+8].hex()
                            enc_part = encryptor_tag[i:i+8].hex()
                            print(f"      字节 {i}-{i+7}: 文件={file_part}, 加密器={enc_part}")
                else:
                    print(f"   ✅ 标签匹配")
                
                # 比较IV
                if file_iv != encrypt_result.iv:
                    print(f"   ❌ IV不匹配!")
                else:
                    print(f"   ✅ IV匹配")
                    
                # 检查文件大小
                actual_size = os.path.getsize(output_encrypted)
                expected_size = 4 + 12 + len(ciphertext) + 16  # 文件头 + IV + 密文 + 标签
                print(f"   实际文件大小: {actual_size:,} 字节")
                print(f"   预期文件大小: {expected_size:,} 字节")
                
                if actual_size != expected_size:
                    print(f"   ❌ 文件大小不匹配!")
                    print(f"      差值: {actual_size - expected_size} 字节")
                else:
                    print(f"   ✅ 文件大小正确")
                
                # 3. 手动解密验证
                print(f"3. 手动解密验证...")
                try:
                    # 使用加密器标签解密
                    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                    from cryptography.hazmat.backends import default_backend
                    
                    cipher1 = Cipher(
                        algorithms.AES(encrypt_result.key),
                        modes.GCM(file_iv, file_tag),  # 使用文件中的标签
                        backend=default_backend()
                    )
                    decryptor1 = cipher1.decryptor()
                    plaintext1 = decryptor1.update(ciphertext) + decryptor1.finalize()
                    
                    # 使用加密器标签解密
                    cipher2 = Cipher(
                        algorithms.AES(encrypt_result.key),
                        modes.GCM(file_iv, encryptor_tag),  # 使用加密器标签
                        backend=default_backend()
                    )
                    decryptor2 = cipher2.decryptor()
                    plaintext2 = decryptor2.update(ciphertext) + decryptor2.finalize()
                    
                    # 比较解密结果
                    if plaintext1 == test_data:
                        print(f"   ✅ 使用文件标签解密成功")
                    else:
                        print(f"   ❌ 使用文件标签解密失败")
                        
                    if plaintext2 == test_data:
                        print(f"   ✅ 使用加密器标签解密成功")
                    else:
                        print(f"   ❌ 使用加密器标签解密失败")
                        
                    # 如果两个解密都失败，可能是其他问题
                    if plaintext1 != test_data and plaintext2 != test_data:
                        print(f"   🔍 两个标签解密都失败，可能是密钥或IV问题")
                        
                except Exception as e:
                    print(f"   解密过程中出错: {e}")
                    import traceback
                    traceback.print_exc()
                
            except Exception as e:
                print(f"   读取加密文件失败: {e}")
                import traceback
                traceback.print_exc()
                
        finally:
            # 清理临时文件
            for f in [input_file, output_encrypted, output_decrypted]:
                if f and os.path.exists(f):
                    try:
                        os.unlink(f)
                    except:
                        pass

def test_file_structure():
    """详细检查AES文件结构"""
    print("\n" + "="*80)
    print("详细检查AES文件结构")
    print("="*80)
    
    # 创建小文件测试
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.test') as f:
        test_data = b"A" * 100  # 100字节测试数据
        f.write(test_data)
        input_file = f.name
    
    try:
        output_encrypted = input_file + '.enc'
        
        # 加密文件
        aes_algo = AES256Algorithm()
        result = aes_algo.encrypt_with_random_key_chunked_to_file(
            input_file,
            output_encrypted,
            chunk_size=1024 * 1024
        )
        
        # 读取原始文件字节进行分析
        with open(output_encrypted, 'rb') as f:
            all_bytes = f.read()
        
        print(f"加密文件总大小: {len(all_bytes)} 字节")
        print(f"文件内容分析:")
        
        # 解析文件结构
        header = all_bytes[0:4]
        print(f"  文件头 (0-3): {header.hex()} = '{header.decode('latin-1')}'")
        
        iv = all_bytes[4:16]
        print(f"  IV (4-15): {iv.hex()} (12字节)")
        
        # 计算密文和标签
        ciphertext = all_bytes[16:-16]
        tag = all_bytes[-16:]
        
        print(f"  密文 (16-{16+len(ciphertext)-1}): {len(ciphertext)} 字节")
        print(f"  标签 (最后16字节): {tag.hex()}")
        
        # 验证标签
        if tag == result.tag:
            print(f"  ✅ 文件中的标签与加密器标签匹配")
        else:
            print(f"  ❌ 标签不匹配!")
            print(f"     文件标签: {tag.hex()}")
            print(f"     加密器标签: {result.tag.hex()}")
        
        # 验证IV
        if iv == result.iv:
            print(f"  ✅ 文件中的IV与加密器IV匹配")
        else:
            print(f"  ❌ IV不匹配!")
            
    finally:
        for f in [input_file, output_encrypted]:
            if f and os.path.exists(f):
                try:
                    os.unlink(f)
                except:
                    pass

def test_cipher_gui_decrypt_logic():
    """测试cipher_gui.py中的解密逻辑"""
    print("\n" + "="*80)
    print("分析cipher_gui.py中的解密逻辑")
    print("="*80)
    
    # 检查cipher_gui.py中的_decrypt_file_chunked方法
    import inspect
    
    try:
        # 动态导入cipher_gui模块
        import cipher_gui
        source = inspect.getsource(cipher_gui.CipherGUI._decrypt_file_chunked)
        
        # 查找关键代码段
        lines = source.split('\n')
        
        print("关键代码分析:")
        for i, line in enumerate(lines):
            if 'ciphertext_size = os.path.getsize' in line or 'header_skip' in line:
                print(f"  行 {i+1}: {line.strip()}")
            if 'tag length' in line.lower() or '标签' in line:
                print(f"  行 {i+1}: {line.strip()}")
                
    except Exception as e:
        print(f"分析cipher_gui.py时出错: {e}")

def test_otp_large_file():
    """测试OTP大文件处理"""
    print("\n" + "="*80)
    print("测试OTP大文件处理")
    print("="*80)
    
    # 创建5MB测试文件
    file_size = 5 * 1024 * 1024
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.test') as f:
        test_data = secrets.token_bytes(file_size)
        f.write(test_data)
        input_file = f.name
    
    try:
        output_encrypted = input_file + '.enc'
        output_decrypted = input_file + '.dec'
        
        # 获取OTP算法实例
        otp_algo = get_algorithm(AlgorithmType.OTP)
        
        print(f"文件大小: {file_size:,} 字节")
        
        # 1. 分块加密
        print(f"1. 分块加密...")
        encrypt_result = otp_algo.encrypt_chunked_to_file(
            input_file,
            output_encrypted,
            chunk_size=1024 * 1024
        )
        
        print(f"   密钥长度: {len(encrypt_result.key):,} 字节")
        
        # 检查密钥长度
        if len(encrypt_result.key) == file_size:
            print(f"   ✅ 密钥长度与文件大小匹配")
        else:
            print(f"   ❌ 密钥长度不匹配!")
            print(f"      密钥长度: {len(encrypt_result.key):,} 字节")
            print(f"      文件大小: {file_size:,} 字节")
        
        # 2. 分块解密
        print(f"2. 分块解密...")
        decrypt_result = otp_algo.decrypt_chunked_from_file(
            output_encrypted,
            output_decrypted,
            encrypt_result.key,
            chunk_size=1024 * 1024
        )
        
        # 3. 验证解密结果
        with open(output_decrypted, 'rb') as f:
            decrypted_data = f.read()
        
        if decrypted_data == test_data:
            print(f"   ✅ OTP解密成功，文件内容匹配")
        else:
            print(f"   ❌ OTP解密失败，文件内容不匹配")
            print(f"      解密大小: {len(decrypted_data):,} 字节")
            print(f"      原始大小: {len(test_data):,} 字节")
            
            # 检查第一个不匹配的字节
            for i in range(min(len(decrypted_data), len(test_data))):
                if decrypted_data[i] != test_data[i]:
                    print(f"      第一个不匹配的字节在位置 {i}")
                    print(f"        解密: {decrypted_data[i]}")
                    print(f"        原始: {test_data[i]}")
                    break
        
    finally:
        for f in [input_file, output_encrypted, output_decrypted]:
            if f and os.path.exists(f):
                try:
                    os.unlink(f)
                except:
                    pass

def main():
    """主测试函数"""
    print("开始详细测试分块加密解密问题")
    print("="*80)
    
    try:
        test_aes_chunked_tag_issue()
        test_file_structure()
        test_cipher_gui_decrypt_logic()
        test_otp_large_file()
        
        print("\n" + "="*80)
        print("测试完成")
        print("="*80)
        
    except Exception as e:
        print(f"\n测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())