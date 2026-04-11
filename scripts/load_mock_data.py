import json
import os
import subprocess

def load_json(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_sql():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mock_dir = os.path.join(script_dir, 'mock_data')
    
    # 定义由于外键约束所需考虑的插入顺序
    tables = [
        'users', 
        'user_stats', 
        'posts', 
        'post_contents', 
        'post_stats'
    ]
    
    sql_statements = []
    
    for table in tables:
        filepath = os.path.join(mock_dir, f"{table}.json")
        data = load_json(filepath)
        for row in data:
            columns = ", ".join([f"`{k}`" for k in row.keys()])
            
            values = []
            for v in row.values():
                if isinstance(v, str):
                    # 处理 SQL 注入需要的单引号等转义问题
                    escaped_v = v.replace("\\", "\\\\").replace("'", "''")
                    values.append(f"'{escaped_v}'")
                elif v is None:
                    values.append("NULL")
                else:
                    values.append(str(v))
                    
            vals = ", ".join(values)
            # 使用 INSERT IGNORE 防止重复插入报错
            sql = f"INSERT IGNORE INTO `{table}` ({columns}) VALUES ({vals});"
            sql_statements.append(sql)
            
    return "\n".join(sql_statements)

def insert_mock_data():
    sql = generate_sql()
    if not sql.strip():
        print("没有生成任何 SQL 数据，请检查 mock_data 目录下是否有数据文件。")
        return

    print("开始生成 Mock 数据 SQL 语句并插入数据库 (如果数据已存在则忽略)...")
    
    # 结合选用库 USE forumhub
    final_sql = "USE forumhub;\n" + sql

    try:
        # 使用 subprocess 调用 mysql 并传入拼接的 SQL，不使用密码
        process = subprocess.run(
            ["mysql", "-u", "root"],
            input=final_sql,
            capture_output=True,
            text=True,
            check=True
        )
        print("Mock 数据导入成功！")
    except subprocess.CalledProcessError as e:
        print("数据导入失败，请检查 MySQL 服务或 SQL 语句！")
        print("错误信息:", e.stderr)
        exit(1)

if __name__ == '__main__':
    insert_mock_data()
