/**
 * ScholAR — Frontend Application Logic
 *
 * Single-file JS for the research decision engine.
 * Handles: input, API calls, loading stages, result rendering.
 */

// ===== State =====
let currentResult = null;
let activeTab = 'overview';
let isLoading = false;
let loadingTimers = [];

// ===== DOM Elements =====
const input = document.getElementById('research-input');
const submitBtn = document.getElementById('submit-btn');
const resultsArea = document.getElementById('results-area');
const headerStatus = document.getElementById('header-status');

// ===== Event Listeners =====
submitBtn.addEventListener('click', handleSubmit);
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    handleSubmit();
  }
});

// ===== Submit Handler =====
async function handleSubmit() {
  const topic = input.value.trim();
  if (!topic || isLoading) return;

  isLoading = true;
  currentResult = null;
  activeTab = 'overview';
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<div class="spinner"></div> Analyzing...';
  headerStatus.textContent = `Analyzing: ${topic.substring(0, 80)}${topic.length > 80 ? '...' : ''}`;

  showLoading();

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      const msg = err.detail || `Request failed (${response.status})`;
      // Tag 401 errors so the frontend can show API key help
      if (response.status === 401) throw new Error(`[AUTH] ${msg}`);
      throw new Error(msg);
    }

    currentResult = await response.json();
    console.log('[ScholAR] Analysis result:', currentResult);
    headerStatus.textContent = 'Analysis complete ✓';
    renderResult();
  } catch (err) {
    console.error('[ScholAR] Error:', err);
    headerStatus.textContent = 'Error — see details below';
    showError(err.message);
  } finally {
    isLoading = false;
    loadingTimers.forEach(clearTimeout);
    loadingTimers = [];
    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Run Analysis <span style="font-size:16px">→</span>';
  }
}

