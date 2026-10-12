const statusEl = document.getElementById('system-status');
const peopleEl = document.getElementById('people-count');
const faceEl = document.getElementById('face-count');
const fallEl = document.getElementById('fall-detected');
const drowsinessEl = document.getElementById('drowsiness');
const incidentListEl = document.getElementById('incident-list');
const triggerBtn = document.getElementById('trigger-incident');

const chartConfig = {
  type: 'line',
  data: {
    labels: ['00:00', '00:10', '00:20', '00:30', '00:40', '00:50'],
    datasets: [{
      label: 'Risk index',
      data: [18, 22, 26, 24, 32, 29],
      borderColor: '#2dd4bf',
      backgroundColor: 'rgba(45, 212, 191, 0.1)',
      fill: true,
      tension: 0.35
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { beginAtZero: true, max: 100 }
    }
  }
};

new Chart(document.getElementById('safety-chart'), chartConfig);

async function loadStatus() {
  try {
    const response = await fetch('/api/system-status');
    const data = await response.json();
    statusEl.textContent = data.status || 'SAFE';
    peopleEl.textContent = data.people_count ?? 0;
    faceEl.textContent = data.face_count ?? 0;
    fallEl.textContent = data.fall_detected ? 'Yes' : 'No';
    drowsinessEl.textContent = data.drowsiness ? 'Yes' : 'No';
    renderIncidents(data.recent_incidents || []);
  } catch (error) {
    console.error('Unable to load status', error);
  }
}

function renderIncidents(incidents) {
  if (!incidents.length) {
    incidentListEl.innerHTML = '<div class="incident-item"><strong>No incidents yet.</strong><br><small>System is monitoring in passive mode.</small></div>';
    return;
  }

  incidentListEl.innerHTML = incidents.slice(0, 5).map((item) => `
    <div class="incident-item">
      <strong>${item.incident_type || 'monitoring'}</strong>
      <div><small>${new Date(item.created_at).toLocaleString()} • ${item.severity || 'SAFE'}</small></div>
    </div>
  `).join('');
}

triggerBtn.addEventListener('click', async () => {
  await fetch('/api/trigger-incident', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      incident_type: 'unsafe_activity',
      severity: 'HIGH',
      confidence: 0.78,
      details: 'Manual test incident triggered from dashboard',
      people_count: 2,
      face_count: 2
    })
  });
  loadStatus();
});

loadStatus();
setInterval(loadStatus, 2500);
