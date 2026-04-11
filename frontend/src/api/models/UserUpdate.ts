/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * 更新用户（部分字段可选）
 * - 注意：一般不允许在普通更新接口里直接改角色/状态（除非是管理员接口）
 * - 可根据你的权限体系拆成 UserUpdateSelf / AdminUserUpdate
 */
export type UserUpdate = {
    username?: (string | null);
    email?: (string | null);
    phone?: (string | null);
    avatar_url?: (string | null);
    bio?: (string | null);
};

