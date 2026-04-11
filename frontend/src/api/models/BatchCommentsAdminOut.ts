/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CommentAdminOut } from './CommentAdminOut';
/**
 * 管理员视角的评论分页列表：
 * - 使用 CommentAdminOut，能看到 deleted_at 等信息
 */
export type BatchCommentsAdminOut = {
    total: number;
    count: number;
    items: Array<CommentAdminOut>;
};

