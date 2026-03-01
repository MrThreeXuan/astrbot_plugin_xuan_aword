import aiohttp
import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

@register("astrbot_plugin_xuan_aword", "你的名字", "发送群指令 aword 获取随机一言", "1.0.0")
class OneWordPlugin(Star):
    def __init__(self, context: Context):
        # 兼容性处理：确保 context 有 scheduler 属性（避免旧版本 AstrBot 报错）
        if not hasattr(context, 'scheduler'):
            context.scheduler = None
        super().__init__(context)

    @filter.command("aword")
    async def aword(self, event: AstrMessageEvent):
        '''获取一句随机一言（句子 + 出处）'''
        yield event.plain_result("正在寻章摘句，请稍候...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://v1.hitokoto.cn", timeout=10) as resp:
                    if resp.status != 200:
                        yield event.plain_result(f"网络开小差了，状态码：{resp.status}")
                        return
                    data = await resp.json()

            hitokoto = data.get("hitokoto", "")
            from_who = data.get("from_who")
            from_text = data.get("from", "")

            source_parts = []
            if from_who:
                source_parts.append(from_who)
            if from_text:
                source_parts.append(f"《{from_text}》")
            source = " —— ".join(source_parts) if source_parts else ""

            message = f"📖 {hitokoto}"
            if source:
                message += f"\n{source}"

            yield event.plain_result(message)

        except asyncio.TimeoutError:
            yield event.plain_result("请求超时，可能是网络问题，请稍后重试。")
        except aiohttp.ClientError as e:
            yield event.plain_result(f"网络请求失败：{str(e)}")
        except Exception as e:
            yield event.plain_result(f"发生未知错误：{str(e)}，请稍后再试。")
