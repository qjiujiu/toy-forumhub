/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BatchCommentsAdminOut } from '../models/BatchCommentsAdminOut';
import type { BatchCommentsOut } from '../models/BatchCommentsOut';
import type { CommentAdminOut } from '../models/CommentAdminOut';
import type { CommentCreate } from '../models/CommentCreate';
import type { CommentOut } from '../models/CommentOut';
import type { ReviewUpdate } from '../models/ReviewUpdate';
import type { StatusUpdate } from '../models/StatusUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CommentsService {
    /**
     * Create Comment
     * 创建评论：
     * - 校验用户是否存在
     * - 校验帖子是否存在（访客可见）
     * - 创建评论记录 + 评论内容记录
     * @param requestBody
     * @returns CommentOut Successful Response
     * @throws ApiError
     */
    public static createCommentCommentsPost(
        requestBody: CommentCreate,
    ): CancelablePromise<CommentOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/comments/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Comment
     * 获取单条评论（用户视角）：
     * - 不返回软删 / 折叠 / 审核拒绝的评论
     * @param cid
     * @returns CommentOut Successful Response
     * @throws ApiError
     */
    public static getCommentCommentsCidGet(
        cid: string,
    ): CancelablePromise<CommentOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/comments/{cid}',
            path: {
                'cid': cid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin Get Comment
     * 管理员查看单条评论：
     * - 可以看到软删除 / 折叠 / 审核拒绝等所有状态
     * @param cid
     * @returns CommentAdminOut Successful Response
     * @throws ApiError
     */
    public static adminGetCommentCommentsAdminCidGet(
        cid: string,
    ): CancelablePromise<CommentAdminOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/comments/admin/{cid}',
            path: {
                'cid': cid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Comment Thread
     * 查看某条评论所在整组对话（基于 root_id）——用户视角
     * @param cid
     * @returns BatchCommentsOut Successful Response
     * @throws ApiError
     */
    public static getCommentThreadCommentsThreadCidGet(
        cid: string,
    ): CancelablePromise<BatchCommentsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/comments/thread/{cid}',
            path: {
                'cid': cid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Comment Subtree
     * 查看从某条评论开始的子树对话（只看这一支）——用户视角
     * @param cid
     * @returns BatchCommentsOut Successful Response
     * @throws ApiError
     */
    public static getCommentSubtreeCommentsSubtreeCidGet(
        cid: string,
    ): CancelablePromise<BatchCommentsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/comments/subtree/{cid}',
            path: {
                'cid': cid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Comments By Post For User
     * 普通用户 / 前台：
     * - 查看某帖子的评论列表，只返回一级评论（不含软删 / 折叠 / 审核拒绝）
     * @param postId
     * @param page
     * @param pageSize
     * @returns BatchCommentsOut Successful Response
     * @throws ApiError
     */
    public static listCommentsByPostForUserCommentsPostPostIdGet(
        postId: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchCommentsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/comments/post/{post_id}',
            path: {
                'post_id': postId,
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
     * List Comments By Post For Reviewer
     * 审核员：
     * - 查看某帖子的所有审核状态评论（PENDING / APPROVED / REJECTED）
     * - 不含软删
     * @param postId
     * @param page
     * @param pageSize
     * @returns BatchCommentsAdminOut Successful Response
     * @throws ApiError
     */
    public static listCommentsByPostForReviewerCommentsReviewPostPostIdGet(
        postId: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchCommentsAdminOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/comments/review/post/{post_id}',
            path: {
                'post_id': postId,
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
     * List Comments By Post For Admin
     * 管理员：
     * - 查看某帖子的所有评论（含软删除、折叠、REJECTED）
     * @param postId
     * @param page
     * @param pageSize
     * @returns BatchCommentsAdminOut Successful Response
     * @throws ApiError
     */
    public static listCommentsByPostForAdminCommentsAdminPostPostIdGet(
        postId: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchCommentsAdminOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/comments/admin/post/{post_id}',
            path: {
                'post_id': postId,
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
     * Review Comment
     * 审核评论：
     * - 修改 review_status（PENDING / APPROVED / REJECTED）
     * - 不允许从通过/拒绝回到待审
     * @param cid
     * @param requestBody
     * @returns CommentAdminOut Successful Response
     * @throws ApiError
     */
    public static reviewCommentCommentsReviewCidPut(
        cid: string,
        requestBody: ReviewUpdate,
    ): CancelablePromise<CommentAdminOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/comments/review/{cid}',
            path: {
                'cid': cid,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Comment Status
     * 管理员更新评论显示状态：
     * - 折叠 / 取消折叠（status 字段）
     * @param cid
     * @param requestBody
     * @returns CommentAdminOut Successful Response
     * @throws ApiError
     */
    public static updateCommentStatusCommentsAdminStatusCidPut(
        cid: string,
        requestBody: StatusUpdate,
    ): CancelablePromise<CommentAdminOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/comments/admin/status/{cid}',
            path: {
                'cid': cid,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Soft Delete Comment
     * 普通用户软删除评论：
     * - 实际为设置 deleted_at
     * - 是否只能删除自己的评论，由上层鉴权控制
     * @param cid
     * @returns any Successful Response
     * @throws ApiError
     */
    public static softDeleteCommentCommentsSoftCidDelete(
        cid: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/comments/soft/{cid}',
            path: {
                'cid': cid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Restore Comment Api
     * 管理员恢复已软删除的评论
     * @param cid
     * @returns CommentAdminOut Successful Response
     * @throws ApiError
     */
    public static restoreCommentApiCommentsAdminRestoreCidPost(
        cid: string,
    ): CancelablePromise<CommentAdminOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/comments/admin/restore/{cid}',
            path: {
                'cid': cid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Hard Delete Comment
     * 管理员硬删除评论：
     * - 直接删除 comments 记录
     * - 通过 cascade 一并删除 CommentContent 等
     * @param cid
     * @returns any Successful Response
     * @throws ApiError
     */
    public static hardDeleteCommentCommentsHardCidDelete(
        cid: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/comments/hard/{cid}',
            path: {
                'cid': cid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
