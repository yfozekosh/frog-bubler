# frog-bubler
Simple vibe coded project to control aquarium air pump from raspberry pi

## Features
- Control two Tapo P110 smart plugs independently
- Real-time power monitoring
- Energy usage tracking (daily/monthly)
- Automated scheduling (cron-based)
- Activity logging with device tracking
- Editable plug names
- URL routing for bookmarks
- Responsive web interface

## Project Structure

See [STRUCTURE.md](STRUCTURE.md) for detailed architecture documentation.

```
├── app/              # Backend application
│   ├── routes/       # API endpoints
│   ├── services/     # Business logic
│   └── storage/      # Data persistence
├── static/           # Frontend assets
│   ├── css/          # Stylesheets
│   └── js/           # JavaScript
├── templates/        # HTML templates
└── data/            # Runtime data storage
```

## Setup
```bash
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
export TAPO_USERNAME=example@exampl.com
export TAPO_PASSWORD=example
export TAPO_IP_1=192.168.1.2
export TAPO_IP_2=192.168.1.3
python main.py
# open localhost:5011 in the browser
```

## Technology Stack
- **Backend**: Python 3.11, Flask, APScheduler
- **Frontend**: Vanilla JavaScript, CSS3, HTML5
- **Device Control**: Tapo P110 Python Library
- **Data Storage**: JSON files

## Notes
This project was created rapidly using Claude and has been refactored for maintainability.
