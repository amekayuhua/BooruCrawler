import functools
import time
import pandas as pd
import os
import glob


def timmer(func):
    def wrapper(*args):
        t1 = time.time()
        func(*args)
        t2 = time.time()
        print(f"总耗时: {t2 - t1:.2f} 秒")
    return wrapper


def async_timer(func):
    """
    专门用于测量 async 函数执行时间的装饰器
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"总耗时: {end_time - start_time:.2f} 秒")
        return result
        
    return wrapper
    
    
# ================= 配置区域 =================
# 停用词
STOP_WORDS = {
    "absurdres", "highres", "translated", "commentary_request", 
    "check_commentary", "bilibili", "weibo"
}
# ===========================================

def clean_tag(tag):
    """
    清洗标签逻辑：
    1. 去掉 rating:xxx, score:xxx, user:xxx 等元数据
    2. 去掉包含括号的标签 (通常是作品名或角色名备注) -> 可选
    """
    tag = tag.strip()
    
    # 过滤元数据标签 (包含冒号的通常是 meta tags)
    if ':' in tag:
        return None
        
    # 过滤一些纯数字或无意义字符
    if tag.isdigit():
        return None
        
    return tag
