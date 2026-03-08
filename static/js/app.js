let currentPlug = localStorage.getItem('currentPlug') || '1';
let plugNames = {};

async function loadConfig() {
  try {
    const resp = await fetch('/api/config');
    const config = await resp.json();
    plugNames = config.plug_names || { '1': 'Plug 1', '2': 'Plug 2' };
    document.getElementById('tabName1').textContent = plugNames['1'];
    document.getElementById('tabName2').textContent = plugNames['2'];
  } catch (e) {
    console.error('Failed to load config:', e);
  }
}

async function editPlugName(plugId) {
  const currentName = plugNames[plugId];
  const newName = prompt(`Enter new name for ${currentName}:`, currentName);
  if (newName && newName.trim() !== '' && newName !== currentName) {
    plugNames[plugId] = newName.trim();
    try {
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plug_names: plugNames })
      });
      document.getElementById(`tabName${plugId}`).textContent = newName.trim();
    } catch (e) {
      alert('Failed to update plug name');
      console.error(e);
    }
  }
}

function switchTab(evt, plugId) {
  currentPlug = plugId;
  localStorage.setItem('currentPlug', plugId);
  window.location.hash = `plug${plugId}`;

  document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
  document.querySelectorAll('.plug-content').forEach(content => content.classList.remove('active'));

  // use the event passed from the click handler
  evt.target.closest('.tab').classList.add('active');
  document.getElementById(`plug${plugId}`).classList.add('active');

  updateStatus(plugId);
  updateEnergy(plugId);
  loadSchedules(plugId);
  displayLogs(plugId);
}

function initializeFromURL() {
  const hash = window.location.hash.slice(1); // Remove #
  if (hash === 'plug1' || hash === 'plug2') {
    currentPlug = hash.replace('plug', '');
    localStorage.setItem('currentPlug', currentPlug);
  }
}

async function displayLogs(plugId) {
  try {
    const resp = await fetch(`/api/activity_log/${plugId}`);
    const logs = await resp.json();
    const list = document.getElementById(`logList${plugId}`);
    const hideAutomatic = document.getElementById(`hideAutomatic${plugId}`).checked;

    const filteredLogs = hideAutomatic
      ? logs.filter(log => log.source !== 'automatic')
      : logs;

    if (filteredLogs.length === 0) {
      list.innerHTML = '<div style="text-align: center; color: #999; padding: 20px;">No activity logged yet</div>';
      return;
    }

    list.innerHTML = filteredLogs.map(log => {
      const date = new Date(log.timestamp);
      const localTime = date.toLocaleString();
      const sourceClass = log.source === 'automatic' ? 'automatic' : '';
      const sourceInfo = log.device_info ? `<span class="log-source">${log.device_info}</span>` : '';
      const sourceLabel = log.source === 'automatic' ? ' [AUTO]' : '';
      return `<div class="log-entry ${log.action} ${sourceClass}">
                ${log.action.toUpperCase()}${sourceLabel} - ${localTime}
                ${sourceInfo}
            </div>`;
    }).join('');
  } catch (e) {
    console.error('Failed to load logs:', e);
  }
}

async function clearLog(plugId) {
  if (confirm('Clear all log entries for this plug?')) {
    try {
      await fetch(`/api/activity_log/${plugId}`, { method: 'DELETE' });
      await displayLogs(plugId);
    } catch (e) {
      alert('Failed to clear log');
      console.error(e);
    }
  }
}

function updateClocks() {
  const now = new Date();
  document.getElementById('localTime').textContent = now.toLocaleTimeString('en-GB');
  document.getElementById('berlinTime').textContent = now.toLocaleTimeString('en-GB', { timeZone: 'Europe/Berlin' });
  document.getElementById('utcTime').textContent = now.toLocaleTimeString('en-GB', { timeZone: 'UTC' });
}

