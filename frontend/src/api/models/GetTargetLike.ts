/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LikeTargetType } from './LikeTargetType';
/**
 * 获取目标类型点赞的请求体：“某内容点赞用户列表”
 * - 不包含软删除
 */
export type GetTargetLike = {
    target_type: LikeTargetType;
    target_id: string;
};

