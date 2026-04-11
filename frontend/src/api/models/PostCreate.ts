/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PostPublishStatus } from './PostPublishStatus';
import type { PostVisibility } from './PostVisibility';
/**
 * 创建帖子（业务上通常由作者自己调用）
 */
export type PostCreate = {
    author_id: string;
    title: string;
    content: string;
    visibility?: (PostVisibility | null);
    publish_status?: (PostPublishStatus | null);
};

