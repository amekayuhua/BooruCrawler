import logging
from rich.logging import RichHandler
from rich.console import Console
# from tqdm import tqdm

# class TqdmLoggingHandler(logging.Handler):
    # """自定义处理器：让所有日志都通过 tqdm.write 输出"""
    # def emit(self, record):
    #     try:
    #         msg = self.format(record)
    #         tqdm.write(msg)
    #         self.flush()
    #     except Exception:
    #         self.handleError(record)
    
console = Console()

def setup_global_logger(level: str="INFO"):
    """初始化全局日志配置"""
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }  
    
    # actual_level = level_mapping.get(level.upper(), logging.INFO)
    
    # root_logger = logging.getLogger()
    # root_logger.setLevel(actual_level)
    
    # if root_logger.hasHandlers():
    #     root_logger.handlers.clear()

    # tqdm_handler = TqdmLoggingHandler()
    
    # formatter = logging.Formatter(
    #     fmt='[%(levelname)s] %(asctime)s | %(name)s | %(message)s',
    #     datefmt='%H:%M:%S'
    # )
    # tqdm_handler.setFormatter(formatter)
    
    # root_logger.addHandler(tqdm_handler)
    
    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        markup=True,
        show_path=True
    )

    # 2. 全局配置
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[rich_handler]
    )
    
    # ================= 屏蔽第三方库的垃圾日志 =================
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    # ==========================================================