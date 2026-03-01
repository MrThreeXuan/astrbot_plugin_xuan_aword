import aiohttp
import json
import os
from datetime import datetime
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("astrbot_plugin_daily_hitokoto", "你的名字", "每日一言/诗词，支持定时和指令触发", "1.0.0")
class DailyHitokotoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "https://v1.hitokoto.cn"
        # 配置要发送的群列表（替换为你的群号）
        self.target_groups = ["123456789", "987654321"]  # 请修改为实际群号
        # 定时任务配置：每天 10:21 和 18:00 执行
        self.schedule_times = ["10:21", "18:00"]

    async def _fetch_hitokoto(self) -> str:
        """从 API 获取一言，返回句子文本，失败时返回默认句子"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # API 返回的字段是 hitokoto
                        return data.get("hitokoto", "✨ 今日份的句子不见啦～")
                    else:
                        logger.error(f"一言 API 返回错误状态码: {resp.status}")
                        return "🌈 网络似乎有些波动，晚点再来试试吧。"
        except Exception as e:
            logger.error(f"获取一言时发生异常: {e}")
            return "🌟 今天的小句子迷路了，明天再来看看吧。"

    async def _send_to_groups(self, message: str):
        """向配置的群列表发送消息"""
        if not message:
            return
        for group_id in self.target_groups:
            try:
                # 发送群消息
                await self.context.send_group_message(group_id, message)
                logger.info(f"已向群 {group_id} 发送一言")
            except Exception as e:
                logger.error(f"向群 {group_id} 发送消息失败: {e}")

    @filter.command("aword")
    async def aword(self, event: AstrMessageEvent):
        """群指令：获取一言"""
        # 检查是否在群聊中使用
        group_id = event.get_group_id()
        if not group_id:
            yield event.plain_result("该指令只能在群聊中使用。")
            return

        # 获取一言
        hitokoto = await self._fetch_hitokoto()
        # 直接回复
        yield event.plain_result(hitokoto)

    async def _schedule_task(self, target_time: str):
        """定时任务逻辑"""
        # 检查当前时间是否为目标时间（分钟级匹配，避免秒数影响）
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        if current_time == target_time:
            logger.info(f"触发定时一言任务: {target_time}")
            hitokoto = await self._fetch_hitokoto()
            if hitokoto:
                await self._send_to_groups(f"⏰ 每日一言时间到\n{hitokoto}")

    # AstrBot 调度入口：每分钟执行一次
    @filter.schedule("*/1 * * * *")  # Cron 表达式，每分钟一次
    async def check_schedule(self, event: AstrMessageEvent):
        """每分钟检查一次是否需要发送定时一言"""
        for t in self.schedule_times:
            await self._schedule_task(t)
