import os
import sys
import argparse
import socket
import subprocess
import ctypes
import pymysql
from pathlib import Path


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def get_mysql_config_path():
    """利用环境变量探测 my.ini 路径"""
    mysql_home = os.environ.get('MYSQL_HOME')
    if not mysql_home:
        print("[-] 错误: 未找到 MYSQL_HOME 环境变量，请确保已正确配置。")
        return None

    # 路径 A: MYSQL_HOME 目录下 (部分安装方式)
    # 路径 B: C:\ProgramData\MySQL\MySQL Server 8.0 (标准 Windows MSI 安装)
    # 路径 C: MYSQL_HOME 父目录下面的 Data 目录
    possible_paths = [
        Path(mysql_home) / "my.ini",
        Path(os.environ.get('ProgramData', 'C:/ProgramData')) / "MySQL" / "MySQL Server 8.0" / "my.ini",
        Path(os.environ.get('ProgramData', 'C:/ProgramData')) / "MySQL" / "MySQL Server 5.7" / "my.ini"
    ]

    for p in possible_paths:
        if p.exists():
            return p
    return None


# 设置远程访问, 允许同一个局域网下面的其它电脑访问本机的 MySQL 服务
def setup_remote_access(args):
    # 打开防火墙
    print(f"[*] 正在开启防火墙 3306 端口...")
    subprocess.run('netsh advfirewall firewall add rule name="MySQL_LAN_Access" dir=in action=allow protocol=TCP localport=3306',
                   shell=True, capture_output=True)

    # MySQL 授权
    print(f"[*] 正在为用户 {args.user} 授权...")
    try:
        conn = pymysql.connect(host='127.0.0.1', user='root', password=args.root_pass)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE USER IF NOT EXISTS '{args.user}'@'%' IDENTIFIED BY '{args.password}';")
            cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{args.user}'@'%' WITH GRANT OPTION;")
            cursor.execute("FLUSH PRIVILEGES;")
        conn.commit()
        conn.close()
        print(f"[+] 授权成功！")
    except Exception as e:
        print(f"[-] 授权失败: {e}")
        return

    # 3. 修改 my.ini 绑定地址
    config_path = get_mysql_config_path()
    if config_path:
        print(f"[*] 检测到配置文件: {config_path}")
        content = config_path.read_text(encoding='utf-8')
        if "bind-address=127.0.0.1" in content:
            new_content = content.replace("bind-address=127.0.0.1", "bind-address=0.0.0.0")
            config_path.write_text(new_content, encoding='utf-8')
            print("[+] 已将 bind-address 修改为 0.0.0.0")
        else:
            print("[?] 未发现限制或已修改，跳过配置文件编辑。")
    else:
        print("[!] 警告: 未能自动找到 my.ini，请手动确认配置。")

    print(f"\n[完成] 配置已就绪！")
    print(f"你的局域网 IP: {get_local_ip()}")
    print(f"连接信息: User={args.user}, Password={args.password}")


if __name__ == "__main__":
    if not is_admin():
        print("请以【管理员身份】运行此脚本。")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="MySQL 局域网共享一键配置工具")
    parser.add_argument("--root-pass", required=True, help="当前 MySQL root 用户的密码")
    parser.add_argument("--user", default="volmodaoist", help="要创建的远程访问用户名")
    parser.add_argument("--password", required=True, help="远程访问用户的密码")

    args = parser.parse_args()
    setup_remote_access(args)