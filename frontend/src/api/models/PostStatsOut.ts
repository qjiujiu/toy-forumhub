/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * 返回帖子统计信息：
 * - 用于帖子详情
 * - 用于帖子列表时附带统计信息
 */
export type PostStatsOut = {
    psid: string;
    post_id: string;
    like_count: number;
    comment_count: number;
};

