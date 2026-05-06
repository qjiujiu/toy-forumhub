
"""v2 User Storage

数据数据访问层实现。

1) 为什么 user 与 user_stats 物理分表仍要“一个 repo”
- 物理层拆表的动机通常是：字段访问频率/更新频率差异, e.g. 统计计数高频变动, 
  但从业务语义看，`user` 与 `user_stats` 往往一起出现（用户主页、关注/粉丝展示等）。
- 因此数据访问采用聚合仓储, 把多个数据表的逻辑打包在一起, 对上层只暴露 `IUserRepository`，内部同时读写两张表。

2) 接口抽象：Protocol + Duck Typing
- `IUserRepository` 采用 Protocol 描述“行为契约”。
- 好处在于 mock repo 与 SQLAlchemy repo 不必继承同一基类，只要实现同名方法即可, 其它模块也采用了同样的思路

3) PATCH 语义（Partial Update）
- 更新接口遵循 PATCH 习惯：只更新显式传入的字段，不会把未传字段清空。
- Pydantic/ORM 组合中常用 `model_dump(exclude_none=True)` 来构造“只含变更字段”的 patch。

"""
