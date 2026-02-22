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
    
    def encrypt_chunked_to_file(self, input_file: str, output_file: str, chunk_size: int = 1024*1024) -> EncryptionResult:
        """
        OTP分块加密到文件
        input_file: 输入文件路径
        output_file: 输出文件路径
        chunk_size: 块大小（字节）
        """
        file_size = os.path.getsize(input_file)
        
        # 生成完整密钥（为了保持与现有API兼容性）
        key = os.urandom(file_size)
        
        # 分块读取、生成密钥块、加密、写入
        ciphertext_parts = []
        with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
            total_read = 0
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                
                # 获取对应的密钥块
                key_chunk = key[total_read:total_read + len(chunk)]
                
                # OTP加密：异或操作
                cipher_chunk = bytes([a ^ b for a, b in zip(chunk, key_chunk)])
                f_out.write(cipher_chunk)
                ciphertext_parts.append(cipher_chunk)
                
                total_read += len(chunk)
        
        ciphertext = b''.join(ciphertext_parts)
        
        return EncryptionResult(
            ciphertext=ciphertext,
            key=key,
            iv=None,
            tag=None,
            salt=None,
            algorithm=self.algorithm_type,
            key_type=KeyType.RANDOM
        )
    
    def encrypt_with_streaming_key(self, plaintext_generator, file_size: int) -> tuple:
        """
        流式OTP加密（生成器版本）
        plaintext_generator: 生成明文块的生成器
        file_size: 文件总大小
        """
        # 这里不实际实现，因为需要返回密钥
        # 保持向后兼容，使用完整密钥
        pass
    
    def decrypt_chunked_from_file(self, input_file: str, output_file: str, key: bytes, chunk_size: int = 1024*1024) -> DecryptionResult:
        """
        OTP分块解密从文件
        input_file: 输入文件路径
        output_file: 输出文件路径
        key: 密钥
        chunk_size: 块大小（字节）
        """
        file_size = os.path.getsize(input_file)
        if len(key) != file_size:
            raise ValueError(f"密钥长度({len(key)})与文件大小({file_size})不匹配")
        
        # 分块读取、获取密钥块、解密、写入
        with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
            total_read = 0
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                
                # 获取对应的密钥块
                key_chunk = key[total_read:total_read + len(chunk)]
                
                # OTP解密：异或操作
                plain_chunk = bytes([a ^ b for a, b in zip(chunk, key_chunk)])
                f_out.write(plain_chunk)
                
                total_read += len(chunk)
        
        # 读取解密后的明文
        with open(output_file, 'rb') as f:
            plaintext = f.read()
        
        return DecryptionResult(
            plaintext=plaintext,
            algorithm=self.algorithm_type
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
    
    def encrypt_with_random_key_chunked_to_file(self, input_file: str, output_file: str, chunk_size: int = 1024*1024) -> EncryptionResult:
        """
        随机密钥模式分块加密到文件
        input_file: 输入文件路径
        output_file: 输出文件路径
        chunk_size: 块大小（字节）
        """
        # 生成随机密钥和IV
        key = secrets.token_bytes(32)  # AES256需要32字节密钥
        iv = secrets.token_bytes(12)   # GCM推荐12字节IV
        
        # 创建加密器
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # 写入标准文件格式：文件头 + IV + 密文（分块）+ 标签
        with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
            # 写入文件头
            f_out.write(b'AES\x00')  # 标准AES格式标识
            # 写入IV
            f_out.write(iv)
            
            # 分块读取、加密、写入
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                
                cipher_chunk = encryptor.update(chunk)
                f_out.write(cipher_chunk)
        
        # 完成加密
        final_chunk = encryptor.finalize()
        if final_chunk:
            with open(output_file, 'ab') as f_out:
                f_out.write(final_chunk)
        
        # 写入标签
        with open(output_file, 'ab') as f_out:
            f_out.write(encryptor.tag)
        
        # 计算密文大小
        plaintext_size = os.path.getsize(input_file)
        
        # 为了返回结果，创建一个适当长度的占位密文
        ciphertext = b'\x00' * plaintext_size  # 占位符
        
        return EncryptionResult(
            ciphertext=ciphertext,
            key=key,
            iv=iv,
            tag=encryptor.tag,
            salt=None,
            algorithm=self.algorithm_type,
            key_type=KeyType.RANDOM
        )
    
    def encrypt_with_password_chunked_to_file(self, input_file: str, output_file: str, password: str, salt: Optional[bytes] = None, iv: Optional[bytes] = None, chunk_size: int = 1024*1024) -> EncryptionResult:
        """
        密码模式分块加密到文件
        input_file: 输入文件路径
        output_file: 输出文件路径
        password: 密码字符串
        salt: 盐值（可选）
        iv: 初始化向量（可选）
        chunk_size: 块大小（字节）
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
        
        # 生成IV（如果未提供）
        if iv is None:
            iv = secrets.token_bytes(12)
        
        # 创建加密器
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # 写入标准文件格式：文件头 + 盐值长度 + 盐值 + IV + 密文（分块）+ 标签
        with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
            # 写入文件头
            f_out.write(b'AES\x01')  # 带盐值的AES格式标识
            # 写入盐值长度（1字节）和盐值
            f_out.write(len(salt).to_bytes(1, 'big'))
            f_out.write(salt)
            # 写入IV
            f_out.write(iv)
            
            # 分块读取、加密、写入
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                
                cipher_chunk = encryptor.update(chunk)
                f_out.write(cipher_chunk)
        
        # 完成加密
        final_chunk = encryptor.finalize()
        if final_chunk:
            with open(output_file, 'ab') as f_out:
                f_out.write(final_chunk)
        
        # 写入标签
        with open(output_file, 'ab') as f_out:
            f_out.write(encryptor.tag)
        
        # 计算密文大小（等于原始文件大小，因为AES-GCM是流加密）
        plaintext_size = os.path.getsize(input_file)
        
        # 为了返回结果，创建一个适当长度的占位密文
        # 实际上ciphertext字段可能不被使用，但我们确保其长度正确
        ciphertext = b'\x00' * plaintext_size  # 占位符
        
        return EncryptionResult(
            ciphertext=ciphertext,
            key=key,
            iv=iv,
            tag=encryptor.tag,
            salt=salt,
            algorithm=self.algorithm_type,
            key_type=KeyType.PASSWORD
        )
    
    def decrypt_with_password_chunked_from_file(self, input_file: str, output_file: str, password: str, salt: bytes = None, iv: bytes = None, tag: bytes = None, chunk_size: int = 1024*1024) -> DecryptionResult:
        """
        密码模式分块解密从文件
        input_file: 输入文件路径
        output_file: 输出文件路径
        password: 密码字符串
        salt: 盐值（可选，如果文件是标准格式会自动读取）
        iv: 初始化向量（可选，如果文件是标准格式会自动读取）
        tag: 认证标签（可选，如果文件是标准格式会自动读取）
        chunk_size: 块大小（字节）
        
        支持两种文件格式：
        1. 标准格式：包含文件头(b'AES\x01')、盐值长度、盐值、IV、密文、标签
        2. 原始格式：只包含密文（需要提供salt、iv、tag参数）
        """
        if not password:
            raise ValueError("密码不能为空")
        
        # 检查文件格式
        with open(input_file, 'rb') as f:
            header = f.read(4)
        
        # 如果是标准格式，读取元数据
        if header == b'AES\x01':
            # 使用FileFormatHandler读取文件元数据
            ciphertext, file_salt, file_iv, file_tag, _ = FileFormatHandler.read_aes_file_with_salt(input_file)
            
            # 如果提供了参数，优先使用参数值（为了向后兼容）
            use_salt = salt if salt is not None else file_salt
            use_iv = iv if iv is not None else file_iv
            use_tag = tag if tag is not None else file_tag
            
            # 将密文写入临时文件，用于分块处理
            import tempfile
            temp_cipher_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
            temp_cipher_file.write(ciphertext)
            temp_cipher_file.close()
            
            input_file_to_decrypt = temp_cipher_file.name
            ciphertext_size = len(ciphertext)
        else:
            # 原始格式，必须提供salt、iv、tag
            if salt is None or iv is None or tag is None:
                raise ValueError("对于原始格式文件，必须提供salt、iv和tag参数")
            
            use_salt = salt
            use_iv = iv
            use_tag = tag
            input_file_to_decrypt = input_file
            ciphertext_size = os.path.getsize(input_file)
        
        # 使用PBKDF2从密码派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=use_salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        
        # 创建解密器
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(use_iv, use_tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # 分块读取、解密、写入
        plaintext_parts = []
        with open(input_file_to_decrypt, 'rb') as f_in, open(output_file, 'wb') as f_out:
            while True:
                chunk = f_in.read(chunk_size)
                if not chunk:
                    break
                
                plain_chunk = decryptor.update(chunk)
                plaintext_parts.append(plain_chunk)
                f_out.write(plain_chunk)
        
        # 完成解密
        final_chunk = decryptor.finalize()
        if final_chunk:
            plaintext_parts.append(final_chunk)
            with open(output_file, 'ab') as f_out:
                f_out.write(final_chunk)
        
        # 清理临时文件
        if 'temp_cipher_file' in locals() and os.path.exists(temp_cipher_file.name):
            os.unlink(temp_cipher_file.name)
        
        plaintext = b''.join(plaintext_parts)
        
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
        import logging
        
        logging.debug(f"检测文件算法: {file_path}")
        
        if file_path.endswith('.enc'):
            # 读取前4个字节检查算法标识
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    logging.debug(f"读取文件头: {header.hex() if header else '空文件'}")
                    
                    if header == b'AES\x00' or header == b'AES\x01':
                        logging.info(f"检测到AES256算法 (文件头: {header.hex()})")
                        return AlgorithmType.AES256
                    elif header == b'OTP\x00':
                        logging.info(f"检测到OTP算法 (文件头: {header.hex()})")
                        return AlgorithmType.OTP
                    else:
                        logging.warning(f"未知文件头: {header.hex() if header else '空'}, 默认为OTP算法")
            except Exception as e:
                logging.error(f"读取文件头时出错: {e}, 默认为OTP算法")
                pass
            
            # 如果没有标识，默认为OTP（向后兼容）
            logging.info(f"未检测到有效文件头，默认为OTP算法")
            return AlgorithmType.OTP
        
        logging.debug(f"文件扩展名非.enc，默认为AES256算法")
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
        import logging
        
        logging.debug(f"读取AES格式文件: {file_path}")
        
        with open(file_path, 'rb') as f:
            header = f.read(4)  # 算法标识
            logging.debug(f"AES文件头: {header.hex() if header else '空文件'}")
            
            if header != b'AES\x00':
                error_msg = f"无效的AES文件格式: 期望AES\\x00, 实际{header.hex() if header else '空'}"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            iv = f.read(12)  # 12字节IV
            logging.debug(f"读取IV: {iv.hex() if iv else '读取失败'}, 长度: {len(iv) if iv else 0}字节")
            
            # 读取密文和标签（最后16字节是标签）
            remaining = f.read()
            logging.debug(f"读取剩余数据: {len(remaining)}字节")
            
            if len(remaining) < 16:
                error_msg = f"文件损坏：缺少认证标签，剩余数据只有{len(remaining)}字节"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            ciphertext = remaining[:-16]
            tag = remaining[-16:]
            
            logging.info(f"AES文件解析成功: 密文大小={len(ciphertext)}字节, 标签大小={len(tag)}字节")
            logging.debug(f"标签内容: {tag.hex()[:32]}...")
            
        return ciphertext, iv, tag, AlgorithmType.AES256
    
    @staticmethod
    def read_aes_file_with_salt(file_path: str) -> Tuple[bytes, bytes, bytes, bytes, AlgorithmType]:
        """读取带盐值的AES格式文件（密码模式）"""
        import logging
        
        logging.debug(f"读取带盐值的AES格式文件: {file_path}")
        
        with open(file_path, 'rb') as f:
            header = f.read(4)  # 算法标识
            logging.debug(f"带盐值AES文件头: {header.hex() if header else '空文件'}")
            
            if header != b'AES\x01':  # 新版本标识
                error_msg = f"无效的带盐值AES文件格式: 期望AES\\x01, 实际{header.hex() if header else '空'}"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            salt_len = int.from_bytes(f.read(1), 'big')
            logging.debug(f"盐值长度: {salt_len}字节")
            
            salt = f.read(salt_len)
            logging.debug(f"读取盐值: {salt.hex()[:32] if salt else '读取失败'}..., 长度: {len(salt) if salt else 0}字节")
            
            iv = f.read(12)
            logging.debug(f"读取IV: {iv.hex() if iv else '读取失败'}, 长度: {len(iv) if iv else 0}字节")
            
            remaining = f.read()
            logging.debug(f"读取剩余数据: {len(remaining)}字节")
            
            if len(remaining) < 16:
                error_msg = f"文件损坏：缺少认证标签，剩余数据只有{len(remaining)}字节"
                logging.error(error_msg)
                raise ValueError(error_msg)
            
            ciphertext = remaining[:-16]
            tag = remaining[-16:]
            
            logging.info(f"带盐值AES文件解析成功: 密文大小={len(ciphertext)}字节, 盐值大小={len(salt)}字节, 标签大小={len(tag)}字节")
            logging.debug(f"标签内容: {tag.hex()[:32]}...")
            
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

class FileCipher:
    """
    高级文件加密/解密API
    整合所有文件操作、分块处理、密钥管理和错误处理逻辑
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        
    def encrypt_file(self, input_path, output_path, algorithm, key_type, password=None, 
                    progress_callback=None, **kwargs):
        """
        加密文件 - 统一入口，自动选择分块或完整处理
        
        参数:
            input_path: 输入文件路径
            output_path: 输出文件路径
            algorithm: 算法名称 ("OTP" 或 "AES256")
            key_type: 密钥类型 ("random" 或 "password")
            password: 密码（仅密码模式需要）
            progress_callback: 进度回调函数 function(progress_percent, message)
            **kwargs: 其他参数
            
        返回:
            dict: 包含加密结果和元数据
        """
        import os
        import logging
        from enum import Enum
        
        # 转换参数类型
        if algorithm == "OTP":
            algorithm_type = AlgorithmType.OTP
        else:
            algorithm_type = AlgorithmType.AES256
            
        if key_type == "random":
            key_type_enum = KeyType.RANDOM
        else:
            key_type_enum = KeyType.PASSWORD
        
        # 获取配置
        buffer_size_mb = 10  # 默认10MB
        if self.config_manager:
            try:
                buffer_size_mb = self.config_manager.get_buffer_size()
            except:
                pass
        
        chunk_size = buffer_size_mb * 1024 * 1024  # 转换为字节
        file_size = os.path.getsize(input_path)
        
        # 发送开始进度
        if progress_callback:
            progress_callback(0, f"开始加密，文件大小: {file_size:,} 字节")
        
        # 获取算法实例
        cipher_algorithm = get_algorithm(algorithm_type)
        
        # 根据文件大小选择处理方式
        if file_size <= chunk_size:
            # 小文件：完整读取处理
            if progress_callback:
                progress_callback(10, "读取文件...")
                
            with open(input_path, 'rb') as f:
                plaintext = f.read()
            
            if progress_callback:
                progress_callback(30, "加密中...")
            
            # 加密
            if algorithm_type == AlgorithmType.OTP:
                result = cipher_algorithm.encrypt(plaintext)
            else:  # AES256
                if key_type_enum == KeyType.RANDOM:
                    result = cipher_algorithm.encrypt(plaintext, key_type=key_type_enum)
                else:
                    if not password:
                        raise ValueError("密码模式需要提供密码")
                    result = cipher_algorithm.encrypt(
                        plaintext, 
                        key_type=key_type_enum,
                        password=password
                    )
            
            if progress_callback:
                progress_callback(70, "写入密文文件...")
            
            # 保存密文文件
            if algorithm_type == AlgorithmType.OTP:
                FileFormatHandler.write_otp_file(output_path, result.ciphertext)
            else:
                if key_type_enum == KeyType.PASSWORD:
                    FileFormatHandler.write_aes_file_with_salt(
                        output_path,
                        result.ciphertext,
                        result.salt,
                        result.iv,
                        result.tag
                    )
                else:
                    FileFormatHandler.write_aes_file(
                        output_path,
                        result.ciphertext,
                        result.iv,
                        result.tag
                    )
            
            if progress_callback:
                progress_callback(100, "加密完成")
                
        else:
            # 大文件：分块处理
            if progress_callback:
                progress_callback(10, f"开始分块加密，块大小: {buffer_size_mb}MB")
            
            if algorithm_type == AlgorithmType.OTP:
                # OTP分块加密
                result = cipher_algorithm.encrypt_chunked_to_file(
                    input_path,
                    output_path,
                    chunk_size=chunk_size
                )
                
            else:  # AES256
                if key_type_enum == KeyType.RANDOM:
                    # 随机密钥模式需要特殊处理
                    # 先加密到临时文件，然后使用正确格式写入
                    import tempfile
                    import shutil
                    
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
                    temp_path = temp_file.name
                    temp_file.close()
                    
                    try:
                        # 生成密钥和IV
                        import secrets
                        key = secrets.token_bytes(32)
                        iv = secrets.token_bytes(12)
                        
                        # 创建加密器
                        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                        from cryptography.hazmat.backends import default_backend
                        cipher = Cipher(
                            algorithms.AES(key),
                            modes.GCM(iv),
                            backend=default_backend()
                        )
                        encryptor = cipher.encryptor()
                        
                        # 分块处理
                        with open(input_path, 'rb') as f_in, open(temp_path, 'wb') as f_out:
                            total_read = 0
                            while True:
                                chunk = f_in.read(chunk_size)
                                if not chunk:
                                    break
                                
                                cipher_chunk = encryptor.update(chunk)
                                f_out.write(cipher_chunk)
                                total_read += len(chunk)
                                
                                # 更新进度
                                if progress_callback and total_read % (10 * 1024 * 1024) == 0:
                                    progress = (total_read / file_size) * 100
                                    progress_callback(10 + progress * 0.8, f"加密进度: {progress:.1f}%")
                        
                        # 完成加密
                        final_chunk = encryptor.finalize()
                        if final_chunk:
                            with open(temp_path, 'ab') as f_out:
                                f_out.write(final_chunk)
                        
                        # 写入标签
                        with open(temp_path, 'ab') as f_out:
                            f_out.write(encryptor.tag)
                        
                        # 现在用正确格式写入输出文件
                        # 临时文件中包含了密文 + tag，但我们需要只读取密文部分
                        with open(temp_path, 'rb') as f_in:
                            temp_content = f_in.read()
                        
                        # 获取文件大小，减去标签大小(16字节)得到纯密文
                        temp_size = len(temp_content)
                        if temp_size < 16:
                            raise ValueError("临时文件大小无效")
                        
                        # 分离密文和标签
                        ciphertext_only = temp_content[:-16]  # 纯密文部分
                        tag_from_temp = temp_content[-16:]    # 标签部分
                        
                        # 验证临时文件中的标签与encryptor.tag是否匹配
                        if tag_from_temp != encryptor.tag:
                            logging.warning(f"临时文件标签({tag_from_temp.hex()[:16]}...)与加密器标签({encryptor.tag.hex()[:16]}...)不匹配，使用加密器标签")
                        
                        FileFormatHandler.write_aes_file(
                            output_path,
                            ciphertext_only,  # 只写入纯密文，不包含标签
                            iv,
                            encryptor.tag
                        )
                        
                        result = EncryptionResult(
                            ciphertext=ciphertext_only,  # 使用纯密文部分
                            key=key,
                            iv=iv,
                            tag=encryptor.tag,
                            salt=None,
                            algorithm=algorithm_type,
                            key_type=key_type_enum
                        )
                        
                    finally:
                        # 清理临时文件
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                            
                else:  # 密码模式
                    result = cipher_algorithm.encrypt_with_password_chunked_to_file(
                        input_path,
                        output_path,
                        password,
                        chunk_size=chunk_size
                    )
            
            if progress_callback:
                progress_callback(100, "分块加密完成")
        
        # 准备返回结果
        return {
            'algorithm': algorithm,
            'key_type': key_type,
            'input_file': input_path,
            'output_file': output_path,
            'key': result.key if hasattr(result, 'key') else None,
            'iv': result.iv if hasattr(result, 'iv') else None,
            'tag': result.tag if hasattr(result, 'tag') else None,
            'salt': result.salt if hasattr(result, 'salt') else None,
            'key_file_needed': algorithm_type == AlgorithmType.OTP or 
                             (algorithm_type == AlgorithmType.AES256 and key_type_enum == KeyType.RANDOM)
        }
    
    def decrypt_file(self, input_path, output_path, algorithm, key_type, 
                    key_path=None, password=None, progress_callback=None, **kwargs):
        """
        解密文件 - 统一入口，自动选择分块或完整处理
        
        参数:
            input_path: 输入密文文件路径
            output_path: 输出明文文件路径
            algorithm: 算法名称 ("OTP" 或 "AES256")
            key_type: 密钥类型 ("random" 或 "password")
            key_path: 密钥文件路径（仅随机密钥模式需要）
            password: 密码（仅密码模式需要）
            progress_callback: 进度回调函数 function(progress_percent, message)
            **kwargs: 其他参数
            
        返回:
            dict: 包含解密结果和元数据
        """
        import os
        import logging
        
        # 检测文件算法
        try:
            detected_algorithm = FileFormatHandler.detect_algorithm(input_path)
        except Exception as e:
            # 如果检测失败，使用指定的算法
            if algorithm == "OTP":
                detected_algorithm = AlgorithmType.OTP
            else:
                detected_algorithm = AlgorithmType.AES256
        
        # 转换参数类型
        if algorithm == "OTP":
            algorithm_type = AlgorithmType.OTP
        else:
            algorithm_type = AlgorithmType.AES256
            
        if key_type == "random":
            key_type_enum = KeyType.RANDOM
        else:
            key_type_enum = KeyType.PASSWORD
        
        # 获取配置
        buffer_size_mb = 10  # 默认10MB
        if self.config_manager:
            try:
                buffer_size_mb = self.config_manager.get_buffer_size()
            except:
                pass
        
        chunk_size = buffer_size_mb * 1024 * 1024  # 转换为字节
        file_size = os.path.getsize(input_path)
        
        # 发送开始进度
        if progress_callback:
            progress_callback(0, f"开始解密，文件大小: {file_size:,} 字节")
        
        # 获取算法实例
        cipher_algorithm = get_algorithm(algorithm_type)
        
        # 根据文件大小选择处理方式
        if file_size <= chunk_size:
            # 小文件：完整读取处理
            if progress_callback:
                progress_callback(10, "读取密文文件...")
            
            if algorithm_type == AlgorithmType.OTP:
                # OTP解密
                ciphertext, _ = FileFormatHandler.read_otp_file(input_path)
                
                if not key_path:
                    raise ValueError("OTP解密需要密钥文件路径")
                
                if progress_callback:
                    progress_callback(30, "读取密钥文件...")
                
                key = self.load_key(key_path, "OTP")
                
                if progress_callback:
                    progress_callback(50, "解密中...")
                
                result = cipher_algorithm.decrypt(ciphertext, key=key)
                
                if progress_callback:
                    progress_callback(80, "写入解密文件...")
                
                with open(output_path, 'wb') as f:
                    f.write(result.plaintext)
                    
            else:  # AES256
                # 先读取文件头判断格式
                with open(input_path, 'rb') as f:
                    header = f.read(4)
                
                if header == b'AES\x01':
                    # 密码模式格式
                    ciphertext, salt, iv, tag, _ = FileFormatHandler.read_aes_file_with_salt(input_path)
                    
                    if not password:
                        raise ValueError("AES密码解密需要密码")
                    
                    if progress_callback:
                        progress_callback(30, "解密中...")
                    
                    result = cipher_algorithm.decrypt(
                        ciphertext,
                        key_type=KeyType.PASSWORD,
                        password=password,
                        salt=salt,
                        iv=iv,
                        tag=tag
                    )
                    
                else:
                    # 随机密钥模式格式
                    ciphertext, iv, tag, _ = FileFormatHandler.read_aes_file(input_path)
                    
                    if not key_path:
                        raise ValueError("AES随机密钥解密需要密钥文件")
                    
                    if progress_callback:
                        progress_callback(30, "读取密钥文件...")
                    
                    with open(key_path, 'rb') as f:
                        key = f.read()
                    
                    if progress_callback:
                        progress_callback(50, "解密中...")
                    
                    result = cipher_algorithm.decrypt(
                        ciphertext,
                        key_type=KeyType.RANDOM,
                        key=key,
                        iv=iv,
                        tag=tag
                    )
                
                if progress_callback:
                    progress_callback(80, "写入解密文件...")
                
                with open(output_path, 'wb') as f:
                    f.write(result.plaintext)
            
            if progress_callback:
                progress_callback(100, "解密完成")
                
        else:
            # 大文件：分块处理
            if progress_callback:
                progress_callback(10, f"开始分块解密，块大小: {buffer_size_mb}MB")
            
            if algorithm_type == AlgorithmType.OTP:
                # OTP分块解密
                if not key_path:
                    raise ValueError("OTP解密需要密钥文件路径")
                
                key = self.load_key(key_path, "OTP")
                
                result = cipher_algorithm.decrypt_chunked_from_file(
                    input_path,
                    output_path,
                    key,
                    chunk_size=chunk_size
                )
                
            else:  # AES256
                # 先读取文件头判断格式
                with open(input_path, 'rb') as f:
                    header = f.read(4)
                
                if header == b'AES\x01':
                    # 密码模式格式
                    if not password:
                        raise ValueError("AES密码解密需要密码")
                    
                    ciphertext, salt, iv, tag, _ = FileFormatHandler.read_aes_file_with_salt(input_path)
                    
                    # 将密文写入临时文件用于分块处理
                    import tempfile
                    temp_cipher_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
                    temp_cipher_file.write(ciphertext)
                    temp_cipher_file.close()
                    
                    try:
                        result = cipher_algorithm.decrypt_with_password_chunked_from_file(
                            temp_cipher_file.name,
                            output_path,
                            password,
                            salt=salt,
                            iv=iv,
                            tag=tag,
                            chunk_size=chunk_size
                        )
                    finally:
                        if os.path.exists(temp_cipher_file.name):
                            os.unlink(temp_cipher_file.name)
                            
                else:
                    # 随机密钥模式格式
                    if not key_path:
                        raise ValueError("AES随机密钥解密需要密钥文件")
                    
                    ciphertext, iv, tag, _ = FileFormatHandler.read_aes_file(input_path)
                    
                    with open(key_path, 'rb') as f:
                        key = f.read()
                    
                    # 将密文写入临时文件用于分块处理
                    import tempfile
                    temp_cipher_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
                    temp_cipher_file.write(ciphertext)
                    temp_cipher_file.close()
                    
                    try:
                        # 创建解密器
                        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                        from cryptography.hazmat.backends import default_backend
                        cipher = Cipher(
                            algorithms.AES(key),
                            modes.GCM(iv, tag),
                            backend=default_backend()
                        )
                        decryptor = cipher.decryptor()
                        
                        # 分块处理
                        with open(temp_cipher_file.name, 'rb') as f_in, open(output_path, 'wb') as f_out:
                            while True:
                                chunk = f_in.read(chunk_size)
                                if not chunk:
                                    break
                                
                                plain_chunk = decryptor.update(chunk)
                                f_out.write(plain_chunk)
                        
                        # 完成解密
                        final_chunk = decryptor.finalize()
                        if final_chunk:
                            with open(output_path, 'ab') as f_out:
                                f_out.write(final_chunk)
                        
                        result = DecryptionResult(
                            plaintext=b'',  # 不需要实际内容
                            algorithm=algorithm_type
                        )
                        
                    finally:
                        if os.path.exists(temp_cipher_file.name):
                            os.unlink(temp_cipher_file.name)
            
            if progress_callback:
                progress_callback(100, "分块解密完成")
        
        return {
            'algorithm': algorithm,
            'key_type': key_type,
            'input_file': input_path,
            'output_file': output_path,
            'success': True
        }
    
    def save_key(self, key, output_dir, base_name, algorithm, key_type):
        """
        智能保存密钥，根据配置和算法选择格式
        
        参数:
            key: 密钥字节
            output_dir: 输出目录
            base_name: 基础文件名
            algorithm: 算法名称
            key_type: 密钥类型
            
        返回:
            str: 密钥文件路径
        """
        import os
        
        # 获取配置
        otp_key_format = "hex"  # 默认十六进制格式
        if self.config_manager:
            try:
                otp_key_format = self.config_manager.get("basic.encryption.otp_key_format", "hex")
            except:
                pass
        
        if algorithm == "OTP":
            if otp_key_format == "binary":
                # 二进制格式
                key_file = os.path.join(output_dir, f"key_{base_name}.bin")
                with open(key_file, 'wb') as f:
                    f.write(key)
            else:
                # 十六进制格式（默认）
                key_file = os.path.join(output_dir, f"key_{base_name}.txt")
                with open(key_file, 'w') as f:
                    f.write(key.hex())
        else:  # AES256
            if key_type == "random":
                key_file = os.path.join(output_dir, f"key_{base_name}.key")
                with open(key_file, 'wb') as f:
                    f.write(key)
            else:
                # 密码模式不保存密钥文件
                return None
        
        return key_file
    
    def load_key(self, key_path, algorithm):
        """
        智能加载密钥，自动检测格式
        
        参数:
            key_path: 密钥文件路径
            algorithm: 算法名称
            
        返回:
            bytes: 密钥字节
        """
        import os
        
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"密钥文件不存在: {key_path}")
        
        file_ext = os.path.splitext(key_path)[1].lower()
        
        if file_ext == '.bin':
            # 二进制格式
            with open(key_path, 'rb') as f:
                key = f.read()
        elif file_ext == '.txt':
            # 十六进制格式
            with open(key_path, 'r') as f:
                key_hex = f.read().strip()
            key = bytes.fromhex(key_hex)
        else:
            # 尝试自动检测
            try:
                with open(key_path, 'rb') as f:
                    content = f.read()
                # 尝试解码为十六进制
                key_hex = content.decode('ascii').strip()
                key = bytes.fromhex(key_hex)
            except (UnicodeDecodeError, ValueError):
                # 否则当作二进制文件
                key = content
        
        return key
    
    def validate_password(self, password):
        """
        密码强度验证，集成配置要求
        
        参数:
            password: 密码字符串
            
        返回:
            tuple: (是否有效, 错误消息)
        """
        if not password:
            return False, "密码不能为空"
        
        min_length = 8  # 默认最小长度
        requires_strong = False  # 默认不要求强密码
        
        if self.config_manager:
            try:
                min_length = self.config_manager.get_password_min_length()
                requires_strong = self.config_manager.requires_strong_password()
            except:
                pass
        
        if len(password) < min_length:
            return False, f"密码太短，至少需要{min_length}个字符"
        
        if requires_strong:
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            
            if not (has_upper and has_lower and has_digit):
                return False, "密码强度不足，需要包含大小写字母和数字"
        
        return True, "密码有效"

# 算法工厂
def get_algorithm(algorithm_type: AlgorithmType) -> CipherAlgorithm:
    """获取算法实例"""
    if algorithm_type == AlgorithmType.OTP:
        return OTPAlgorithm()
    elif algorithm_type == AlgorithmType.AES256:
        return AES256Algorithm()
    else:
        raise ValueError(f"不支持的算法类型: {algorithm_type}")
