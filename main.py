import os
import json
import asyncio
import traceback
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from tapo import ApiClient
from tapo.requests import EnergyDataInterval, PowerDataInterval
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

app = Flask(__name__)
app.config["DEBUG"] = True

# Configuration from environment variables
TAPO_USERNAME = os.getenv("TAPO_USERNAME")
TAPO_PASSWORD = os.getenv("TAPO_PASSWORD")
TAPO_IP = os.getenv("TAPO_IP")

print("Starting Tapo Control App")
print(f"Username: {TAPO_USERNAME}")
print(f"IP: {TAPO_IP}")
print(f"Password: {'*' * len(TAPO_PASSWORD) if TAPO_PASSWORD else 'NOT SET'}")

# Schedule storage file
SCHEDULE_FILE = "data/schedules.json"

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


async def get_device():
    client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
    return await client.p110(TAPO_IP)


async def turn_on_plug():
    device = await get_device()
    await device.on()


async def turn_off_plug():
    device = await get_device()
    await device.off()


def schedule_job(action, hour, minute, job_id):
    if action == "on":
        func = lambda: asyncio.run(turn_on_plug())
    else:
        func = lambda: asyncio.run(turn_off_plug())

    scheduler.add_job(
        func, CronTrigger(hour=hour, minute=minute), id=job_id, replace_existing=True
    )


def load_and_schedule():
    schedules = load_schedules()
    for schedule in schedules:
        schedule_job(
            schedule["action"], schedule["hour"], schedule["minute"], schedule["id"]
        )


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
async def get_status():
    try:
        print(f"Connecting to Tapo device at {TAPO_IP}...")
        device = await get_device()
        print("Getting device info...")
        info = await device.get_device_info()
        print("Getting energy usage...")
        energy = await device.get_current_power()

        result = {
            "success": True,
            "is_on": info.device_on,
            "current_power": energy.current_power,  # Convert to watts
        }
        print(f"Status result: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_status: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/energy/day")
async def get_energy_day():
    try:
        device = await get_device()
        # Get today's energy data
        energy_data = await device.get_energy_data(interval=EnergyDataInterval.Daily)  # 0 = hourly

        total = sum(energy_data.data) if energy_data.data else 0
        return jsonify(
            {
                "success": True,
                "energy": total,  # Convert to kWh
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/energy/month")
async def get_energy_month():
    try:
        device = await get_device()
        # Get this month's energy data
        now = datetime.now()
        energy_data = await device.get_energy_data(interval=2, start_date=datetime(now.year, now.month, 1))

        total = sum(energy_data.data) if energy_data.data else 0
        return jsonify(
            {
                "success": True,
                "energy": total,  # Convert to kWh
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/turn_on", methods=["POST"])
async def turn_on():
    try:
        await turn_on_plug()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/turn_off", methods=["POST"])
async def turn_off():
    try:
        await turn_off_plug()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/schedules", methods=["GET"])
def get_schedules():
    return jsonify(load_schedules())


@app.route("/api/schedules", methods=["POST"])
def add_schedule():
    data = request.json
    schedules = load_schedules()

    schedule_id = f"schedule_{len(schedules)}_{datetime.now().timestamp()}"
    new_schedule = {
        "id": schedule_id,
        "action": data["action"],
        "hour": data["hour"],
        "minute": data["minute"],
    }

    schedules.append(new_schedule)
    save_schedules(schedules)

    schedule_job(data["action"], data["hour"], data["minute"], schedule_id)

    return jsonify({"success": True, "schedule": new_schedule})


@app.route("/api/schedules/<schedule_id>", methods=["DELETE"])
def delete_schedule(schedule_id):
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
