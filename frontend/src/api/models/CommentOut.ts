/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CommentContentOut } from './CommentContentOut';
import type { CommentStatus } from './CommentStatus';
import type { ReviewStatus } from './ReviewStatus';
/**
 * 对外返回的评论基础信息：
 * - 不包含正文内容（正文在 CommentContent 表）
 * - 常用于评论列表 / 详情
 */
export type CommentOut = {
    cid: string;
    post_id: string;
    author_id: string;
    comment_content: CommentContentOut;
    parent_id?: (string | null);
    root_id?: (string | null);
    comment_count: number;
    like_count: number;
    status: CommentStatus;
    review_status: ReviewStatus;
    reviewed_at?: (string | null);
};

