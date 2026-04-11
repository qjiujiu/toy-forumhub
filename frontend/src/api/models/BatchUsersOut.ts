/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserOut } from './UserOut';
/**
 * 列表/分页返回
 * - total: 满足筛选条件的总数
 * - count: 当前这页返回的条数
 * - users: 当前页的用户列表
 */
export type BatchUsersOut = {
    total: number;
    count: number;
    users: Array<UserOut>;
};

