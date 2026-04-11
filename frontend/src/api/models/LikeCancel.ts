/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LikeTargetType } from './LikeTargetType';
/**
 * 取消点赞：
 * - 通常只需要 user_id + target_type + target_id 即可定位记录
 * - 如果你接口是 DELETE /likes/{lid}，那也可以不用这个模型
 */
export type LikeCancel = {
    user_id: string;
    target_type: LikeTargetType;
    target_id: string;
};

