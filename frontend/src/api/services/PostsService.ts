/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BatchPostsAdminOut } from '../models/BatchPostsAdminOut';
import type { BatchPostsOut } from '../models/BatchPostsOut';
import type { BatchPostsReviewOut } from '../models/BatchPostsReviewOut';
import type { PostAdminOut } from '../models/PostAdminOut';
import type { PostCreate } from '../models/PostCreate';
import type { PostGet } from '../models/PostGet';
import type { PostOut } from '../models/PostOut';
import type { PostReviewOut } from '../models/PostReviewOut';
import type { PostReviewUpdate } from '../models/PostReviewUpdate';
import type { PostUpdate } from '../models/PostUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class PostsService {
    /**
     * Create Post
     * 创建帖子：
     * - 在 posts 表创建记录
     * - 在 post_contents 表创建内容
     * - 在 post_stats 表创建统计记录
     * @param requestBody
     * @returns PostOut Successful Response
     * @throws ApiError
     */
    public static createPostPostsPost(
        requestBody: PostCreate,
    ): CancelablePromise<PostOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/posts/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Posts
     * 分页获取帖子列表（对外可见的帖子）
     * @param page
     * @param pageSize
     * @returns BatchPostsOut Successful Response
     * @throws ApiError
     */
    public static listPostsPostsGet(
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchPostsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/posts/',
            query: {
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Post
     * 通过帖子 ID 获取帖子详情（含内容 + 统计）
     * @param pid
     * @returns PostOut Successful Response
     * @throws ApiError
     */
    public static getPostPostsUserPidGet(
        pid: string,
    ): CancelablePromise<PostOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/posts/user/{pid}',
            path: {
                'pid': pid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Posts By Author
     * 根据作者 ID 分页获取该作者的帖子列表
     * （当前实现为“访客视角”，只返回对外可见的帖子）
     * @param requestBody
     * @param page
     * @param pageSize
     * @returns BatchPostsOut Successful Response
     * @throws ApiError
     */
    public static listPostsByAuthorPostsAuthorGet(
        requestBody: PostGet,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchPostsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/posts/author/',
            query: {
                'page': page,
                'page_size': pageSize,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Post
     * 作者更新帖子：
     * - 只允许更新 visibility / publish_status
     * - 审核状态不在这里修改
     * @param pid
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updatePostPostsStatusPidPidPut(
        pid: string,
        requestBody: PostUpdate,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/posts/status/pid/{pid}',
            path: {
                'pid': pid,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Soft Delete Post
     * 软删除帖子：
     * - 设置 deleted_at，不真正删除记录
     * @param pid
     * @returns any Successful Response
     * @throws ApiError
     */
    public static softDeletePostPostsSoftPidPidDelete(
        pid: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/posts/soft/pid/{pid}',
            path: {
                'pid': pid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Post Review
     * 审核详情：通过帖子 ID 查询帖子审核信息（附带内容）
     * @param pid
     * @returns PostReviewOut Successful Response
     * @throws ApiError
     */
    public static getPostReviewPostsReviewPidPidGet(
        pid: string,
    ): CancelablePromise<PostReviewOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/posts/review/pid/{pid}',
            path: {
                'pid': pid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Review Post
     * 审核帖子：
     * - 更新 review_status（并自动写入 reviewed_at）
     * - 不允许从 通过/拒绝 回到 待审
     * @param pid
     * @param requestBody
     * @returns PostReviewOut Successful Response
     * @throws ApiError
     */
    public static reviewPostPostsReviewPidPidPut(
        pid: string,
        requestBody: PostReviewUpdate,
    ): CancelablePromise<PostReviewOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/posts/review/pid/{pid}',
            path: {
                'pid': pid,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Post Reviews By Author
     * 审核员：通过作者 ID 查看该作者的所有帖子审核信息（包含所有审核状态）
     * @param authorId
     * @param page
     * @param pageSize
     * @returns BatchPostsReviewOut Successful Response
     * @throws ApiError
     */
    public static listPostReviewsByAuthorPostsReviewAuthorAuthorIdGet(
        authorId: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchPostsReviewOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/posts/review/author/{author_id}',
            path: {
                'author_id': authorId,
            },
            query: {
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Pending Review Posts
     * 审核员 / 管理员：查看所有待审帖子列表
     * @param page
     * @param pageSize
     * @returns BatchPostsReviewOut Successful Response
     * @throws ApiError
     */
    public static listPendingReviewPostsPostsReviewPendingGet(
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchPostsReviewOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/posts/review/pending',
            query: {
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin Get Post
     * 管理员：根据帖子 ID 查看帖子详情
     * - 包含软删除帖子
     * - 返回 PostAdminOut（包含审核状态、可见性、发布状态、deleted_at 等）
     * @param pid
     * @returns PostAdminOut Successful Response
     * @throws ApiError
     */
    public static adminGetPostPostsAdminPidPidGet(
        pid: string,
    ): CancelablePromise<PostAdminOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/posts/admin/pid/{pid}',
            path: {
                'pid': pid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin List All Posts
     * 管理员：查看所有帖子（含软删除）
     * @param page
     * @param pageSize
     * @returns BatchPostsAdminOut Successful Response
     * @throws ApiError
     */
    public static adminListAllPostsPostsAdminGet(
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchPostsAdminOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/posts/admin',
            query: {
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin List Deleted Posts
     * 管理员：查看所有软删除的帖子
     * @param page
     * @param pageSize
     * @returns BatchPostsAdminOut Successful Response
     * @throws ApiError
     */
    public static adminListDeletedPostsPostsAdminDeletedGet(
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchPostsAdminOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/posts/admin/deleted',
            query: {
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin List Posts By Author
     * 管理员：根据作者 ID 查看该作者的所有帖子（含软删）
     * @param authorId
     * @param page
     * @param pageSize
     * @returns BatchPostsAdminOut Successful Response
     * @throws ApiError
     */
    public static adminListPostsByAuthorPostsAdminAuthorAuthorIdGet(
        authorId: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchPostsAdminOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/posts/admin/author/{author_id}',
            path: {
                'author_id': authorId,
            },
            query: {
                'page': page,
                'page_size': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin Hard Delete Post
     * 管理员：硬删除帖子
     * - 直接从 posts 表移除
     * - 依赖 ORM cascade 删除内容 / 统计 / 评论等
     * @param pid
     * @returns any Successful Response
     * @throws ApiError
     */
    public static adminHardDeletePostPostsAdminHardPidDelete(
        pid: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/posts/admin/hard/{pid}',
            path: {
                'pid': pid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin Restore Post
     * 管理员恢复软删除帖子：
     * - 必须是软删除状态才能恢复
     * - 未软删除 → 返回 False
     * - 帖子不存在 → 404
     * @param pid
     * @returns any Successful Response
     * @throws ApiError
     */
    public static adminRestorePostPostsAdminRestorePidPut(
        pid: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/posts/admin/restore/{pid}',
            path: {
                'pid': pid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
