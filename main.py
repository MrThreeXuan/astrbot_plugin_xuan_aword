import aiohttp
import asyncio
from datetime import datetime
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("astrbot_plugin_xuan_aword", "你的名字", "每日一言/诗词，支持群指令和定时发送", "1.0.0")
class DailyHitokotoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api_url = "https://v1.hitokoto.cn"
        # 配置要发送的群列表（请替换为你的群号）
        self.target_groups = ["123456789", "987654321"]  # ← 修改这里
        # 定时时间（24小时制，冒号分隔）
        self.schedule_times = ["10:21", "18:00"]
        
        # 启动后台定时任务
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def _scheduler_loop(self):
        """每分钟检查一次是否需要发送定时一言"""
        while True:
            try:
                now = datetime.now().strftime("%H:%M")
                if now in self.schedule_times:
                    logger.info(f"触发定时一言任务: {now}")
                    hitokoto = await self._fetch_hitokoto()
                    if hitokoto:
                        await self._send_to_groups(f"⏰ 每日一言时间到\n{hitokoto}")
                    # 避免同一分钟内重复发送，休眠60秒
                    await asyncio.sleep(60)
                else:
                    # 每分钟检查一次
                    await asyncio.sleep(60)
            except asyncio.CancelledError:
                logger.info("定时任务被取消")
                break
            except Exception as e:
                logger.error(f"定时任务出错: {e}")
                await asyncio.sleep(60)

    async def _fetch_hitokoto(self) -> str:
        """从 API 获取一言，返回句子文本"""
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

    async def _stop(self):
        """插件卸载时取消定时任务"""
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
