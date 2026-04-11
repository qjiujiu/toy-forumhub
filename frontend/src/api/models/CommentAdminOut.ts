/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CommentContentOut } from './CommentContentOut';
import type { CommentStatus } from './CommentStatus';
import type { ReviewStatus } from './ReviewStatus';
import type { UserAllOut } from './UserAllOut';
/**
 * 管理员视角的评论信息：
 * - 在 CommentOut 的基础上额外包含 deleted_at
 */
export type CommentAdminOut = {
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
    author: UserAllOut;
    deleted_at?: (string | null);
};

