import functools
import time
import config


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


def output_name() -> str:
    if config.ARTIST_NAME:
        name = config.ARTIST_NAME
        return name
    
    else:
        name = config.SEARCH_TAGS
        return name