import logging
from tqdm import tqdm

class TqdmLoggingHandler(logging.Handler):
    """自定义处理器：让所有日志都通过 tqdm.write 输出"""
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)

def setup_global_logger(level=logging.DEBUG):
    """初始化全局日志配置"""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    tqdm_handler = TqdmLoggingHandler()
    
    formatter = logging.Formatter(
        fmt='[%(levelname)s] %(asctime)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    tqdm_handler.setFormatter(formatter)
    
    root_logger.addHandler(tqdm_handler)
    
    # ================= 屏蔽第三方库的垃圾日志 =================
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    # logging.getLogger('wordcloud').setLevel(logging.WARNING)
    # ==========================================================