"""
加密算法模块
支持多种加密算法：
1. OTP (One-Time Pad) - 一次性密码本
2. AES256-GCM - AES256加密，GCM模式
"""

import os
import hashlib
from typing import Tuple, Optional, Union
from enum import Enum
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import secrets

class AlgorithmType(Enum):
    """加密算法类型"""
    OTP = "OTP"      # 一次性密码本
    AES256 = "AES"   # AES256-GCM

class KeyType(Enum):
    """密钥类型"""
    RANDOM = "random"     # 随机密钥
    PASSWORD = "password" # 密码派生密钥

@dataclass
class EncryptionResult:
    """加密结果"""
    ciphertext: bytes      # 密文
    key: bytes             # 密钥（随机密钥模式）
    iv: Optional[bytes]    # 初始化向量（AES模式）
    tag: Optional[bytes]   # 认证标签（GCM模式）
    salt: Optional[bytes]  # 盐值（密码模式）
    algorithm: AlgorithmType
    key_type: KeyType

@dataclass
class DecryptionResult:
    """解密结果"""
    plaintext: bytes       # 明文
    algorithm: AlgorithmType

class CipherAlgorithm:
    """加密算法基类"""
    
    def __init__(self, algorithm_type: AlgorithmType):
        self.algorithm_type = algorithm_type
    
    def encrypt(self, plaintext: bytes, **kwargs) -> EncryptionResult:
        """加密方法（子类实现）"""
        raise NotImplementedError
    
    def decrypt(self, ciphertext: bytes, **kwargs) -> DecryptionResult:
        """解密方法（子类实现）"""
        raise NotImplementedError
    
    @staticmethod
    def generate_salt(length: int = 16) -> bytes:
        """生成盐值"""
        return os.urandom(length)

class OTPAlgorithm(CipherAlgorithm):
    """OTP（一次性密码本）算法"""
    
    def __init__(self):
        super().__init__(AlgorithmType.OTP)
    
    def encrypt(self, plaintext: bytes, **kwargs) -> EncryptionResult:
        """
        使用OTP加密
        生成与明文长度相同的随机密钥
        """
        # 生成随机密钥
        key = os.urandom(len(plaintext))
        
        # 异或加密
        ciphertext = bytes([a ^ b for a, b in zip(plaintext, key)])
        
        return EncryptionResult(
            ciphertext=ciphertext,
            key=key,
            iv=None,
            tag=None,
            salt=None,
            algorithm=self.algorithm_type,
            key_type=KeyType.RANDOM
        )
    
    def decrypt(self, ciphertext: bytes, key: bytes, **kwargs) -> DecryptionResult:
        """
        使用OTP解密
        key: 密钥字节
        """
        if len(ciphertext) != len(key):
            raise ValueError("密文和密钥长度不匹配")
        
        # 异或解密
        plaintext = bytes([a ^ b for a, b in zip(ciphertext, key)])
        
        return DecryptionResult(
            plaintext=plaintext,
            algorithm=self.algorithm_type
        )

