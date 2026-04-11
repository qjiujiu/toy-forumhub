/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserRole } from './UserRole';
import type { UserStatus } from './UserStatus';
/**
 * 对外返回的用户基础信息（不包含敏感字段，如 password、phone 可按你需求放/不放）
 */
export type UserOut = {
    uid: string;
    username: string;
    avatar_url?: (string | null);
    role?: UserRole;
    bio?: (string | null);
    status?: UserStatus;
};

