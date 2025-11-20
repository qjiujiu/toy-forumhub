import logging

from sqlalchemy.orm import Session
from contextlib import contextmanager


""" 此处涉及的几个要素:
 
    - 数据事务

    
    - 几种异常抛出方式
        1. raise
            直接抛出当前异常，保留原始异常栈信息
        2. raise e       
            直接抛出当前异常，但是在之前的信息会丢失
        3. raise Exception("message") from e  
            附带额外的报错信息 "message"，同时保留原始异常作为上下文, 形成一大串异常链
        4. raise ValueError("message") 
            只抛出当前异常栈信息 (在此之前的调用栈信息不被抛出), 终端给出报错信息会相对少一点
            
    数据访问层只抛异常，不对异常进行过多的处理，异常的处理交给上层来解决(通常是接口层, 或者业务逻辑层, 取决于设计者)
"""


# 使用 Python上下文管理器来处理数据库事务, 在失败的时候自动回滚, 通过事务管理器来保证原子性
# 成功时提交事务(commit),  commit 完成之后才能调用 refresh 获取最新状态;  失败时回滚事务, 打印异常调用栈，并且重新向上抛出异常!
@contextmanager
def transaction(db: Session):
    try:
        yield db
        db.commit()
    except Exception as e:
        logging.exception(e)
        db.rollback()
        raise