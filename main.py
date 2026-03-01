import aiohttp
import json
import os
from datetime import datetime
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("astrbot_plugin_xuan_aword", "你的名字", "每日一言/诗词，支持群指令 aword 和定时发送", "1.0.0")
class DailyHitokotoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "https://v1.hitokoto.cn"
        # 配置要发送的群列表（替换为你的群号）
        self.target_groups = ["123456789", "987654321"]  # 请修改为实际群号
        # 定时任务配置：每天 10:21 和 18:00 执行
        self._add_scheduled_jobs()

    def _add_scheduled_jobs(self):
        """通过调度器添加定时任务"""
        scheduler = self.context.scheduler
        if scheduler is None:
            logger.error("无法获取调度器，定时任务将不会执行")
            return

        # 添加每天 10:21 的任务
        scheduler.add_job(
            self._scheduled_send,
            "cron",
            hour=10,
            minute=21,
            id="hitokoto_morning",
            replace_existing=True,
            args=["上午"]
        )
        # 添加每天 18:00 的任务
        scheduler.add_job(
            self._scheduled_send,
            "cron",
            hour=18,
            minute=0,
            id="hitokoto_evening",
            replace_existing=True,
            args=["下午/傍晚"]
        )
        logger.info("已添加一言定时任务（10:21 和 18:00）")

    async def _scheduled_send(self, time_tag: str):
        """定时发送的逻辑，time_tag 用于区分上下午"""
        hitokoto = await self._fetch_hitokoto()
        if hitokoto:
            message = f"⏰ 每日一言时间（{time_tag}）\n{hitokoto}"
            await self._send_to_groups(message)

    async def _fetch_hitokoto(self) -> str:
        """从 API 获取一言，返回句子文本，失败时返回默认句子"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
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
                await self.context.send_group_message(group_id, message)
                logger.info(f"已向群 {group_id} 发送一言")
            except Exception as e:
                logger.error(f"向群 {group_id} 发送消息失败: {e}")

    @filter.command("aword")
    async def aword(self, event: AstrMessageEvent):
        """群指令：获取一言"""
        group_id = event.get_group_id()
        if not group_id:
            yield event.plain_result("该指令只能在群聊中使用。")
            return

        hitokoto = await self._fetch_hitokoto()
        yield event.plain_result(hitokoto)
