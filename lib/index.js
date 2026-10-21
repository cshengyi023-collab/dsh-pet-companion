/**
 * dsh-pet-companion —— 宿主半侧（v0.1）
 *
 * 纯浏览器 UI 插件：面板逻辑全部在 lib/client.js。
 * 这里只保留一个空的 apply，作为 Loader 入口，让插件进入 profile 并发布浏览器 bundle。
 * 后续版本会在这里注册 HTTP 路由（前台窗口检测、LLM 代理等）。
 */
export const name = "pet-companion";
export const inject = [];

export function apply() {}
