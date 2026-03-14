import base64
import datetime
import enum
import json
import os.path
import uuid

from Crypto.Cipher import AES
import argparse

# 初始化AES密码器
from PySide6.QtNetwork import QNetworkInterface

__lung_reconstruction_key = b'lung_reconstuct_'
__suffix = "zong"
__encrypt_mode = AES.MODE_CBC

lung_module = enum.auto()


def __generate_secret_key(_mac: str, _mode: enum, _date_text: str):
    """
    生成密钥
    :param _mac: mac地址，123456789012或12:34:56:78:90:12都行
    :param _mode: 0:胸肺模块
    :param _date_text:  日期字符串，格式必须为"20230802"之类的
    :return: [flag, secret_key]: flag:是否成功生成密钥；secret_key：密钥字符串
    """
    _secret_key = ""
    if _mode == lung_module:
        mode_key = __lung_reconstruction_key
    else:
        print("mode error")
        return False, _secret_key

    _mac = _mac.replace(":", "")
    if len(_mac) != 12:
        print("mac error")
        return False, _secret_key

    init_vector = bytes(_mac + __suffix, "gbk")
    # 判断字符串是不是8位纯数字
    if not _date_text.isdigit() and len(_date_text) != 8:
        print("date error")
        return False, _secret_key
    # 判断日期是否正确
    is_date_format_correct = False
    try:
        datetime.datetime.strptime(_date_text, "%Y%m%d")
        is_date_format_correct = True
    except ValueError:
        pass

    if not is_date_format_correct:
        print("date error")
        return False, _secret_key

    # 补位
    BLOCK_SIZE = AES.block_size
    text = _date_text + (BLOCK_SIZE - len(_date_text.encode()) % BLOCK_SIZE) * chr(
        BLOCK_SIZE - len(_date_text.encode()) % BLOCK_SIZE)
    # 创建AES对象
    cipher = AES.new(key=mode_key, mode=__encrypt_mode, IV=init_vector)
    # 利用AES对象 对数据进行加密
    encrypted_text = cipher.encrypt(text.encode())
    _secret_key = base64.b64encode(encrypted_text).decode()
    # 数据base64加密 url解码 utf-8
    return True, _secret_key


def decrypted_secret_key(encrypted_text: str, module: enum):
    """
    AES/CBC/PKCS5Padding 解密
    :param encrypted_text: 需要解密的数据
    :param module: 解密的模块
    :return: 解密后的数据
    """
    if len(encrypted_text) != 24:
        return False, ""
    key = __lung_reconstruction_key
    if module == lung_module:
        key = __lung_reconstruction_key

    init_vector = bytes(get_mac_address() + __suffix, "gbk")

    # 加密数据base64解密
    encrypted_text = base64.b64decode(encrypted_text)
    # AES 秘钥和偏移量 16位
    # 创建AES对象
    cipher = AES.new(key=key, mode=__encrypt_mode, IV=init_vector)
    # 使用AES对象对加密数据进行解密
    decrypted_text = cipher.decrypt(encrypted_text)
    # 去除补位
    dec_res = decrypted_text[:- ord(decrypted_text[len(decrypted_text) - 1:])]
    date_str = dec_res.decode()
    # 返回解码数据
    if date_str:
        try:
            # 将日期字符串转换为datetime对象
            date = datetime.datetime.strptime(date_str, '%Y%m%d')
            if date >= datetime.datetime.now():
                return True, date_str
            else:
                return False, date_str
        except ValueError:
            pass
    return False, "",


def get_mac_address():
    # 获取所有网络接口
    interfaces = QNetworkInterface.allInterfaces()

    # 遍历每个网络接口
    for interface in interfaces:
        # 获取MAC地址
        mac_address = interface.hardwareAddress()
        # 获取接口描述
        interface_description = interface.humanReadableName()
        if "以太网" in interface_description:
            return mac_address.replace(":", "")

    if len(interfaces) > 0:
        return interfaces[0].hardwareAddress().replace(":", "")
    return None


if __name__ == "__main__":
    # 定义命令行参数
    print("mac:", get_mac_address())
    flag,secret_key = __generate_secret_key(get_mac_address(), lung_module, "2030101")

    tmp_path = os.path.join(os.path.expanduser("~"), ".3dnav")
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    key_dic = {"lung_rec": secret_key}
    with open(os.path.join(tmp_path,'3dnav_key'), 'w') as f:
        json.dump(key_dic, f)
