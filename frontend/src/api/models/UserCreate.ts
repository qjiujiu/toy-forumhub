/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserRole } from './UserRole';
import type { UserStatus } from './UserStatus';
/**
 * 创建用户（账号密码注册）
 */
export type UserCreate = {
    username: string;
    phone: string;
    email?: (string | null);
    avatar_url?: (string | null);
    bio?: (string | null);
    password: string;
    role?: (UserRole | null);
    status?: (UserStatus | null);
};

