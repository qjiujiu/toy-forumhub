/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LikeOut } from './LikeOut';
/**
 * 点赞分页列表（普通场景）：
 * - 用于 “某用户点赞列表” / “某内容点赞用户列表” 等
 */
export type BatchLikesOut = {
    total: number;
    count: number;
    items: Array<LikeOut>;
};

