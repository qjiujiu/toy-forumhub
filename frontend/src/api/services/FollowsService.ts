/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BatchFollowsOut } from '../models/BatchFollowsOut';
import type { FollowCancel } from '../models/FollowCancel';
import type { FollowCreate } from '../models/FollowCreate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FollowsService {
    /**
     * Follow User
     * 关注用户：
     * - current_uid 关注 target_uid
     * - 更新双方的关注数/粉丝数
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static followUserFollowsPost(
        requestBody: FollowCreate,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/follows/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Cancel Follow
     * 取消关注：
     * - current_uid 取消关注 target_uid
     * - 更新双方的关注数/粉丝数
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static cancelFollowFollowsSoftDelete(
        requestBody: FollowCancel,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/follows/soft',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin Hard Delete Follow
     * 管理员硬删除关注关系：
     * - 要求该关注记录已经处于软删除状态（deleted_at 不为 NULL）
     * @param requestBody
     * @returns boolean Successful Response
     * @throws ApiError
     */
    public static adminHardDeleteFollowFollowsHardDelete(
        requestBody: FollowCancel,
    ): CancelablePromise<boolean> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/follows/hard',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Following
     * 我关注的人列表
     * @param uid
     * @param page
     * @param pageSize
     * @returns BatchFollowsOut Successful Response
     * @throws ApiError
     */
    public static listFollowingFollowsFollowingUidGet(
        uid: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchFollowsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/follows/following/{uid}',
            path: {
                'uid': uid,
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
     * List Followers
     * 我的粉丝列表
     * @param uid
     * @param page
     * @param pageSize
     * @returns BatchFollowsOut Successful Response
     * @throws ApiError
     */
    public static listFollowersFollowsFollowersUidGet(
        uid: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchFollowsOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/follows/followers/{uid}',
            path: {
                'uid': uid,
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
