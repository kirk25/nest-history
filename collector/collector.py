#!/usr/bin/env python3
import os, time, json, urllib.request, urllib.parse, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "300"))
VM_URL = os.environ.get("VICTORIAMETRICS_URL", "http://victoriametrics:8428")
SDM_PROJECT_ID = os.environ["SDM_PROJECT_ID"]
SDM_CLIENT_ID = os.environ["SDM_CLIENT_ID"]
SDM_CLIENT_SECRET = os.environ["SDM_CLIENT_SECRET"]
SDM_REFRESH_TOKEN = os.environ["SDM_REFRESH_TOKEN"]

THERMOSTAT_DEVICE_TYPE = "sdm.devices.types.THERMOSTAT"


def get_access_token():
    data = urllib.parse.urlencode({
        "client_id": SDM_CLIENT_ID,
        "client_secret": SDM_CLIENT_SECRET,
        "refresh_token": SDM_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }).encode()
    resp = urllib.request.urlopen("https://oauth2.googleapis.com/token", data)
    return json.loads(resp.read())["access_token"]


def get_devices(access_token):
    req = urllib.request.Request(
        f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{SDM_PROJECT_ID}/devices",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read()).get("devices", [])


def extract_metrics(device):
    traits = device.get("traits", {})
    name = traits.get("sdm.devices.traits.Info", {}).get("customName", "unknown")
    label = name.lower().replace(" ", "_")
    metrics = {}

    temp = traits.get("sdm.devices.traits.Temperature", {}).get("ambientTemperatureCelsius")
    if temp is not None:
        metrics["nest_ambient_temperature_celsius"] = temp

    humidity = traits.get("sdm.devices.traits.Humidity", {}).get("ambientHumidityPercent")
    if humidity is not None:
        metrics["nest_ambient_humidity_percent"] = humidity

    setpoint = traits.get("sdm.devices.traits.ThermostatTemperatureSetpoint", {})
    if "heatCelsius" in setpoint:
        metrics["nest_setpoint_heat_celsius"] = setpoint["heatCelsius"]
    if "coolCelsius" in setpoint:
        metrics["nest_setpoint_cool_celsius"] = setpoint["coolCelsius"]

    hvac_status = traits.get("sdm.devices.traits.ThermostatHvac", {}).get("status")
    if hvac_status is not None:
        metrics["nest_hvac_heating"] = 1 if hvac_status == "HEATING" else 0
        metrics["nest_hvac_cooling"] = 1 if hvac_status == "COOLING" else 0

    mode = traits.get("sdm.devices.traits.ThermostatMode", {}).get("mode")
    if mode is not None:
        metrics["nest_mode_heat"] = 1 if mode == "HEAT" else 0
        metrics["nest_mode_cool"] = 1 if mode == "COOL" else 0
        metrics["nest_mode_heatcool"] = 1 if mode == "HEATCOOL" else 0
        metrics["nest_mode_off"] = 1 if mode == "OFF" else 0

    eco = traits.get("sdm.devices.traits.ThermostatEco", {})
    if eco.get("mode") is not None:
        metrics["nest_eco_active"] = 1 if eco["mode"] == "MANUAL_ECO" else 0
    if "heatCelsius" in eco:
        metrics["nest_eco_heat_celsius"] = eco["heatCelsius"]
    if "coolCelsius" in eco:
        metrics["nest_eco_cool_celsius"] = eco["coolCelsius"]

    fan = traits.get("sdm.devices.traits.Fan", {}).get("timerMode")
    if fan is not None:
        metrics["nest_fan_active"] = 1 if fan == "ON" else 0

    connectivity = traits.get("sdm.devices.traits.Connectivity", {}).get("status")
    if connectivity is not None:
        metrics["nest_connectivity_online"] = 1 if connectivity == "ONLINE" else 0

    return label, metrics


def push_metrics(label, metrics, timestamp_ms):
    lines = []
    for name, value in metrics.items():
        lines.append(f'{name}{{device="{label}"}} {value} {timestamp_ms}')
    body = "\n".join(lines).encode()
    req = urllib.request.Request(
        f"{VM_URL}/api/v1/import/prometheus",
        data=body,
        method="POST",
    )
    urllib.request.urlopen(req)


def collect():
    access_token = get_access_token()
    devices = get_devices(access_token)
    timestamp_ms = int(time.time() * 1000)
    for device in devices:
        if device.get("type") != THERMOSTAT_DEVICE_TYPE:
            continue
        label, metrics = extract_metrics(device)
        push_metrics(label, metrics, timestamp_ms)
        log.info(f"Pushed {len(metrics)} metrics for {label}")


def main():
    log.info(f"Collector starting, polling every {POLL_INTERVAL}s")
    while True:
        try:
            collect()
        except Exception as e:
            log.error(f"Collection failed: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
