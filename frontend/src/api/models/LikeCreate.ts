/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LikeTargetType } from './LikeTargetType';
/**
 * 创建点赞：
 * - 业务上通常由当前登录用户对某个帖子 / 评论点赞
 * - 一个用户对同一 target_type + target_id 只能有一条有效点赞记录
 */
export type LikeCreate = {
    user_id: string;
    target_type: LikeTargetType;
    target_id: string;
};

