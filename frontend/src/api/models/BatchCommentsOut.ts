/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CommentOut } from './CommentOut';
/**
 * 评论分页列表返回结构：
 * - total: 满足条件的总评论数
 * - count: 当前页的评论条数
 * - items: 当前页的评论列表
 */
export type BatchCommentsOut = {
    total: number;
    count: number;
    items: Array<CommentOut>;
};

