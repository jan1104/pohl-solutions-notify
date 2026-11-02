"""Phone and browser pairing through actual HA registry associations."""
import re


def sensor_roles(entities, states):
    roles = {"ringer": [], "volume": []}
    for entry in entities:
        if entry.entity_id not in states or not entry.entity_id.startswith("sensor."):
            continue
        key = f"{entry.unique_id} {entry.entity_id}".lower()
        if re.search(r"ringer.?mode", key):
            roles["ringer"].append(entry.entity_id)
        if "notification" in key and "volume" in key and states[entry.entity_id].attributes.get("unit_of_measurement") != "%":
            roles["volume"].append(entry.entity_id)
    return roles


def browser_connections(entities, states, devices=()):
    """Registered HA devices remain selectable when their browser is offline."""
    found, device_ids = {}, {}
    for device in devices:
        identifiers = [value for domain, value in device.identifiers if domain == "browser_mod" and isinstance(value, str) and value]
        if len(identifiers) != 1:
            continue
        bid = identifiers[0]
        device_ids[device.id] = bid
        found.setdefault(bid, {"id": bid, "visibility_sensor": "", "available": False})
    visibility = {}
    for entry in entities:
        if entry.platform != "browser_mod":
            continue
        state = states.get(entry.entity_id)
        bid = device_ids.get(entry.device_id)
        # Entity attributes are a second documented source for the exact BrowserID.
        if not bid and state:
            bid = state.attributes.get("browserID")
        key = str(entry.unique_id)
        if not bid:
            match = re.search(r"-(?:browser_?id)$", key, re.I)
            if match:
                bid = key[:match.start()]
            elif "browser_id" in key.lower() and state and state.state not in ("unknown", "unavailable"):
                bid = state.state
        if not isinstance(bid, str) or not bid or bid in ("unknown", "unavailable"):
            continue
        item = found.setdefault(bid, {"id": bid, "visibility_sensor": "", "available": False})
        if entry.device_id:
            device_ids.setdefault(entry.device_id, bid)
        if state and state.state not in ("unknown", "unavailable"):
            item["available"] = True
    # Match visibility by actual device association, not a guessed entity suffix.
    for entry in entities:
        if entry.platform != "browser_mod" or not entry.entity_id.startswith("sensor."):
            continue
        key = str(entry.unique_id).lower()
        if not (key.endswith("-browser_visibility") or key.endswith("_browser_visibility") or key.endswith("-visibility")):
            continue
        bid = device_ids.get(entry.device_id)
        if not bid and (state := states.get(entry.entity_id)):
            bid = state.attributes.get("browserID")
        if bid in found:
            visibility.setdefault(bid, []).append(entry.entity_id)
    for bid, candidates in visibility.items():
        if len(candidates) == 1:
            found[bid]["visibility_sensor"] = candidates[0]
    return sorted(found.values(), key=lambda x: x["id"].casefold())


def connections(hass):
    from homeassistant.helpers import entity_registry as er, device_registry as dr
    registry = er.async_get(hass)
    states = {s.entity_id: s for s in hass.states.async_all()}
    phones, browsers = {}, []
    mobile = hass.data.get("mobile_app", {})
    if mobile:
        from homeassistant.components.mobile_app.const import DATA_DEVICES, DATA_NOTIFY
        notify = mobile.get(DATA_NOTIFY)
        for service, webhook in getattr(notify, "registered_targets", {}).items():
            device = mobile.get(DATA_DEVICES, {}).get(webhook)
            if not device:
                continue
            action = service if service.startswith("notify.") else "notify." + service
            phones[action] = {"device_id": device.id,
                **sensor_roles(er.async_entries_for_device(registry, device.id), states)}
    browsers = browser_connections(list(registry.entities.values()), states, list(dr.async_get(hass).devices.values()))
    return phones, browsers


def complete_device(payload, phones, browsers):
    data = dict(payload)
    phone = phones.get(data.get("notify_action"), {})
    for role, field in (("ringer", "ringer_sensor"), ("volume", "volume_sensor")):
        if not data.get(field) and len(phone.get(role, [])) == 1:
            data[field] = phone[role][0]
    known = {b["id"]: b for b in browsers}
    data["browsers"] = [{**b, "visibility_sensor": b.get("visibility_sensor") or known.get(b.get("id"), {}).get("visibility_sensor", "")} for b in data.get("browsers", [])]
    return data
