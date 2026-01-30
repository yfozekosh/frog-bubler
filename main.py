import os
import json
import asyncio
import traceback
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from tapo import ApiClient
from tapo.requests import EnergyDataInterval
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

app = Flask(__name__)
app.config["DEBUG"] = True

# Configuration from environment variables
TAPO_USERNAME = os.getenv("TAPO_USERNAME")
TAPO_PASSWORD = os.getenv("TAPO_PASSWORD")
TAPO_IP_1 = os.getenv("TAPO_IP_1")
TAPO_IP_2 = os.getenv("TAPO_IP_2")

print("Starting Tapo Control App")
print(f"Username: {TAPO_USERNAME}")
print(f"IP 1: {TAPO_IP_1}")
print(f"IP 2: {TAPO_IP_2}")
print(f"Password: {'*' * len(TAPO_PASSWORD) if TAPO_PASSWORD else 'NOT SET'}")

# Storage files
SCHEDULE_FILE = "data/schedules.json"
CONFIG_FILE = "data/config.json"

PLUG_IPS = {
    "1": TAPO_IP_1,
    "2": TAPO_IP_2
}

# Global scheduler
scheduler = BackgroundScheduler()
scheduler.start()


def load_schedules():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return []


def save_schedules(schedules):
    os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedules, f)


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"plug_names": {"1": "Plug 1", "2": "Plug 2"}}


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


async def get_device(plug_id):
    client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
    ip = PLUG_IPS.get(plug_id)
    if not ip:
        raise ValueError(f"Invalid plug_id: {plug_id}")
    return await client.p110(ip)


async def turn_on_plug(plug_id):
    device = await get_device(plug_id)
    await device.on()


async def turn_off_plug(plug_id):
    device = await get_device(plug_id)
    await device.off()


def schedule_job(action, hour, minute, job_id, plug_id):
    if action == "on":
        func = lambda: asyncio.run(turn_on_plug(plug_id))
    else:
        func = lambda: asyncio.run(turn_off_plug(plug_id))

    scheduler.add_job(
        func, CronTrigger(hour=hour, minute=minute), id=job_id, replace_existing=True
    )


def load_and_schedule():
    schedules = load_schedules()
    for schedule in schedules:
        schedule_job(
            schedule["action"], schedule["hour"], schedule["minute"], 
            schedule["id"], schedule.get("plug_id", "1")
        )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(load_config())


@app.route("/api/config", methods=["POST"])
def update_config():
    config = load_config()
    data = request.json
    if "plug_names" in data:
        config["plug_names"] = data["plug_names"]
    save_config(config)
    return jsonify({"success": True, "config": config})

@app.route("/api/status/<plug_id>")
async def get_status(plug_id):
    try:
        ip = PLUG_IPS.get(plug_id)
        print(f"Connecting to Tapo device at {ip}...")
        device = await get_device(plug_id)
        print("Getting device info...")
        info = await device.get_device_info()
        print("Getting energy usage...")
        energy = await device.get_current_power()

        result = {
            "success": True,
            "is_on": info.device_on,
            "current_power": energy.current_power,
        }
        print(f"Status result: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_status: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/energy/day/<plug_id>")
async def get_energy_day(plug_id):
    try:
        device = await get_device(plug_id)
        energy_data = await device.get_energy_data(interval=EnergyDataInterval.Daily)

        total = sum(energy_data.data) if energy_data.data else 0
        return jsonify(
            {
                "success": True,
                "energy": total,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/energy/month/<plug_id>")
async def get_energy_month(plug_id):
    try:
        device = await get_device(plug_id)
        now = datetime.now()
        energy_data = await device.get_energy_data(interval=2, start_date=datetime(now.year, now.month, 1))

        total = sum(energy_data.data) if energy_data.data else 0
        return jsonify(
            {
                "success": True,
                "energy": total,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/turn_on/<plug_id>", methods=["POST"])
async def turn_on(plug_id):
    try:
        await turn_on_plug(plug_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/turn_off/<plug_id>", methods=["POST"])
async def turn_off(plug_id):
    try:
        await turn_off_plug(plug_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/schedules/<plug_id>", methods=["GET"])
def get_schedules(plug_id):
    schedules = load_schedules()
    filtered = [s for s in schedules if s.get("plug_id", "1") == plug_id]
    return jsonify(filtered)


@app.route("/api/schedules/<plug_id>", methods=["POST"])
def add_schedule(plug_id):
    data = request.json
    schedules = load_schedules()

    schedule_id = f"schedule_{plug_id}_{len(schedules)}_{datetime.now().timestamp()}"
    new_schedule = {
        "id": schedule_id,
        "plug_id": plug_id,
        "action": data["action"],
        "hour": data["hour"],
        "minute": data["minute"],
    }

    schedules.append(new_schedule)
    save_schedules(schedules)

    schedule_job(data["action"], data["hour"], data["minute"], schedule_id, plug_id)

    return jsonify({"success": True, "schedule": new_schedule})


@app.route("/api/schedules/<plug_id>/<schedule_id>", methods=["DELETE"])
def delete_schedule(plug_id, schedule_id):
    schedules = load_schedules()
    schedules = [s for s in schedules if s["id"] != schedule_id]
    save_schedules(schedules)

    try:
        scheduler.remove_job(schedule_id)
    except:
        pass

    return jsonify({"success": True})


if __name__ == "__main__":
    load_and_schedule()
    app.run(host="0.0.0.0", port=5011)
