import os
import subprocess

def init_db():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, "init_db.sql")
    
    if not os.path.exists(sql_file):
        print(f"Error: init_db.sql not found at {sql_file}")
        exit(1)

    print("开始执行数据库初始化...")
    print(f"执行文件: {sql_file}")

    # 使用 subprocess 调用 mysql 命令行客户端导入 SQL
    # 注意：这里默认使用 root 账户无密码直接登录（如果 MySQL 需要密码，需要额外处理）
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            process = subprocess.run(
                ["mysql", "-u", "root"],
                stdin=f,
                capture_output=True,
                text=True,
                check=True
            )
        print("数据库初始化成功！")
        print("你可以使用以下命令进入 MySQL 查看：")
        print("mysql -u root")
        print("USE forumhub;")
        print("SHOW TABLES;")
    except subprocess.CalledProcessError as e:
        print("数据库初始化失败，请检查 MySQL 服务是否启动以及相关错误信息。")
        print("错误信息:", e.stderr)
        exit(1)

if __name__ == "__main__":
    init_db()
