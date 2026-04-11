/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PostPublishStatus } from './PostPublishStatus';
import type { PostVisibility } from './PostVisibility';
/**
 * 作者更新帖子的可见性与发布状态
 * - 帖子的可见性可从所有人可见到仅作者可见随意切换
 * - 帖子的发布状态只可以由草稿到发布状态的转变（业务层限制）
 */
export type PostUpdate = {
    visibility?: (PostVisibility | null);
    publish_status?: (PostPublishStatus | null);
};

