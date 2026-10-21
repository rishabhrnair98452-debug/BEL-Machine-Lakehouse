(() => {
  const $ = (id) => document.getElementById(id);
  let charts = {};
  let latestData = null;

  const colors = { temperature: '#1685e6', vibration: '#f59b20', pressure: '#11a875' };
  const labels = { temperature: 'Temperature (°C)', vibration: 'Vibration (mm/s)', pressure: 'Pressure (bar)' };

  function number(value, digits=2) {
    return value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : Number(value).toFixed(digits);
  }
  function shortTime(value) {
    if (!value) return '';
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? String(value).replace('T',' ').slice(0,16) : d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
  }
  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  function toast(message) {
    const node = $('toast'); node.textContent = message; node.style.display = 'block';
    setTimeout(() => node.style.display = 'none', 3200);
  }
  function makeLineChart(id, metric, series, machineFilter='all') {
    const canvas = $(id);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (charts[id]) charts[id].destroy();
    const machines = [...new Set(series.map(r => r.machine_id).filter(Boolean))];
    const palette = ['#1685e6','#f59b20','#11a875'];
    const datasets = machines.map((machine, i) => {
      const rows = series.filter(r => r.machine_id === machine && r.value !== null);
      return { label: machine, data: rows.map(r => ({x: shortTime(r.timestamp), y: r.value})), borderColor: palette[i % palette.length], backgroundColor: palette[i % palette.length], pointRadius: 1.8, borderWidth: 2, tension: .28 };
    });
    charts[id] = new Chart(ctx, {type:'line',data:{datasets},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'nearest',intersect:false},plugins:{legend:{display:true,position:'top',labels:{boxWidth:6,usePointStyle:true,font:{size:9}}},tooltip:{callbacks:{label:(c)=>`${c.dataset.label}: ${number(c.parsed.y)}`}}},scales:{x:{ticks:{maxTicksLimit:6,font:{size:9},maxRotation:0},grid:{color:'#edf3f9'}},y:{beginAtZero:false,ticks:{font:{size:9}},grid:{color:'#edf3f9'}}}}});
  }
  function fillMachineFilter(machines) {
    const select = $('machineFilter'); const current = select.value || 'all';
    select.innerHTML = '<option value="all">All machines</option>' + machines.map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('');
    select.value = machines.includes(current) || current === 'all' ? current : 'all';
  }
  function renderStatus(data) {
    const list = $('machineStatusList');
    const summaries = data.summary || [];
    if (!summaries.length) { list.innerHTML = '<div class="empty-state">No machine data available.</div>'; return; }
    list.innerHTML = summaries.map(m => {
      const isAlert = Number(m.alert_pct || 0) > 30;
      const badge = isAlert ? 'REVIEW' : 'NORMAL';
      const text = isAlert ? `${number(m.alert_pct,1)}% of readings flagged for review` : 'Readings within demo thresholds';
      return `<div class="machine-status-item ${isAlert?'alert':'normal'}"><div class="machine-gear">⚙</div><div class="machine-info"><strong>${esc(m.machine_id)}</strong><p>${text}</p></div><span class="status-badge ${isAlert?'':'normal'}">${badge}</span></div>`;
    }).join('');
  }
  function renderSummary(data) {
    const body = $('summaryBody');
    if (!(data.summary || []).length) { body.innerHTML = '<tr><td colspan="8">No summary data available.</td></tr>'; return; }
    body.innerHTML = data.summary.map(m => {
      const review = Number(m.alert_pct || 0) > 30;
      return `<tr><td><strong>${esc(m.machine_id)}</strong></td><td>${m.readings ?? 0}</td><td>${number(m.avg_temperature)}</td><td>${number(m.avg_vibration)}</td><td>${number(m.avg_pressure)}</td><td>${m.alerts ?? 0}</td><td>${number(m.alert_pct,1)}%</td><td><span class="badge ${review?'':'good'}">${review?'REVIEW REQUIRED':'MONITOR'}</span></td></tr>`;
    }).join('');
  }
  function renderAlerts(data) {
    const body = $('alertsBody'); const alerts = (data.alerts || []).slice().reverse().slice(-12).reverse();
    $('alertSubtext').textContent = `${data.alert_count ?? alerts.length} flagged readings`;
    if (!alerts.length) { body.innerHTML = '<tr><td colspan="6">No readings currently require review.</td></tr>'; return; }
    body.innerHTML = alerts.map(r => `<tr><td>${esc(r.timestamp || '')}</td><td><strong>${esc(r.machine_id || '')}</strong></td><td>${number(r.temperature)}</td><td>${number(r.vibration)}</td><td>${number(r.pressure)}</td><td><span class="badge high">CHECK REQUIRED</span></td></tr>`).join('');
  }
  function renderInsights(data) {
    const summaries = data.summary || [];
    const highest = [...summaries].sort((a,b)=>(b.alert_pct||0)-(a.alert_pct||0))[0];
    const avg = key => {
      const vals = (data.records || []).map(r => Number(r[key])).filter(v => Number.isFinite(v));
      return vals.length ? vals.reduce((a,b)=>a+b,0)/vals.length : null;
    };
    const items = [
      highest ? `Highest review percentage: ${highest.machine_id} (${number(highest.alert_pct,1)}%).` : 'No machine summary is available yet.',
      `Average temperature across displayed readings: ${number(avg('temperature'))} °C.`,
      `Average vibration across displayed readings: ${number(avg('vibration'))} mm/s.`,
      `Average pressure across displayed readings: ${number(avg('pressure'))} bar.`
    ];
    $('insights').innerHTML = items.map((t,i)=>`<div class="insight"><span class="insight-icon">${['⚠','♨','≋','◉'][i]}</span><span>${esc(t)}</span></div>`).join('');
  }
  function renderHealthChart(data) {
    const summaries = data.summary || [];
    const review = summaries.filter(m => Number(m.alert_pct || 0) > 30).length;
    const monitor = summaries.length - review;
    $('healthMachineCount').textContent = summaries.length;
    if (charts.healthChart) charts.healthChart.destroy();
    charts.healthChart = new Chart($('healthChart').getContext('2d'), {type:'doughnut',data:{labels:['Review required','Monitor'],datasets:[{data:[review,monitor],backgroundColor:['#f12d37','#10a36d'],borderWidth:2,borderColor:'#fff'}]},options:{responsive:true,maintainAspectRatio:false,cutout:'72%',plugins:{legend:{display:false},tooltip:{enabled:true}}}});
    $('healthLegend').innerHTML = `<div><i style="background:#f12d37"></i><span>Review required</span><strong>${review} (${summaries.length?Math.round(review/summaries.length*100):0}%)</strong></div><div><i style="background:#10a36d"></i><span>Monitor</span><strong>${monitor} (${summaries.length?Math.round(monitor/summaries.length*100):0}%)</strong></div>`;
  }
  function render(data) {
    latestData = data;
    if (!data.ready) { toast(data.message || 'No data found.'); return; }
    $('totalReadings').textContent = data.total_readings ?? 0;
    $('machinesMonitored').textContent = data.machines_monitored ?? 0;
    $('alertCount').textContent = data.alert_count ?? 0;
    $('normalCount').textContent = data.normal_count ?? 0;
    fillMachineFilter(data.machines || []);
    const reportSelect = $('reportMachine');
    if (reportSelect) {
      const prior = reportSelect.value;
      reportSelect.innerHTML = '<option value="">Select machine</option>' + (data.machines || []).map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('');
      if ((data.machines || []).includes(prior)) reportSelect.value = prior;
    }
    renderStatus(data); renderSummary(data); renderAlerts(data); renderInsights(data); renderHealthChart(data);
    const series = data.metric_series || [];
    makeLineChart('temperatureChart','temperature',series.map(r=>({...r,value:((data.records||[]).find(x=>x.timestamp===r.timestamp&&x.machine_id===r.machine_id)||{}).temperature ?? null})));
    makeLineChart('vibrationChart','vibration',series.map(r=>({...r,value:((data.records||[]).find(x=>x.timestamp===r.timestamp&&x.machine_id===r.machine_id)||{}).vibration ?? null})));
    makeLineChart('pressureChart','pressure',series.map(r=>({...r,value:((data.records||[]).find(x=>x.timestamp===r.timestamp&&x.machine_id===r.machine_id)||{}).pressure ?? null})));
    const exportButton = $('exportButton');
    const role = document.body.dataset.role || '';
    if (!['Admin','Maintenance Engineer'].includes(role)) { exportButton.style.display = 'none'; }
  }

  function reportQuery() {
    const params = new URLSearchParams();
    params.set('machine', $('reportMachine').value);
    if ($('reportStart').value) params.set('start', $('reportStart').value);
    if ($('reportEnd').value) params.set('end', $('reportEnd').value);
    return params.toString();
  }
  async function generateMachineReport() {
    const machine = $('reportMachine').value;
    if (!machine) { toast('Please select a machine first.'); return; }
    if ($('reportStart').value && $('reportEnd').value && $('reportStart').value > $('reportEnd').value) {
      toast('Start date must be before the end date.'); return;
    }
    const output = $('machineReportResult');
    output.innerHTML = '<p>Generating machine report…</p>';
    try {
      const response = await fetch('/api/report?' + reportQuery());
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Report could not be generated.');
      const metricCard = (title, stat, unit) => `<div class="kpi-card blue"><div><span>${title}</span><strong>${stat ?? '—'}</strong><small>${unit}</small></div></div>`;
      const s = data.stats || {};
      const canExport = ['Admin','Maintenance Engineer'].includes(document.body.dataset.role);
      const csvLink = canExport ? `<a class="primary-button" href="/api/report.csv?${reportQuery()}">Download this machine CSV ↓</a>` : '';
      output.innerHTML = `
        <div class="panel-heading dark"><h2>${esc(data.machine_id)} — Detailed Health Report</h2><span class="badge ${data.status==='REVIEW REQUIRED'?'high':'good'}">${esc(data.status)}</span></div>
        <p class="permission-note">Generated: ${esc(data.generated_at)} · Period: ${esc(data.date_from)} to ${esc(data.date_to)}</p>
        <div class="kpi-grid" style="margin:14px 0">
          ${metricCard('Total readings',data.total_readings,'Sensor records')}
          ${metricCard('Flagged readings',data.flagged_readings,'Require review')}
          ${metricCard('Normal readings',data.normal_readings,'Within demo rules')}
          ${metricCard('Flagged percentage',data.flagged_percentage+'%','Of selected readings')}
        </div>
        <div class="table-wrap"><table><thead><tr><th>Sensor</th><th>Average</th><th>Minimum</th><th>Maximum</th><th>Valid readings</th></tr></thead><tbody>
          ${[['Temperature','temperature','°C'],['Vibration','vibration','mm/s'],['Pressure','pressure','bar']].map(([label,key,unit])=>`<tr><td>${label} (${unit})</td><td>${number(s[key]?.average)}</td><td>${number(s[key]?.minimum)}</td><td>${number(s[key]?.maximum)}</td><td>${s[key]?.valid_readings ?? 0}</td></tr>`).join('')}
        </tbody></table></div>
        <h3 style="margin:18px 0 8px">Recent flagged readings</h3>
        <div class="table-wrap"><table><thead><tr><th>Timestamp</th><th>Temperature</th><th>Vibration</th><th>Pressure</th><th>Status</th></tr></thead><tbody>
          ${(data.recent_flagged || []).length ? data.recent_flagged.map(r=>`<tr><td>${esc(r.timestamp||'')}</td><td>${number(r.temperature)}</td><td>${number(r.vibration)}</td><td>${number(r.pressure)}</td><td><span class="badge high">CHECK REQUIRED</span></td></tr>`).join('') : '<tr><td colspan="5">No flagged readings in this period.</td></tr>'}
        </tbody></table></div>
        <p class="permission-note" style="margin-top:12px">${esc(data.threshold_note)}</p>${csvLink}`;
    } catch (error) {
      output.innerHTML = `<p class="permission-note">${esc(error.message)}</p>`;
    }
  }
  async function loadUsers() {
    const response = await fetch('/api/settings/users');
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not load users.');
    $('usersBody').innerHTML = (data.users || []).map(u=>`<tr><td>${esc(u.username)}</td><td>${esc(u.role)}</td><td>${u.active ? 'Yes':'No'}</td><td>${esc(u.created_at || '')}</td></tr>`).join('') || '<tr><td colspan="4">No accounts found.</td></tr>';
  }
  async function initSettings() {
    if (document.body.dataset.role !== 'Admin') return;
    $('adminSettings').style.display = 'block';
    $('settingsRestricted').style.display = 'none';
    try { await loadUsers(); } catch (e) { $('settingsMessage').textContent = e.message; }
  }
  $('generateReport')?.addEventListener('click', generateMachineReport);
  $('createUserForm')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = $('settingsMessage');
    try {
      const response = await fetch('/api/settings/users', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({username:$('newUsername').value.trim(),password:$('newPassword').value,role:$('newRole').value})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not create account.');
      message.textContent = data.message;
      $('createUserForm').reset();
      await loadUsers();
    } catch (e) { message.textContent = e.message; }
  });
  initSettings();

  async function loadDashboard() {
    const machine = $('machineFilter').value || 'all';
    const metric = $('metricFilter').value || 'temperature';
    try {
      const response = await fetch(`/api/dashboard?machine=${encodeURIComponent(machine)}&metric=${encodeURIComponent(metric)}`, {headers:{'Accept':'application/json'}});
      if (response.status === 401) { window.location.href = '/login'; return; }
      if (!response.ok) throw new Error(`Dashboard request failed (${response.status})`);
      const data = await response.json();
      if (data.ready) {
        // Use the full dataset for the charts; API's selected metric controls its series.
        const selected = machine;
        if (selected !== 'all') data.metric_series = (data.metric_series || []).filter(r => r.machine_id === selected);
      }
      render(data);
      $('currentDate').textContent = data.updated_at || new Date().toLocaleString();
    } catch (error) {
      console.error(error);
      toast('Could not load dashboard data. Check that Flask is running and CSV files exist.');
    }
  }
  $('machineFilter').addEventListener('change', loadDashboard);
  $('metricFilter').addEventListener('change', loadDashboard);
  $('menuButton').addEventListener('click', () => $('sidebar').classList.toggle('collapsed'));
  document.querySelectorAll('.nav-item').forEach(link => link.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    link.classList.add('active');
    if (window.innerWidth < 800) $('sidebar').classList.add('collapsed');
  }));
  loadDashboard();
  setInterval(loadDashboard, 60000);
})();