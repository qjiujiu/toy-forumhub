/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LikeTargetType } from './LikeTargetType';
/**
 * 对外返回的点赞基础信息：
 * - 一般用于：查看我给哪些内容点过赞 / 某个内容被哪些人点赞等
 * - 不包含 deleted_at（仅展示有效点赞）
 */
export type LikeOut = {
    lid: string;
    user_id: string;
    target_type: LikeTargetType;
    target_id: string;
    created_at: string;
    updated_at: string;
};

