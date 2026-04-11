/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * 修改密码（单独接口，避免与普通更新混用）
 */
export type UserPasswordUpdate = {
    old_password?: (string | null);
    new_password: string;
};

