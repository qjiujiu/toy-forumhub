/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserOut } from './UserOut';
/**
 * 在关注列表 / 粉丝列表展示中，更实用的结构：
 * - 返回对方用户的基础信息
 * - 可扩展是否互关等逻辑
 */
export type FollowUserOut = {
    user: UserOut;
    is_mutual?: (boolean | null);
};

