/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PostReviewStatus } from './PostReviewStatus';
/**
 * 审核员 / 管理员更新帖子审核状态
 * - 用于审核接口
 * - 审核状态可以从待审切换到通过或者拒绝，不可以从通过或拒绝切换回待审（业务层限制）
 */
export type PostReviewUpdate = {
    review_status: (PostReviewStatus | null);
    reviewed_at?: (string | null);
};

