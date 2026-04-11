/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * 取消关注（软删除）
 * - 若接口路径包含用户 ID，可以不需要 body
 */
export type FollowCancel = {
    user_id: string;
    followed_user_id: string;
};

