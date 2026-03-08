# Project Structure

This document describes the refactored application structure.

## Directory Layout

```
frog-bubler/
├── app/                    # Main application package
│   ├── __init__.py        # Flask app factory
│   ├── config.py          # Configuration and environment variables
│   ├── routes/            # API endpoints (Blueprints)
│   │   ├── __init__.py
│   │   ├── main.py        # Main page route
│   │   ├── status.py      # Device status endpoint
│   │   ├── energy.py      # Energy monitoring endpoints
│   │   ├── control.py     # On/Off control endpoints
│   │   ├── schedules.py   # Schedule management
│   │   ├── config.py      # Config management (plug names)
│   │   └── activity.py    # Activity log endpoints
│   ├── services/          # Business logic layer
│   │   ├── __init__.py
│   │   ├── tapo_device.py # Tapo device communication
│   │   └── scheduler.py   # APScheduler integration
│   └── storage/           # Data persistence layer
│       ├── __init__.py
│       └── data_manager.py # JSON file operations
├── static/                # Static assets
│   ├── css/
│   │   └── styles.css    # All application styles
│   └── js/
│       └── app.js        # All JavaScript logic
├── templates/             # HTML templates
│   └── index.html        # Main page (clean, no inline CSS/JS)
├── data/                  # Data storage (created at runtime)
│   ├── schedules.json    # Schedule definitions
│   ├── config.json       # Plug names and settings
│   └── activity_log.json # Activity history
├── main.py               # Application entry point
├── Dockerfile            # Docker configuration
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## Backend Architecture

### Layers

1. **Entry Point** (`main.py`)
   - Initializes scheduler
   - Creates Flask app
   - Starts web server

2. **Application Factory** (`app/__init__.py`)
   - Creates Flask app instance
   - Registers all blueprints
   - Configures static/template folders

3. **Configuration** (`app/config.py`)
   - Environment variables
   - File paths
   - Global constants

4. **Routes** (`app/routes/`)
   - Each blueprint handles specific API domain
   - Thin layer - delegates to services
   - Returns JSON responses

5. **Services** (`app/services/`)
   - `tapo_device.py`: Device communication, retry logic, rate limiting
   - `scheduler.py`: Cron job management, schedule loading

6. **Storage** (`app/storage/`)
   - `data_manager.py`: All file I/O operations
   - JSON persistence for schedules, config, logs

### API Routes

| Blueprint | Prefix | Routes |
|-----------|--------|--------|
| main | / | GET / (index page) |
| status | /api | GET /api/status/<plug_id> |
| energy | /api | GET /api/energy/day/<plug_id><br>GET /api/energy/month/<plug_id> |
| control | /api | POST /api/turn_on/<plug_id><br>POST /api/turn_off/<plug_id> |
| schedules | /api | GET /api/schedules/<plug_id><br>POST /api/schedules/<plug_id><br>DELETE /api/schedules/<plug_id>/<schedule_id> |
| config | /api | GET /api/config<br>POST /api/config |
| activity | /api | GET /api/activity_log/<plug_id><br>DELETE /api/activity_log/<plug_id> |

## Frontend Architecture

### Files

1. **HTML** (`templates/index.html`)
   - Clean semantic markup
   - No inline styles or scripts
   - Links to external CSS/JS

2. **CSS** (`static/css/styles.css`)
   - All application styles
   - Responsive design
   - Component-based organization

3. **JavaScript** (`static/js/app.js`)
   - URL routing (hash-based)
   - API communication
   - UI state management
   - Tab switching logic
   - Activity log filtering

### JavaScript Structure

- **Configuration Management**: `loadConfig()`, `editPlugName()`
- **Tab Navigation**: `switchTab()`, `initializeFromURL()`
- **Device Control**: `turnOn()`, `turnOff()`
- **Status Updates**: `updateStatus()`, `updateEnergy()`
- **Schedule Management**: `loadSchedules()`, `addSchedule()`, `deleteSchedule()`
- **Activity Logs**: `displayLogs()`, `clearLog()`
- **Clock Display**: `updateClocks()`

## Benefits of Refactoring

### Maintainability
- ✅ Separation of concerns
- ✅ Single responsibility per module
- ✅ Easy to locate and modify code
- ✅ Clear dependency flow

### Scalability
- ✅ Easy to add new routes/blueprints
- ✅ Can swap storage layer without touching routes
- ✅ Services can be tested independently
- ✅ Frontend assets can be minified/bundled

### Development
- ✅ Multiple developers can work on different modules
- ✅ Smaller files are easier to review
- ✅ Clear file names indicate purpose
- ✅ Reusable components

### Performance
- ✅ Browser caches CSS/JS separately
- ✅ Can add CDN for static files
- ✅ Easier to optimize individual layers

## Running the Application

### Development
```bash
export TAPO_USERNAME=your@email.com
export TAPO_PASSWORD=yourpassword
export TAPO_IP_1=192.168.1.2
export TAPO_IP_2=192.168.1.3
python main.py
```

### Docker
```bash
./build.sh
# or manually:
docker build -t frog-bubler .
docker run -d -p 5011:5011 \
  -e TAPO_USERNAME=... \
  -e TAPO_PASSWORD=... \
  -e TAPO_IP_1=... \
  -e TAPO_IP_2=... \
  -v $(pwd)/data:/app/data \
  frog-bubler
```

## Adding New Features

### New API Endpoint
1. Create route in appropriate blueprint (`app/routes/`)
2. Add service function if needed (`app/services/`)
3. Add storage function if needed (`app/storage/`)

### New Page
1. Add route in `app/routes/main.py`
2. Create template in `templates/`
3. Add styles to `static/css/styles.css`
4. Add JavaScript to `static/js/` (create new file if needed)

### New Configuration
1. Add to `app/config.py`
2. Update `.env` or environment variables
3. Use in appropriate service/route
