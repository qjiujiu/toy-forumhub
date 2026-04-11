/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LikeTargetType } from './LikeTargetType';
/**
 * 管理员视角的点赞信息：
 * - 在 LikeOut 基础上额外暴露 deleted_at
 * - 可用于审计 / 数据排查
 */
export type LikeAdminOut = {
    lid: string;
    user_id: string;
    target_type: LikeTargetType;
    target_id: string;
    created_at: string;
    updated_at: string;
    deleted_at?: (string | null);
};

