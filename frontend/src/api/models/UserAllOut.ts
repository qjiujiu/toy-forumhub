/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserRole } from './UserRole';
import type { UserStatus } from './UserStatus';
/**
 * 对外返回的用户所有信息（包含敏感字段，如 password、phone）
 */
export type UserAllOut = {
    uid: string;
    username: string;
    phone: string;
    email?: (string | null);
    avatar_url?: (string | null);
    bio?: (string | null);
    password: string;
    role: (UserRole | null);
    status: (UserStatus | null);
    last_login_at?: (string | null);
    created_at?: (string | null);
    updated_at?: (string | null);
    deleted_at?: (string | null);
};

