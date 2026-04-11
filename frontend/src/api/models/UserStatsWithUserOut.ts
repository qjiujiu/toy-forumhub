/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserOut } from './UserOut';
/**
 * 用于用户主页 / 用户详情展示：
 * - 返回用户信息（UserOut） + 关注/粉丝数
 */
export type UserStatsWithUserOut = {
    user: UserOut;
    following_count: number;
    followers_count: number;
};

