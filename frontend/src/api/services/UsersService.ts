/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AdminUserUpdate } from '../models/AdminUserUpdate';
import type { BatchUsersAllOut } from '../models/BatchUsersAllOut';
import type { BatchUsersOut } from '../models/BatchUsersOut';
import type { UserAllOut } from '../models/UserAllOut';
import type { UserCreate } from '../models/UserCreate';
import type { UserOut } from '../models/UserOut';
import type { UserPasswordUpdate } from '../models/UserPasswordUpdate';
import type { UserStatsWithUserOut } from '../models/UserStatsWithUserOut';
import type { UserUpdate } from '../models/UserUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class UsersService {
    /**
     * Create User
     * 创建用户：
     * - 创建 user 表记录
     * - 初始化 user_statistics（关注数/粉丝数为 0）
     * @param requestBody
     * @returns UserOut Successful Response
     * @throws ApiError
     */
    public static createUserUsersPost(
        requestBody: UserCreate,
    ): CancelablePromise<UserOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/users/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Query Batch Users
     * 分页获取用户列表（只含基础信息）
     * @param page
     * @param pageSize
     * @returns BatchUsersOut Successful Response
     * @throws ApiError
     */
    public static queryBatchUsersUsersGet(
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchUsersOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/users/',
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
     * Get Users By Username
     * 根据用户名分页查询同名用户
     * @param username
     * @param page
     * @param pageSize
     * @returns BatchUsersOut Successful Response
     * @throws ApiError
     */
    public static getUsersByUsernameUsersUsernameUsernameGet(
        username: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchUsersOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/users/username/{username}',
            path: {
                'username': username,
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
     * Query User Basic
     * 根据 uid 查询用户基础信息（不含关注/粉丝统计）
     * @param uid
     * @returns UserOut Successful Response
     * @throws ApiError
     */
    public static queryUserBasicUsersIdUidGet(
        uid: string,
    ): CancelablePromise<UserOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/users/id/{uid}',
            path: {
                'uid': uid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Query User Profile
     * 用户详情：
     * - User 信息 + 关注数/粉丝数
     * @param uid
     * @returns UserStatsWithUserOut Successful Response
     * @throws ApiError
     */
    public static queryUserProfileUsersProfileUidGet(
        uid: string,
    ): CancelablePromise<UserStatsWithUserOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/users/profile/{uid}',
            path: {
                'uid': uid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update User
     * 普通用户更新自己的信息（不包含角色/状态）
     * @param uid
     * @param requestBody
     * @returns UserOut Successful Response
     * @throws ApiError
     */
    public static updateUserUsersInfoIdUidPut(
        uid: string,
        requestBody: UserUpdate,
    ): CancelablePromise<UserOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/users/info/id/{uid}',
            path: {
                'uid': uid,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin Update User
     * 管理员更新用户信息（可以修改角色/状态）
     * @param uid
     * @param requestBody
     * @returns UserOut Successful Response
     * @throws ApiError
     */
    public static adminUpdateUserUsersAdminIdUidPut(
        uid: string,
        requestBody: AdminUserUpdate,
    ): CancelablePromise<UserOut> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/users/admin/id/{uid}',
            path: {
                'uid': uid,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin Get User By Uid
     * 管理员根据 uid 获取用户详情：
     * - 不过滤软删除
     * - 返回 UserAllOut（字段更全）
     * @param uid
     * @returns UserAllOut Successful Response
     * @throws ApiError
     */
    public static adminGetUserByUidUsersAdminIdUidGet(
        uid: string,
    ): CancelablePromise<UserAllOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/users/admin/id/{uid}',
            path: {
                'uid': uid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Change Password
     * 修改密码（业务层会负责哈希和校验 old_password）
     * @param uid
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static changePasswordUsersPasswordIdUidPut(
        uid: string,
        requestBody: UserPasswordUpdate,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/users/password/id/{uid}',
            path: {
                'uid': uid,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Soft Delete User
     * 软删除用户
     * @param uid
     * @returns any Successful Response
     * @throws ApiError
     */
    public static softDeleteUserUsersSoftIdUidDelete(
        uid: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/users/soft/id/{uid}',
            path: {
                'uid': uid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Hard Deleted User
     * @param uid
     * @returns any Successful Response
     * @throws ApiError
     */
    public static hardDeletedUserUsersHardIdUidDelete(
        uid: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/users/hard/id/{uid}',
            path: {
                'uid': uid,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admin Get Users
     * 管理员：分页查看所有用户（包含软删）
     * @param page
     * @param pageSize
     * @returns BatchUsersAllOut Successful Response
     * @throws ApiError
     */
    public static adminGetUsersUsersAdminGet(
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchUsersAllOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/users/admin',
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
     * Admin Get Users By Username
     * 管理员根据用户名分页查询用户：
     * - 不过滤软删除
     * - 返回 BatchUsersAllOut
     * @param username
     * @param page
     * @param pageSize
     * @returns BatchUsersAllOut Successful Response
     * @throws ApiError
     */
    public static adminGetUsersByUsernameUsersAdminUsernameUsernameGet(
        username: string,
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchUsersAllOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/users/admin/username/{username}',
            path: {
                'username': username,
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
     * Admin List Deleted Users
     * 管理员查看所有软删除用户：
     * - deleted_at IS NOT NULL
     * @param page
     * @param pageSize
     * @returns BatchUsersAllOut Successful Response
     * @throws ApiError
     */
    public static adminListDeletedUsersUsersAdminDeletedGet(
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchUsersAllOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/users/admin/deleted',
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
     * Admin List Abnormal Status Users
     * 管理员查看异常状态用户（冻结与禁用）：
     * @param page
     * @param pageSize
     * @returns BatchUsersAllOut Successful Response
     * @throws ApiError
     */
    public static adminListAbnormalStatusUsersUsersAdminAbnormalStatusGet(
        page?: number,
        pageSize: number = 10,
    ): CancelablePromise<BatchUsersAllOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/users/admin/abnormal-status',
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
