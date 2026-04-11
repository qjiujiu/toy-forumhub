-- 初始化数据库
CREATE DATABASE IF NOT EXISTS forumhub DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE forumhub;

-- 1. 创建用户表
CREATE TABLE IF NOT EXISTS users (
    _id INT AUTO_INCREMENT PRIMARY KEY,        -- 系统主键 ID
    uid VARCHAR(36) UNIQUE,                   -- 用户的业务主键（UUID）
    username VARCHAR(100) NOT NULL,           -- 用户昵称
    role SMALLINT DEFAULT 0,                  -- 用户角色（0: 普通用户，1: 审核员，2: 管理员）
    status SMALLINT DEFAULT 0,                -- 用户状态（0: 正常，1: 封禁，2: 冻结）
    phone VARCHAR(50) UNIQUE NOT NULL,        -- 电话
    password VARCHAR(255) NOT NULL,           -- 密码
    avatar_url VARCHAR(255),                  -- 用户头像 URL
    email VARCHAR(100) UNIQUE,                -- 邮箱（可为空）
    bio TEXT,                                 -- 用户简介

    last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 最后登录时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    -- 创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,    -- 更新时间
    deleted_at TIMESTAMP NULL                 -- 软删除时间戳
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 2. 创建用户统计表
CREATE TABLE IF NOT EXISTS user_stats (
    _id INT AUTO_INCREMENT PRIMARY KEY,          -- 系统主键（自增）
    user_id VARCHAR(36) NOT NULL,               -- 用户 ID (FK -> users.uid)
    following_count INT DEFAULT 0,              -- 用户的关注数
    followers_count INT DEFAULT 0,              -- 用户的粉丝数
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,  -- 更新时间
    
    CONSTRAINT fk_user_stats_user FOREIGN KEY (user_id) REFERENCES users(uid),  -- 外键：关联用户表
    UNIQUE (user_id)   -- 保证每个用户只有一条记录
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_user_stats_user_id ON user_stats (user_id);


-- 3. 创建关注表
CREATE TABLE IF NOT EXISTS follows (
    _id INT AUTO_INCREMENT PRIMARY KEY,              -- 系统主键（自增）
    user_id VARCHAR(36) NOT NULL,                    -- 关注者ID (FK -> users.uid)
    followed_user_id VARCHAR(36) NOT NULL,           -- 被关注者ID (FK -> users.uid)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
    deleted_at TIMESTAMP NULL,                       -- 软删除时间戳（用于取消关注）

    CONSTRAINT fk_follow_user FOREIGN KEY (user_id) REFERENCES users(uid),            -- 外键：关注者
    CONSTRAINT fk_followed_user FOREIGN KEY (followed_user_id) REFERENCES users(uid), -- 外键：被关注者
    CONSTRAINT uq_user_follow UNIQUE (user_id, followed_user_id)    -- 联合唯一约束：防止用户重复关注
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_follow_user ON follows (user_id);
CREATE INDEX idx_followed_user ON follows (followed_user_id);


-- 4. 创建帖子表
CREATE TABLE IF NOT EXISTS posts (
    _id INT AUTO_INCREMENT PRIMARY KEY,           -- 系统主键ID（自增）
    pid VARCHAR(36) UNIQUE,                       -- 业务主键PID（UUID）
    author_id VARCHAR(36) NOT NULL,               -- 作者 ID (Fk->users.uid)
    visibility SMALLINT DEFAULT 0,                -- 可见性（0:公开, 1:仅作者）
    publish_status SMALLINT DEFAULT 1,            -- 发布状态（0:草稿, 1:发布）
    review_status SMALLINT DEFAULT 0,             -- 审核状态（0:待审, 1:通过, 2:拒绝）
    reviewed_at TIMESTAMP NULL,                   -- 审核时间
    deleted_at TIMESTAMP NULL,                    -- 软删除时间戳

    FOREIGN KEY (author_id) REFERENCES users(uid)   -- 外键关联到用户表
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_posts_author_id ON posts (author_id);
CREATE INDEX idx_posts_visibility_review_status ON posts (visibility, review_status);
CREATE INDEX idx_posts_author_visibility ON posts (author_id, visibility);


-- 5. 创建帖子内容表
CREATE TABLE IF NOT EXISTS post_contents (
    _id INT AUTO_INCREMENT PRIMARY KEY,           -- 系统主键（自增）
    pcid VARCHAR(36) UNIQUE,                      -- 业务主键PID（UUID）
    post_id VARCHAR(36) NOT NULL UNIQUE,          -- 帖子 ID (FK -> posts.pid)
    title VARCHAR(255) NOT NULL,                  -- 帖子标题
    content TEXT NOT NULL,                        -- 帖子内容
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,    -- 创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,    -- 更新时间
    FOREIGN KEY (post_id) REFERENCES posts(pid)        -- 外键关联到帖子表
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 6. 创建帖子统计表
CREATE TABLE IF NOT EXISTS post_stats (
    _id INT AUTO_INCREMENT PRIMARY KEY,                -- 系统主键（自增）
    psid VARCHAR(36) NOT NULL UNIQUE,                  -- 业务主键（UUID，对外使用）
    post_id VARCHAR(36) NOT NULL UNIQUE,               -- 帖子业务主键（FK -> posts.pid）
    like_count INT DEFAULT 0,                          -- 点赞数
    comment_count INT DEFAULT 0,                       -- 帖子总评论数
    FOREIGN KEY (post_id) REFERENCES posts(pid)        -- 外键关联到帖子表
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 7. 创建评论表
CREATE TABLE IF NOT EXISTS comments (
    _id INT AUTO_INCREMENT PRIMARY KEY,               -- 系统主键（自增）
    cid VARCHAR(36) NOT NULL UNIQUE,                  -- 业务主键（UUID，对外使用）
    post_id VARCHAR(36) NOT NULL,                     -- 评论ID（FK -> posts.pid）
    comment_count INT DEFAULT 0,                      -- 评论的评论数
    author_id VARCHAR(36) NOT NULL,                   -- 评论作者业务主键（FK -> users.uid）
    parent_id VARCHAR(36) NULL,                       -- 父评论业务主键
    root_id VARCHAR(36) NULL,                         -- 顶级评论业务主键（整楼聚合）
    like_count INT NOT NULL DEFAULT 0,                -- 评论点赞数（物化计数）
    status TINYINT NOT NULL DEFAULT 0,                -- 0 正常 / 1 折叠
    review_status TINYINT NOT NULL DEFAULT 0,         -- 0 待审 / 1 通过 / 2 拒绝
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,                              -- 创建时间
    reviewed_at TIMESTAMP NULL,                                                           -- 审核时间
    deleted_at TIMESTAMP NULL,                                                            -- 软删除

    FOREIGN KEY (post_id) REFERENCES posts(pid),      -- 外键关联到帖子表
    FOREIGN KEY (author_id) REFERENCES users(uid)     -- 外键关联到用户表
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_comments_author ON comments(author_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);
CREATE INDEX idx_comments_root ON comments(root_id);


-- 8. 创建评论内容表
CREATE TABLE IF NOT EXISTS comment_contents (
    _id INT AUTO_INCREMENT PRIMARY KEY,             -- 系统主键（自增）
    ccid VARCHAR(36) NOT NULL UNIQUE,               -- 业务主键（UUID，对外使用）
    comment_id VARCHAR(36) NOT NULL,                -- 评论ID（FK -> comments.cid)
    content TEXT NOT NULL,                          -- 评论内容
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,                              -- 创建时间
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,  -- 更新时间
    FOREIGN KEY (comment_id) REFERENCES comments(cid)  -- 外键关联评论内容表
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 9. 创建点赞表
CREATE TABLE IF NOT EXISTS likes (
    _id INT AUTO_INCREMENT PRIMARY KEY,              -- 系统主键（自增）
    lid VARCHAR(36) UNIQUE,                          -- 业务主键（UUID）
    user_id VARCHAR(36) NOT NULL,                    -- 用户 ID (FK -> users.id)
    target_type SMALLINT,                            -- 点赞目标类型（0: 帖子, 1: 评论）
    target_id VARCHAR(36) NOT NULL,                  -- 点赞目标 ID（帖子 ID 或 评论 ID）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 点赞时间
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,  -- 更新时间
    deleted_at TIMESTAMP NULL,                       -- 软删除时间戳
    
    CONSTRAINT uq_likes_user_target UNIQUE (user_id, target_type, target_id),
    CONSTRAINT fk_likes_user FOREIGN KEY (user_id) REFERENCES users(uid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_likes_user_target_type ON likes (user_id, target_type);
CREATE INDEX idx_likes_target_type_id   ON likes (target_type, target_id);
CREATE INDEX idx_likes_created_at       ON likes (created_at);