class AES256Algorithm(CipherAlgorithm):
    """AES256-GCM算法"""
    
    def __init__(self):
        super().__init__(AlgorithmType.AES256)
    
    def encrypt_with_random_key(self, plaintext: bytes, **kwargs) -> EncryptionResult:
        """
        使用随机密钥进行AES256-GCM加密
        """
        # 生成随机密钥
        key = secrets.token_bytes(32)  # AES256需要32字节密钥
        
        # 生成随机IV（12字节是GCM模式的推荐值）
        iv = secrets.token_bytes(12)
        
        # 创建加密器
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # 加密
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        return EncryptionResult(
            ciphertext=ciphertext,
            key=key,
            iv=iv,
            tag=encryptor.tag,
            salt=None,
            algorithm=self.algorithm_type,
            key_type=KeyType.RANDOM
        )
    
    def encrypt_with_password(self, plaintext: bytes, password: str, salt: Optional[bytes] = None, **kwargs) -> EncryptionResult:
        """
        使用密码进行AES256-GCM加密
        """
        if not password:
            raise ValueError("密码不能为空")
        
        # 生成盐值（如果未提供）
        if salt is None:
            salt = self.generate_salt()
        
        # 使用PBKDF2从密码派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # AES256需要32字节
            salt=salt,
            iterations=100000,  # 推荐迭代次数
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        
        # 生成随机IV
        iv = secrets.token_bytes(12)
        
        # 创建加密器
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # 加密
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        return EncryptionResult(
            ciphertext=ciphertext,
            key=key,  # 注意：这里返回派生后的密钥，但实际使用时不需要存储
            iv=iv,
            tag=encryptor.tag,
            salt=salt,
            algorithm=self.algorithm_type,
            key_type=KeyType.PASSWORD
        )
    
    def encrypt(self, plaintext: bytes, key_type: KeyType = KeyType.RANDOM, **kwargs) -> EncryptionResult:
        """
        加密方法
        key_type: 密钥类型（随机或密码）
        """
        if key_type == KeyType.RANDOM:
            return self.encrypt_with_random_key(plaintext, **kwargs)
        elif key_type == KeyType.PASSWORD:
            password = kwargs.get('password')
            if not password:
                raise ValueError("密码模式需要提供password参数")
            salt = kwargs.get('salt')
            # 从kwargs中移除已使用的参数，避免重复传递
            filtered_kwargs = kwargs.copy()
            if 'password' in filtered_kwargs:
                del filtered_kwargs['password']
            if 'salt' in filtered_kwargs:
                del filtered_kwargs['salt']
            return self.encrypt_with_password(plaintext, password, salt, **filtered_kwargs)
        else:
            raise ValueError(f"不支持的密钥类型: {key_type}")
    
    def decrypt_with_random_key(self, ciphertext: bytes, key: bytes, iv: bytes, tag: bytes) -> DecryptionResult:
        """
        使用随机密钥进行AES256-GCM解密
        """
        # 创建解密器
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # 解密
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return DecryptionResult(
            plaintext=plaintext,
            algorithm=self.algorithm_type
        )
    
    def decrypt_with_password(self, ciphertext: bytes, password: str, salt: bytes, iv: bytes, tag: bytes, **kwargs) -> DecryptionResult:
        """
        使用密码进行AES256-GCM解密
        """
        # 使用PBKDF2从密码派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        
        # 创建解密器
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # 解密
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return DecryptionResult(
            plaintext=plaintext,
            algorithm=self.algorithm_type
        )
    
    def decrypt(self, ciphertext: bytes, key_type: KeyType = KeyType.RANDOM, **kwargs) -> DecryptionResult:
        """
        解密方法
        """
        if key_type == KeyType.RANDOM:
            key = kwargs.get('key')
            iv = kwargs.get('iv')
            tag = kwargs.get('tag')
            if not all([key, iv, tag]):
                raise ValueError("随机密钥解密需要key、iv和tag参数")
            return self.decrypt_with_random_key(ciphertext, key, iv, tag)
        elif key_type == KeyType.PASSWORD:
            password = kwargs.get('password')
            salt = kwargs.get('salt')
            iv = kwargs.get('iv')
            tag = kwargs.get('tag')
            if not all([password, salt, iv, tag]):
                raise ValueError("密码解密需要password、salt、iv和tag参数")
            # 从kwargs中移除已使用的参数，避免重复传递
            filtered_kwargs = kwargs.copy()
            for param in ['password', 'salt', 'iv', 'tag']:
                if param in filtered_kwargs:
                    del filtered_kwargs[param]
            return self.decrypt_with_password(ciphertext, password, salt, iv, tag, **filtered_kwargs)
        else:
            raise ValueError(f"不支持的密钥类型: {key_type}")

