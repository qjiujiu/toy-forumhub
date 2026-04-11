/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PostOut } from './PostOut';
/**
 * 帖子分页列表返回：
 * - total: 满足条件的总数
 * - count: 当前页返回的数量
 * - items: 帖子列表
 */
export type BatchPostsOut = {
    total: number;
    count: number;
    items: Array<PostOut>;
};

