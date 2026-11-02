"""Numeric history PNG without extra dependencies; HA recorder query in executor."""
from datetime import timedelta
from functools import partial
import math
from pathlib import Path
import struct
import zlib
from .chart_storage import write_chart, cleanup_charts

# Small numeric font for axis labels.
FONT = dict(zip('0123456789.-:', [
 ['111','101','101','101','111'],['010','110','010','010','111'],
 ['111','001','111','100','111'],['111','001','111','001','111'],
 ['101','101','111','001','001'],['111','100','111','001','111'],
 ['111','100','111','101','111'],['111','001','010','010','010'],
 ['111','101','111','101','111'],['111','101','111','001','111'],
 ['000','000','000','000','010'],['000','000','111','000','000'],
 ['000','010','000','010','000']]))


def png_chart(points, start, end, start_label=None, end_label=None):
    points = [(t, v) for t, v in points if math.isfinite(v)]
    if not points:
        raise ValueError('Kein numerischer Verlauf vorhanden')
    w, h = 720, 300
    pixels = bytearray([20, 26, 34] * w * h)
    def pixel(x, y, color):
        if 0 <= x < w and 0 <= y < h:
            at = (y*w+x)*3
            pixels[at:at+3] = bytes(color)
    def line(x0, y0, x1, y1, color):
        steps = max(abs(x1-x0), abs(y1-y0), 1)
        for n in range(steps+1):
            x, y = round(x0+(x1-x0)*n/steps), round(y0+(y1-y0)*n/steps)
            pixel(x, y, color); pixel(x, y+1, color)
    def text(x, y, value):
        for ch in str(value):
            for dy, row in enumerate(FONT.get(ch, ['000']*5)):
                for dx, p in enumerate(row):
                    if p == '1':
                        for a in (0, 1):
                            for b in (0, 1): pixel(x+dx*2+a, y+dy*2+b, (215,225,239))
            x += 8
    lo, hi = min(v for _, v in points), max(v for _, v in points)
    if hi == lo:
        lo -= max(abs(lo)*.05, .5); hi += max(abs(hi)*.05, .5)
    for n in range(5):
        y = 25+round(n*230/4)
        line(75,y,690,y,(47,58,72))
        text(5,y-5,f'{hi-(hi-lo)*n/4:.2f}')
    line(75,25,75,255,(90,105,126)); line(75,255,690,255,(90,105,126))
    coords = [(75+round(max(0,min(1,(t-start)/(end-start)))*615), 255-round((v-lo)/(hi-lo)*230)) for t,v in points]
    for a,b in zip(coords,coords[1:]):line(*a,*b,(77,196,162))
    if len(coords)==1:pixel(*coords[0],(77,196,162))
    from datetime import datetime
    text(75,274,start_label or datetime.fromtimestamp(start).strftime('%H:%M'))
    text(648,274,end_label or datetime.fromtimestamp(end).strftime('%H:%M'))
    def chunk(kind, data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    raw = b''.join(b'\0'+pixels[y*w*3:(y+1)*w*3] for y in range(h))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')


async def history_image(hass, entity_id, minutes, kind):
    from homeassistant.components.recorder import get_instance
    from homeassistant.components.recorder.history import get_significant_states
    from homeassistant.util import dt as dt_util
    end = dt_util.utcnow(); start = end-timedelta(minutes=int(minutes))
    states = await get_instance(hass).async_add_executor_job(partial(
        get_significant_states, hass, start, end, [entity_id],
        significant_changes_only=False, minimal_response=False, no_attributes=True))
    points = []
    for state in states.get(entity_id, []):
        try:
            value = float(state.state)
            if math.isfinite(value):points.append((state.last_updated.timestamp(),value))
        except (TypeError,ValueError):pass
    # Keep the most recent value to the end of the displayed interval.
    if points:points.append((end.timestamp(),points[-1][1]))
    folder = Path(hass.config.path('.storage', 'alarm_system_charts'))
    def write():
        return write_chart(folder, png_chart(points, start.timestamp(), end.timestamp(),
            dt_util.as_local(start).strftime('%H:%M'), dt_util.as_local(end).strftime('%H:%M')), kind)
    name = await hass.async_add_executor_job(write)
    return '/api/alarm_system/charts/' + name


async def cleanup_history_images(hass):
    await hass.async_add_executor_job(partial(cleanup_charts,
        hass.config.path('.storage', 'alarm_system_charts'),
        hass.config.path('www', 'alarm_system_charts')))
