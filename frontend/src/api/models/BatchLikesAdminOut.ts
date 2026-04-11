/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LikeAdminOut } from './LikeAdminOut';
/**
 * 点赞分页列表（管理员视角）：
 * - 可包含软删除记录
 */
export type BatchLikesAdminOut = {
    total: number;
    count: number;
    items: Array<LikeAdminOut>;
};

