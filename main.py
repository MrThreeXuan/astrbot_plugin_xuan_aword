import aiohttp
import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register

# ===== 猴子补丁：为 Context 类添加 scheduler 属性 =====
if not hasattr(Context, 'scheduler'):
    setattr(Context, 'scheduler', None)
# ===================================================

@register("astrbot_plugin_xuan_aword", "你的名字", "发送群指令 aword 获取随机一言", "1.0.0")
class OneWordPlugin(Star):
    def __init__(self, context: Context):
        # 即使动态属性可能未添加到实例，但类属性会通过继承链被实例访问
        super().__init__(context)

    @filter.command("aword")
    async def aword(self, event: AstrMessageEvent):
        # ... 其余代码保持不变 ...
