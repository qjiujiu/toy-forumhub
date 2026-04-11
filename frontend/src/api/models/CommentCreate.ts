/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * 创建评论（业务上通常由用户自己调用）：
 */
export type CommentCreate = {
    post_id: string;
    author_id: string;
    content: string;
    parent_id?: (string | null);
    root_id?: (string | null);
};

