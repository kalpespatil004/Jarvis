export const userDataKeys = ['settings', 'logs', 'history', 'memory', 'cache'] as const;
export type UserDataKey = typeof userDataKeys[number];
