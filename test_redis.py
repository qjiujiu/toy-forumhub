import redis

r = redis.Redis(
    host="127.0.0.1",
    port=6379,
    db=0,
    decode_responses=True,
    # password="你的密码"  # 如果有密码就加上
)

def main():
    # 测试连接
    print("PING:", r.ping())

    # 测试写入
    r.set("test_key", "hello_redis")
    print("GET test_key:", r.get("test_key"))

if __name__ == "__main__":
    main()
