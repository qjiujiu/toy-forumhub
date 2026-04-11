/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PostContentOut } from './PostContentOut';
import type { PostReviewStatus } from './PostReviewStatus';
export type PostReviewOut = {
    pid: string;
    author_id: string;
    post_content: PostContentOut;
    review_status: PostReviewStatus;
    reviewed_at?: (string | null);
};

