/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PostContentOut } from './PostContentOut';
import type { PostReviewStatus } from './PostReviewStatus';
import type { PostStatsOut } from './PostStatsOut';
/**
 * 对外返回的基础帖子信息
 * - 不包含内容本身（PostContent 单独表）
 * - 可作为列表项 / 基础详情使用
 */
export type PostOut = {
    pid: string;
    author_id: string;
    post_content: PostContentOut;
    post_stats: PostStatsOut;
    visibility: number;
    publish_status: number;
    review_status: PostReviewStatus;
    reviewed_at?: (string | null);
};

