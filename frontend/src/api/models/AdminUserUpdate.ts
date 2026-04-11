/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserRole } from './UserRole';
import type { UserStatus } from './UserStatus';
/**
 * 管理员更新（可以修改角色、状态等敏感字段）
 */
export type AdminUserUpdate = {
    username?: (string | null);
    email?: (string | null);
    phone?: (string | null);
    avatar_url?: (string | null);
    bio?: (string | null);
    role?: (UserRole | null);
    status?: (UserStatus | null);
};