class FileFormatHandler:
    """文件格式处理器"""
    
    @staticmethod
    def detect_algorithm(file_path: str) -> AlgorithmType:
        """
        检测文件使用的算法
        基于文件扩展名或文件内容
        """
        if file_path.endswith('.enc'):
            # 读取前4个字节检查算法标识
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    if header == b'AES\x00' or header == b'AES\x01':
                        return AlgorithmType.AES256
                    elif header == b'OTP\x00':
                        return AlgorithmType.OTP
            except:
                pass
            
            # 如果没有标识，默认为OTP（向后兼容）
            return AlgorithmType.OTP
        return AlgorithmType.AES256  # 其他扩展名默认为AES
    
    @staticmethod
    def read_otp_file(file_path: str) -> Tuple[bytes, AlgorithmType]:
        """读取OTP格式文件"""
        with open(file_path, 'rb') as f:
            ciphertext = f.read()
        return ciphertext, AlgorithmType.OTP
    
    @staticmethod
    def read_aes_file(file_path: str) -> Tuple[bytes, bytes, bytes, AlgorithmType]:
        """读取AES格式文件"""
        with open(file_path, 'rb') as f:
            header = f.read(4)  # 算法标识
            if header != b'AES\x00':
                raise ValueError("无效的AES文件格式")
            
            iv = f.read(12)  # 12字节IV
            # 读取密文和标签（最后16字节是标签）
            remaining = f.read()
            if len(remaining) < 16:
                raise ValueError("文件损坏：缺少认证标签")
            
            ciphertext = remaining[:-16]
            tag = remaining[-16:]
            
        return ciphertext, iv, tag, AlgorithmType.AES256
    
    @staticmethod
    def read_aes_file_with_salt(file_path: str) -> Tuple[bytes, bytes, bytes, bytes, AlgorithmType]:
        """读取带盐值的AES格式文件（密码模式）"""
        with open(file_path, 'rb') as f:
            header = f.read(4)  # 算法标识
            if header != b'AES\x01':  # 新版本标识
                raise ValueError("无效的带盐值AES文件格式")
            
            salt_len = int.from_bytes(f.read(1), 'big')
            salt = f.read(salt_len)
            iv = f.read(12)
            
            remaining = f.read()
            if len(remaining) < 16:
                raise ValueError("文件损坏：缺少认证标签")
            
            ciphertext = remaining[:-16]
            tag = remaining[-16:]
            
        return ciphertext, salt, iv, tag, AlgorithmType.AES256
    
    @staticmethod
    def write_otp_file(file_path: str, ciphertext: bytes):
        """写入OTP格式文件（保持向后兼容）"""
        with open(file_path, 'wb') as f:
            f.write(ciphertext)
    
    @staticmethod
    def write_aes_file(file_path: str, ciphertext: bytes, iv: bytes, tag: bytes):
        """写入AES格式文件"""
        with open(file_path, 'wb') as f:
            f.write(b'AES\x00')  # 算法标识
            f.write(iv)          # 12字节IV
            f.write(ciphertext)  # 密文
            f.write(tag)         # 16字节标签
    
    @staticmethod
    def write_aes_file_with_salt(file_path: str, ciphertext: bytes, salt: bytes, iv: bytes, tag: bytes):
        """写入带盐值的AES格式文件（密码模式）"""
        with open(file_path, 'wb') as f:
            f.write(b'AES\x01')  # 新版本算法标识
            f.write(len(salt).to_bytes(1, 'big'))  # 盐值长度（1字节）
            f.write(salt)        # 盐值
            f.write(iv)          # 12字节IV
            f.write(ciphertext)  # 密文
            f.write(tag)         # 16字节标签

# 算法工厂
def get_algorithm(algorithm_type: AlgorithmType) -> CipherAlgorithm:
    """获取算法实例"""
    if algorithm_type == AlgorithmType.OTP:
        return OTPAlgorithm()
    elif algorithm_type == AlgorithmType.AES256:
        return AES256Algorithm()
    else:
        raise ValueError(f"不支持的算法类型: {algorithm_type}")