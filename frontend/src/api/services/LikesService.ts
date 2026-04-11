/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BatchLikesAdminOut } from '../models/BatchLikesAdminOut';
import type { BatchLikesOut } from '../models/BatchLikesOut';
import type { GetTargetLike } from '../models/GetTargetLike';
import type { LikeCancel } from '../models/LikeCancel';
import type { LikeCreate } from '../models/LikeCreate';
import type { LikeOut } from '../models/LikeOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class LikesService {
    /**
     * Like Target
     * 点赞目标（帖子/评论）：
     *
     * - 校验用户是否存在
     * - 校验帖子 / 评论是否存在
     * - 调用 like_svc.like_target 完成点赞 + 更新计数
     * @param requestBody
     * @returns LikeOut Successful Response
     * @throws ApiError
     */
    public static likeTargetLikesPost(
        requestBody: LikeCreate,
    ): CancelablePromise<LikeOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/likes/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel Like
     * 取消点赞（软删除）：
     *
     * - 校验用户是否存在
     * - 调用 like_svc.cancel_like 完成取消 + 更新计数
     * @param requestBody
     * @returns boolean Successful Response
     * @throws ApiError
     */
    public static cancelLikeLikesCancelPost(
        requestBody: LikeCancel,
    ): CancelablePromise<boolean> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/likes/cancel',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Likes By Target
     * 查询某个目标（帖子 / 评论）的所有 **有效** 点赞记录（分页）
     * - 不包含软删除
     * @param requestBody
     * @param page
     * @param pageSize
     * @returns BatchLikesOut Successful Response
     * @throws ApiError
     */
    public static listLikesByTargetLikesByTargetGet(
        requestBody: GetTargetLike,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchLikesOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/likes/by-target',
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
     * List Likes By User
     * 查询某个用户的所有 **有效** 点赞记录（分页）
     * - 包含该用户对帖子和评论的点赞
     * @param userId
     * @param page
     * @param pageSize
     * @returns BatchLikesOut Successful Response
     * @throws ApiError
     */
    public static listLikesByUserLikesByUserUserIdGet(
        userId: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchLikesOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/likes/by-user/{user_id}',
            path: {
                'user_id': userId,
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
     * Admin List Likes By Target
     * 管理员：查询某个目标的所有点赞记录（包含软删除）
     * @param requestBody
     * @param page
     * @param pageSize
     * @returns BatchLikesAdminOut Successful Response
     * @throws ApiError
     */
    public static adminListLikesByTargetLikesAdminByTargetGet(
        requestBody: GetTargetLike,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchLikesAdminOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/likes/admin/by-target',
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
     * Admin List Likes By User
     * 管理员：查询某个用户的所有点赞记录（包含软删除）
     * @param userId
     * @param page
     * @param pageSize
     * @returns BatchLikesAdminOut Successful Response
     * @throws ApiError
     */
    public static adminListLikesByUserLikesAdminByUserUserIdGet(
        userId: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchLikesAdminOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/likes/admin/by-user/{user_id}',
            path: {
                'user_id': userId,
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
}
