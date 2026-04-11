#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SQL_FILE="$SCRIPT_DIR/init_db.sql"

# 检查 SQL 文件是否存在
if [ ! -f "$SQL_FILE" ]; then
    echo "Error: init_db.sql not found at $SQL_FILE"
    exit 1
fi

echo "开始执行数据库初始化..."
echo "执行文件: $SQL_FILE"

# 执行 mysql 命令
mysql -u root < "$SQL_FILE"

if [ $? -eq 0 ]; then
    echo "数据库初始化成功！"
    echo "你可以使用以下命令进入 MySQL 查看："
    echo "mysql -u root -p"
    echo "USE forumhub;"
    echo "SHOW TABLES;"
else
    echo "数据库初始化失败，请检查 MySQL 服务是否启动以及相关错误信息。"
    exit 1
fi
