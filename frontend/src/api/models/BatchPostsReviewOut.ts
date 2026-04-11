/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PostReviewOut } from './PostReviewOut';
/**
 * 帖子分页列表返回：
 * - total: 满足条件的总数
 * - count: 当前页返回的数量
 * - items: 帖子审核列表
 */
export type BatchPostsReviewOut = {
    total: number;
    count: number;
    items: Array<PostReviewOut>;
};

