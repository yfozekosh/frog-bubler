from app import create_app
from app.services.scheduler import load_and_schedule

if __name__ == "__main__":
    # Load and schedule all saved schedules
    load_and_schedule()
    
    # Create and run the app
    app = create_app()
    app.run(host="0.0.0.0", port=5011)
