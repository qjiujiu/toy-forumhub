/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PostContentOut } from './PostContentOut';
import type { PostReviewStatus } from './PostReviewStatus';
import type { PostStatsOut } from './PostStatsOut';
export type PostAdminOut = {
    pid: string;
    author_id: string;
    post_content: PostContentOut;
    post_stats: PostStatsOut;
    review_status: PostReviewStatus;
    reviewed_at?: (string | null);
    visibility: number;
    publish_status: number;
    deleted_at?: (string | null);
};

