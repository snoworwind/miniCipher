#!/usr/bin/env python3
"""
测试加密解密功能
"""

import os
import tempfile
from cipher_algorithms import (
    AlgorithmType, KeyType, get_algorithm, FileFormatHandler
)

def test_otp_encryption():
    """测试OTP加密解密"""
    print("测试OTP加密解密...")
    
    # 创建测试数据
    test_data = b"This is a test message for OTP encryption."
    
    # 获取OTP算法实例
    otp_algo = get_algorithm(AlgorithmType.OTP)
    
    # 加密
    encrypt_result = otp_algo.encrypt(test_data)
    print(f"  OTP加密完成: ciphertext长度={len(encrypt_result.ciphertext)}, key长度={len(encrypt_result.key)}")
    
    # 解密
    decrypt_result = otp_algo.decrypt(encrypt_result.ciphertext, key=encrypt_result.key)
    
    # 验证
    assert decrypt_result.plaintext == test_data, "OTP解密结果不匹配"
    assert decrypt_result.algorithm == AlgorithmType.OTP, "算法类型不匹配"
    print("  OTP测试通过 ✓")

def test_aes256_random_key():
    """测试AES256随机密钥加密解密"""
    print("测试AES256随机密钥加密解密...")
    
    # 创建测试数据
    test_data = b"This is a test message for AES256 encryption with random key."
    
    # 获取AES256算法实例
    aes_algo = get_algorithm(AlgorithmType.AES256)
    
    # 加密（随机密钥模式）
    encrypt_result = aes_algo.encrypt(test_data, key_type=KeyType.RANDOM)
    print(f"  AES256随机密钥加密完成: ciphertext长度={len(encrypt_result.ciphertext)}, key长度={len(encrypt_result.key)}, iv长度={len(encrypt_result.iv)}, tag长度={len(encrypt_result.tag)}")
    
    # 解密
    decrypt_result = aes_algo.decrypt(
        encrypt_result.ciphertext,
        key_type=KeyType.RANDOM,
        key=encrypt_result.key,
        iv=encrypt_result.iv,
        tag=encrypt_result.tag
    )
    
    # 验证
    assert decrypt_result.plaintext == test_data, "AES256随机密钥解密结果不匹配"
    assert decrypt_result.algorithm == AlgorithmType.AES256, "算法类型不匹配"
    print("  AES256随机密钥测试通过 ✓")

def test_aes256_password():
    """测试AES256密码加密解密"""
    print("测试AES256密码加密解密...")
    
    # 创建测试数据
    test_data = b"This is a test message for AES256 encryption with password."
    test_password = "MySecurePassword123!"
    
    # 获取AES256算法实例
    aes_algo = get_algorithm(AlgorithmType.AES256)
    
    # 生成盐值
    salt = aes_algo.generate_salt()
    
    # 加密（密码模式）
    encrypt_result = aes_algo.encrypt(
        test_data, 
        key_type=KeyType.PASSWORD,
        password=test_password,
        salt=salt
    )
    print(f"  AES256密码加密完成: ciphertext长度={len(encrypt_result.ciphertext)}, iv长度={len(encrypt_result.iv)}, tag长度={len(encrypt_result.tag)}")
    
    # 解密
    decrypt_result = aes_algo.decrypt(
        encrypt_result.ciphertext,
        key_type=KeyType.PASSWORD,
        password=test_password,
        salt=salt,
        iv=encrypt_result.iv,
        tag=encrypt_result.tag
    )
    
    # 验证
    assert decrypt_result.plaintext == test_data, "AES256密码解密结果不匹配"
    assert decrypt_result.algorithm == AlgorithmType.AES256, "算法类型不匹配"
    print("  AES256密码测试通过 ✓")

def test_file_formats():
    """测试文件格式处理"""
    print("测试文件格式处理...")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.enc') as tmp_otp:
        tmp_otp_path = tmp_otp.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.enc') as tmp_aes:
        tmp_aes_path = tmp_aes.name
    
    try:
        # 测试OTP文件格式
        test_data_otp = b"OTP test data"
        FileFormatHandler.write_otp_file(tmp_otp_path, test_data_otp)
        
        # 读取并验证
        read_data, algo = FileFormatHandler.read_otp_file(tmp_otp_path)
        assert read_data == test_data_otp, "OTP文件读取数据不匹配"
        assert algo == AlgorithmType.OTP, "OTP文件算法类型不匹配"
        print("  OTP文件格式测试通过 ✓")
        
        # 测试AES文件格式
        test_ciphertext = b"AES ciphertext data"
        test_iv = b"0123456789ab"  # 12字节
        test_tag = b"0123456789abcdef"  # 16字节
        
        FileFormatHandler.write_aes_file(tmp_aes_path, test_ciphertext, test_iv, test_tag)
        
        # 读取并验证
        read_ciphertext, read_iv, read_tag, read_algo = FileFormatHandler.read_aes_file(tmp_aes_path)
        assert read_ciphertext == test_ciphertext, "AES文件密文不匹配"
        assert read_iv == test_iv, "AES文件IV不匹配"
        assert read_tag == test_tag, "AES文件标签不匹配"
        assert read_algo == AlgorithmType.AES256, "AES文件算法类型不匹配"
        print("  AES文件格式测试通过 ✓")
        
        # 测试算法检测
        detected_otp = FileFormatHandler.detect_algorithm(tmp_otp_path)
        print(f"  OTP文件算法检测: {detected_otp}")
        
        detected_aes = FileFormatHandler.detect_algorithm(tmp_aes_path)
        print(f"  AES文件算法检测: {detected_aes}")
        
    finally:
        # 清理临时文件
        if os.path.exists(tmp_otp_path):
            os.unlink(tmp_otp_path)
        if os.path.exists(tmp_aes_path):
            os.unlink(tmp_aes_path)

def test_backward_compatibility():
    """测试向后兼容性"""
    print("测试向后兼容性...")
    
    # 创建临时文件（模拟旧版OTP文件）
    with tempfile.NamedTemporaryFile(delete=False, suffix='.enc') as tmp:
        tmp_path = tmp.name
        # 写入没有算法标识的数据（旧版格式）
        tmp.write(b"Old OTP ciphertext data")
    
    try:
        # 检测算法（应该检测为OTP）
        detected = FileFormatHandler.detect_algorithm(tmp_path)
        assert detected == AlgorithmType.OTP, f"向后兼容性测试失败: 期望OTP, 得到{detected}"
        print("  向后兼容性测试通过 ✓")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

def main():
    """主测试函数"""
    print("=" * 60)
    print("开始测试加密解密功能")
    print("=" * 60)
    
    try:
        test_otp_encryption()
        print()
        
        test_aes256_random_key()
        print()
        
        test_aes256_password()
        print()
        
        test_file_formats()
        print()
        
        test_backward_compatibility()
        print()
        
        print("=" * 60)
        print("所有测试通过！ ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())