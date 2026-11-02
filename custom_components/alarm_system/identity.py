"""Account display names must never fall back to internal UUIDs."""
import re

def human_name(value, user_id=None):
    if not isinstance(value, str): return None
    value = value.strip()
    if not value or value == user_id or value == 'Name nicht verfügbar': return None
    if re.fullmatch(r'(?:[0-9a-f]{32}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})', value, re.I): return None
    return value

def resolve_name(user_id, accounts, configured, *stored):
    candidates = [accounts.get(user_id), configured.get(user_id, {}).get('name'), *stored]
    return next((n for v in candidates if (n := human_name(v, user_id))), 'Name nicht verfügbar')
