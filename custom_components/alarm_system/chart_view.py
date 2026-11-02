"""Authenticated chart access with the same account/type rules as the panel."""
from functools import partial

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.http.const import KEY_HASS_USER

from .chart_storage import read_chart
from .const import DOMAIN


class AlarmChartView(HomeAssistantView):
    url = "/api/alarm_system/charts/{image_id}"
    name = "api:alarm_system:charts"
    requires_auth = True

    def __init__(self, hass):
        self.hass = hass

    async def get(self, request, image_id):
        user = request.get(KEY_HASS_USER)
        engine = self.hass.data.get(DOMAIN)
        if not user or not user.is_active:
            raise web.HTTPUnauthorized()
        if not engine:
            raise web.HTTPNotFound()
        try:
            kind, image = await self.hass.async_add_executor_job(partial(
                read_chart, self.hass.config.path(".storage", "alarm_system_charts"), image_id))
        except (OSError, ValueError, KeyError, TypeError):
            raise web.HTTPNotFound() from None
        if not user.is_admin and not engine.model.authorized(user.id, {"type": kind}):
            raise web.HTTPForbidden()
        return web.Response(body=image, content_type="image/png", headers={"Cache-Control": "no-store"})
