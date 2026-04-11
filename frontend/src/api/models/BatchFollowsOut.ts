/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FollowUserOut } from './FollowUserOut';
/**
 * 分页列表返回（关注列表/粉丝列表）
 * - items: FollowUserOut 列表，表示对方用户的公开信息
 * - total: 满足条件数量
 * - count: 当前页数量
 */
export type BatchFollowsOut = {
    total: number;
    count: number;
    items: Array<FollowUserOut>;
};