async function updateStatus(plugId) {
  try {
    const resp = await fetch(`/api/status/${plugId}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    if (data.success) {
      document.getElementById(`status${plugId}`).textContent = data.is_on ? 'Plug is ON' : 'Plug is OFF';
      document.getElementById(`status${plugId}`).className = 'status ' + (data.is_on ? 'on' : 'off');
      document.getElementById(`currentPower${plugId}`).textContent = data.current_power.toFixed(2) + ' W';
    } else {
      console.error(`Status error for plug ${plugId}:`, data.error);
    }
  } catch (e) {
    console.error(`Failed to update status for plug ${plugId}:`, e);
  }
}

async function updateEnergy(plugId) {
  try {
    const dayResp = await fetch(`/api/energy/day/${plugId}`);
    if (dayResp.ok) {
      const dayData = await dayResp.json();
      if (dayData.success) {
        document.getElementById(`dayEnergy${plugId}`).textContent = dayData.energy.toFixed(0) + ' Wh';
      }
    }

    const monthResp = await fetch(`/api/energy/month/${plugId}`);
    if (monthResp.ok) {
      const monthData = await monthResp.json();
      if (monthData.success) {
        document.getElementById(`monthEnergy${plugId}`).textContent = monthData.energy.toFixed(0) + ' Wh';
      }
    }
  } catch (e) {
    console.error(`Failed to update energy for plug ${plugId}:`, e);
  }
}

async function turnOn(plugId) {
  await fetch(`/api/turn_on/${plugId}`, { method: 'POST' });
  await updateStatus(plugId);
  await displayLogs(plugId);
}

async function turnOff(plugId) {
  await fetch(`/api/turn_off/${plugId}`, { method: 'POST' });
  await updateStatus(plugId);
  await displayLogs(plugId);
}

async function loadSchedules(plugId) {
  const resp = await fetch(`/api/schedules/${plugId}`);
  const schedules = await resp.json();
  const list = document.getElementById(`scheduleList${plugId}`);
  list.innerHTML = '';
  schedules.forEach(s => {
    const div = document.createElement('div');
    div.className = 'schedule-item';
    div.innerHTML = `
            <span>${s.action.toUpperCase()} at ${String(s.hour).padStart(2, '0')}:${String(s.minute).padStart(2, '0')}</span>
            <button class="btn-delete" onclick="deleteSchedule('${plugId}', '${s.id}')">Delete</button>
        `;
    list.appendChild(div);
  });
}

async function addSchedule(plugId) {
  const action = document.getElementById(`action${plugId}`).value;
  const hour = parseInt(document.getElementById(`hour${plugId}`).value);
  const minute = parseInt(document.getElementById(`minute${plugId}`).value);

  if (isNaN(hour) || isNaN(minute) || hour < 0 || hour > 23 || minute < 0 || minute > 59) {
    alert('Please enter valid hour (0-23) and minute (0-59)');
    return;
  }

  await fetch(`/api/schedules/${plugId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, hour, minute })
  });

  document.getElementById(`hour${plugId}`).value = '';
  document.getElementById(`minute${plugId}`).value = '';
  await loadSchedules(plugId);
}

async function deleteSchedule(plugId, id) {
  await fetch(`/api/schedules/${plugId}/${id}`, { method: 'DELETE' });
  await loadSchedules(plugId);
}

loadConfig().then(() => {
  initializeFromURL();

  updateClocks();
  updateStatus('1');
  updateStatus('2');
  updateEnergy('1');
  updateEnergy('2');
  loadSchedules('1');
  loadSchedules('2');
  displayLogs('1');
  displayLogs('2');

  document.querySelectorAll('.tab')[parseInt(currentPlug) - 1].classList.add('active');
  document.getElementById(`plug${currentPlug}`).classList.add('active');
  document.querySelectorAll('.plug-content').forEach((el, idx) => {
    if (el.id !== `plug${currentPlug}`) el.classList.remove('active');
  });
  document.querySelectorAll('.tab').forEach((el, idx) => {
    if (idx !== parseInt(currentPlug) - 1) el.classList.remove('active');
  });
});

// Handle browser back/forward buttons
window.addEventListener('hashchange', () => {
  initializeFromURL();
  document.querySelectorAll('.tab')[parseInt(currentPlug) - 1]?.click();
});

setInterval(updateClocks, 5000);
setInterval(() => {
  updateStatus('1');
  updateStatus('2');
}, 10000);  // Reduced from 5s to 10s to avoid rate limiting
setInterval(() => {
  updateEnergy('1');
  updateEnergy('2');
}, 120000);  // Reduced from 60s to 120s (2 min)
setInterval(() => {
  displayLogs('1');
  displayLogs('2');
}, 15000);  // Reduced from 10s to 15s