// ===== Loading State =====
function showLoading() {
  const steps = [
    { icon: '🔍', label: 'Extracting core insights...', color: 'var(--cyan)' },
    { icon: '🧪', label: 'Running critical analysis...', color: 'var(--purple)' },
    { icon: '💥', label: 'Testing for failure scenarios...', color: 'var(--amber)' },
    { icon: '⚡', label: 'Simulating under stress...', color: 'var(--blue)' },
    { icon: '🎯', label: 'Forming final judgment...', color: 'var(--emerald)' },
  ];

  let currentStage = 0;

  function renderLoading() {
    resultsArea.innerHTML = `
      <div class="loading-container">
        <div class="loading-icon">
          <div class="loading-icon-glow"></div>
          <div class="loading-icon-emoji">${steps[Math.min(currentStage, steps.length - 1)].icon}</div>
        </div>
        <div class="loading-title">ScholAR is thinking<span class="dots">...</span></div>
        <div class="loading-subtitle">Analyzing, critiquing, and forming an opinionated judgment</div>
        <div class="loading-steps">
          ${steps.map((s, i) => {
            const cls = i === currentStage ? 'active' : i < currentStage ? 'done' : 'pending';
            const icon = i < currentStage ? '✅' : s.icon;
            return `
              <div class="loading-step ${cls}">
                <span class="loading-step-icon">${icon}</span>
                <span style="color: ${i === currentStage ? s.color : 'var(--text-secondary)'}">${s.label}</span>
                ${i === currentStage ? '<div class="step-progress"><div class="step-progress-bar"></div></div>' : ''}
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

  renderLoading();

  const delays = [800, 2000, 3500, 5500];
  delays.forEach((delay, i) => {
    const timer = setTimeout(() => {
      currentStage = i + 1;
      if (isLoading) renderLoading();
    }, delay);
    loadingTimers.push(timer);
  });
}

// ===== Error State =====
function showError(message) {
  const lc = message.toLowerCase();
  const isAuth = lc.includes('api key') || lc.includes('groq_api_key') || lc.includes('401') || lc.includes('invalid_api_key') || message.startsWith('[AUTH]');
  const cleanMessage = message.replace(/^\[AUTH\]\s*/, '');
  const icon = isAuth ? '🔑' : '❌';
  const title = isAuth ? 'API Key Issue' : 'Analysis Failed';

  resultsArea.innerHTML = `
    <div class="section-card error-card">
      <div class="error-icon">${icon}</div>
      <div class="error-title">${title}</div>
      <div class="error-message">${cleanMessage}</div>
      ${isAuth ? '<div style="font-size:11px;color:var(--text-muted);margin-bottom:20px">Set <code style="background:rgba(36,48,85,0.5);padding:2px 6px;border-radius:4px;color:var(--cyan)">GROQ_API_KEY</code> in your <code style="background:rgba(36,48,85,0.5);padding:2px 6px;border-radius:4px;color:var(--cyan)">.env</code> file</div>' : ''}
      <button class="btn-retry" onclick="resultsArea.innerHTML=emptyStateHTML()">Dismiss</button>
    </div>
  `;
}

// ===== Result Rendering =====
function renderResult() {
  if (!currentResult) return;

  const tabsHTML = `
    <div class="result-tabs">
      ${['overview', 'critique', 'break', 'simulation'].map(t => {
        const icons = { overview: '📋', critique: '🔍', break: '💥', simulation: '⚡' };
        const labels = { overview: 'Overview', critique: 'Critique', break: 'Break Paper', simulation: 'Simulation' };
        return `<button class="tab-btn ${activeTab === t ? 'active' : ''}" onclick="switchTab('${t}')">${icons[t]} ${labels[t]}</button>`;
      }).join('')}
    </div>
  `;

  let contentHTML = '';

  if (activeTab === 'overview') {
    contentHTML = renderOverview();
  } else if (activeTab === 'critique') {
    contentHTML = renderCritique();
  } else if (activeTab === 'break') {
    contentHTML = renderBreak();
  } else if (activeTab === 'simulation') {
    contentHTML = renderSimulation();
  }

  resultsArea.innerHTML = tabsHTML + contentHTML;
}

function switchTab(tab) {
  activeTab = tab;
  renderResult();
}

// ===== Overview Tab =====
function renderOverview() {
  const d = currentResult;
  let html = '';

  // Recommendation hero
  if (d.recommendation) {
    const trustLevel = d.trust_score?.level || 'Low';
    const trustClass = trustLevel.toLowerCase() === 'high' ? 'trust-high' : trustLevel.toLowerCase() === 'medium' ? 'trust-medium' : 'trust-low';
    const trustIcon = trustLevel.toLowerCase() === 'high' ? '🟢' : trustLevel.toLowerCase() === 'medium' ? '🟡' : '🔴';

    html += `
      <div class="recommendation-card">
        <div class="rec-icon">🎯</div>
        <div style="flex:1">
          <div class="rec-label">Final Recommendation</div>
          <div class="rec-text">${d.recommendation}</div>
        </div>
        <div class="trust-badge ${trustClass}">${trustIcon} ${trustLevel.toUpperCase()}</div>
      </div>
    `;
  }

  // Summary
  if (d.summary) {
    html += `
      <div class="section-card" style="animation-delay: 50ms">
        <div class="section-header">
          <span class="section-icon">📋</span>
          <span class="section-title">Summary</span>
        </div>
        <div class="summary-text">${d.summary}</div>
      </div>
    `;
  }

  // Insights
  if (d.insights?.length) {
    html += `
      <div class="section-card" style="animation-delay: 100ms">
        <div class="section-header">
          <span class="section-icon">💡</span>
          <span class="section-title">Key Insights</span>
          <span class="section-count">${d.insights.length}</span>
        </div>
        ${d.insights.map((insight, i) => `
          <div class="insight-item" style="animation-delay: ${(i + 2) * 60}ms">
            <div class="insight-num">${i + 1}</div>
            <div class="insight-text">${insight}</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  return html;
}

// ===== Critique Tab =====
function renderCritique() {
  const d = currentResult;
  let html = '';

  if (d.critique?.length) {
    html += `
      <div class="section-card">
        <div class="section-header">
          <span class="section-icon">🔍</span>
          <span class="section-title" style="color: var(--amber)">Critical Analysis</span>
          <span class="section-count">${d.critique.length}</span>
        </div>
        ${d.critique.map((c, i) => {
          const isObj = typeof c === 'object';
          const issue = isObj ? c.issue : c;
          const severity = isObj ? (c.severity || 'moderate') : 'moderate';
          const explanation = isObj ? c.explanation : null;

          return `
            <div class="critique-item ${severity}" style="animation-delay: ${i * 80}ms">
              <div class="critique-header">
                <div class="severity-dot ${severity}"></div>
                <span class="severity-label">${severity.toUpperCase()}</span>
              </div>
              <div class="critique-issue">${issue}</div>
              ${explanation ? `<div class="critique-explanation">${explanation}</div>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  // Trust score card (full)
  if (d.trust_score?.level) {
    const level = d.trust_score.level;
    const cls = level.toLowerCase() === 'high' ? 'trust-high' : level.toLowerCase() === 'medium' ? 'trust-medium' : 'trust-low';
    const icon = level.toLowerCase() === 'high' ? '🟢' : level.toLowerCase() === 'medium' ? '🟡' : '🔴';
    const label = `${level.toUpperCase()} CONFIDENCE`;

    html += `
      <div class="trust-card ${cls}">
        <div class="trust-card-header">
          <span class="trust-card-header-icon">${icon}</span>
          <div>
            <div class="trust-card-label">${label}</div>
            <div class="trust-card-sublabel">Trust Assessment</div>
          </div>
        </div>
        ${d.trust_score.reason ? `<div class="trust-card-reason">${d.trust_score.reason}</div>` : ''}
      </div>
    `;
  }

  if (!d.critique?.length && !d.trust_score?.level) {
    html = '<div class="section-card"><p style="color:var(--text-muted);text-align:center;padding:20px">No critique data available.</p></div>';
  }

  return html;
}

// ===== Break Tab =====
function renderBreak() {
  const d = currentResult;
  let html = '';

  if (d.failure_scenarios?.length) {
    html += `
      <div class="section-card">
        <div class="section-header">
          <span class="section-icon">💥</span>
          <span class="section-title" style="color: var(--red)">Failure Scenarios</span>
          <span class="section-count">${d.failure_scenarios.length}</span>
        </div>
        ${d.failure_scenarios.map((f, i) => {
          const isObj = typeof f === 'object';
          const scenario = isObj ? f.scenario : f;
          const likelihood = isObj ? (f.likelihood || 'medium') : 'medium';
          const impact = isObj ? f.impact : null;

          return `
            <div class="failure-item" style="animation-delay: ${i * 80}ms">
              <div class="failure-header">
                <span class="emoji">💥</span>
                <span class="risk-badge ${likelihood}">${likelihood.toUpperCase()} RISK</span>
              </div>
              <div class="failure-text">${scenario}</div>
              ${impact ? `<div class="failure-impact"><strong>Impact:</strong> ${impact}</div>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
  } else {
    html = '<div class="section-card"><p style="color:var(--text-muted);text-align:center;padding:20px">No failure scenarios identified.</p></div>';
  }

  return html;
}

// ===== Simulation Tab =====
function renderSimulation() {
  const d = currentResult;
  const sim = d.simulation || {};
  let html = '';

  // Robustness badge
  if (sim.overall_robustness) {
    const rob = sim.overall_robustness.toLowerCase();
    const cls = rob.includes('strong') ? 'trust-high' : rob.includes('fragile') ? 'trust-low' : 'trust-medium';
    html += `
      <div class="section-card">
        <div class="section-header">
          <span class="section-icon">⚡</span>
          <span class="section-title" style="color: var(--blue)">Simulation Insights</span>
        </div>
        <div class="robustness-badge ${cls}">Robustness: ${sim.overall_robustness}</div>
      </div>
    `;
  }

  // Impact bars
  const metrics = [
    { key: 'noise_impact', label: 'Noise Impact', icon: '📡', value: sim.noise_impact },
    { key: 'data_sensitivity', label: 'Data Sensitivity', icon: '📊', value: sim.data_sensitivity },
    { key: 'bias_vulnerability', label: 'Bias Vulnerability', icon: '⚖️', value: sim.bias_vulnerability },
  ].filter(m => m.value);

  if (metrics.length) {
    html += `<div class="section-card" style="animation-delay: 100ms">`;
    metrics.forEach((m, i) => {
      // Estimate impact level from text (heuristic: look for severity words)
      const text = m.value.toLowerCase();
      let impactLevel = 50;
      let barClass = 'moderate';
      if (text.includes('severe') || text.includes('significantly') || text.includes('critical') || text.includes('fundamentally')) {
        impactLevel = 80; barClass = 'high';
      } else if (text.includes('minimal') || text.includes('stable') || text.includes('low')) {
        impactLevel = 25; barClass = 'low';
      }

      html += `
        <div class="sim-metric" style="animation-delay: ${(i + 2) * 80}ms">
          <div class="sim-metric-header">
            <span class="sim-metric-icon">${m.icon}</span>
            <span class="sim-metric-label">${m.label}</span>
            <span class="sim-metric-value" style="color: ${barClass === 'high' ? 'var(--red)' : barClass === 'low' ? 'var(--emerald)' : 'var(--amber)'}">${impactLevel}%</span>
          </div>
          <div class="impact-bar">
            <div class="impact-bar-fill ${barClass}" style="width: ${impactLevel}%"></div>
          </div>
          <div class="sim-metric-explanation">${m.value}</div>
        </div>
      `;
    });
    html += `</div>`;
  }

  if (!sim.overall_robustness && !metrics.length) {
    html = '<div class="section-card"><p style="color:var(--text-muted);text-align:center;padding:20px">No simulation data available.</p></div>';
  }

  return html;
}

// ===== Empty State =====
function emptyStateHTML() {
  return `
    <div class="empty-state">
      <div class="empty-orb">
        <div class="empty-orb-glow"></div>
        <div class="empty-orb-icon">🔬</div>
      </div>
      <div class="empty-title">Research Decision Engine</div>
      <div class="empty-desc">Enter a research topic or paste a paper abstract to get an opinionated analysis, critique, and clear decision.</div>
      <div class="capabilities-grid">
        <div class="capability-card">
          <div class="capability-icon">🔬</div>
          <div class="capability-label">Deep Analysis</div>
          <div class="capability-desc">Extract core insights</div>
        </div>
        <div class="capability-card">
          <div class="capability-icon">🔍</div>
          <div class="capability-label">Peer Critique</div>
          <div class="capability-desc">Find weaknesses</div>
        </div>
        <div class="capability-card">
          <div class="capability-icon">💥</div>
          <div class="capability-label">Break Papers</div>
          <div class="capability-desc">Test failure modes</div>
        </div>
        <div class="capability-card">
          <div class="capability-icon">⚡</div>
          <div class="capability-label">Simulate</div>
          <div class="capability-desc">Stress-test ideas</div>
        </div>
      </div>
    </div>
  `;
}

// Initialize with empty state
resultsArea.innerHTML = emptyStateHTML();
