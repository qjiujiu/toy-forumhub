
"""v2 Post Storage

帖子的数据访问层实现, 这个模块的设计说明了 “物理分表 != 代码分散” 

1) 聚合仓储（Aggregate Repository Pattern）
- 物理层: `posts` / `post_contents` / `post_stats` 依然是三张表。
- 逻辑层: repo 对外暴露“一个统一的 Post Repository 接口”，屏蔽底层三表细节。
- 好处: 上层（service/router/tests）只依赖一个抽象接口，避免业务层知道分表细节导致耦合, 
        如何判断耦合? 如果业务层的逻辑必须知道底下数据层是如何实现的, 无法简单调用数据访问对象的方法完成, 
        那么大概发生了耦合

2) 垂直拆分 / 冷热分离（Vertical Partitioning / Hot-Cold Split）
- `post_contents` 往往包含 `TEXT` 等大字段：写入一次、读取多次。
- `post_stats` 包含点赞/评论等高频更新计数：可能被频繁 `UPDATE`。
- 拆分可以降低: 写放大 & 锁竞争, 点赞不必去更新包含大字段的那一行。

3) 事务边界
- 对帖子聚合来说，一个“已创建的帖子”应同时具备：
  - 基础信息（post）
  - 内容（post_content）
  - 统计（post_stats）
- 因此 `create_post()` 必须在同一事务里创建三张表记录：
  - 要么三者都成功（commit），要么都失败（rollback）。
  - 这样可以避免出现 “主表有了，但内容/统计缺失” 这样的半成品状态。
"""
