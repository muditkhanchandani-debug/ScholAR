/**
 * ScholAR — Frontend Application Logic
 *
 * Handles: input → API call → loading → structured result rendering.
 */

// ===== State =====
let currentResult = null;
let activeTab = 'overview';
let isLoading = false;

// ===== DOM Elements =====
const input = document.getElementById('research-input');
const submitBtn = document.getElementById('submit-btn');
const resultsArea = document.getElementById('results-area');
const headerStatus = document.getElementById('header-status');
const logsContainer = document.getElementById('logs-container');

// ===== Log System =====
function addLog(category, message, type = 'info') {
  const now = new Date();
  const time = now.toTimeString().slice(0, 8);
  const entry = document.createElement('div');
  entry.className = `log-entry log-${type}`;
  entry.innerHTML = `<span class="log-time">${time}</span><span class="log-cat">${category}</span><span class="log-msg">${message}</span>`;
  logsContainer.appendChild(entry);
  logsContainer.scrollTop = logsContainer.scrollHeight;
}

function logDivider() {
  const hr = document.createElement('hr');
  hr.className = 'log-divider';
  logsContainer.appendChild(hr);
}

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
  headerStatus.textContent = 'Processing...';

  logDivider();
  addLog('INPUT', `Query: "${topic.length > 60 ? topic.slice(0, 60) + '...' : topic}"`, 'info');
  addLog('SYSTEM', 'Starting analysis pipeline', 'ok');
  const startTime = performance.now();

  resultsArea.innerHTML = `
    <div class="loading-container">
      <div class="loading-text">Processing...</div>
      <div class="loading-sub">Analyzing, critiquing, and forming a judgment</div>
    </div>
  `;

  try {
    addLog('API', 'POST /api/analyze', 'info');
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic }),
    });

    const elapsed = ((performance.now() - startTime) / 1000).toFixed(1);
    addLog('API', `Response ${response.status} — ${elapsed}s`, response.ok ? 'ok' : 'err');

    currentResult = await response.json();
    addLog('PARSE', 'JSON valid — ' + Object.keys(currentResult).length + ' fields', 'ok');
    console.log('[ScholAR] Result:', currentResult);

    // Log data summary
    logDataSummary(currentResult);

    headerStatus.textContent = 'Analysis complete';
    addLog('RENDER', 'Rendering results', 'ok');
    renderResult();
  } catch (err) {
    console.error('[ScholAR] Error:', err);
    addLog('ERROR', err.message || 'Unknown error', 'err');
    headerStatus.textContent = 'Error';
    showError('Could not analyze properly. Try again.');
  } finally {
    isLoading = false;
    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Run Analysis <span style="font-size:14px">\u2192</span>';
  }
}

function logDataSummary(d) {
  const fields = [
    ['summary', typeof d.summary === 'string' && d.summary.length > 10],
    ['insights', Array.isArray(d.insights) ? d.insights.length + ' items' : false],
    ['critique', Array.isArray(d.critique) ? d.critique.length + ' items' : false],
    ['failure_scenarios', Array.isArray(d.failure_scenarios) ? d.failure_scenarios.length + ' items' : false],
    ['simulation', d.simulation && d.simulation.outcome ? d.simulation.outcome : false],
    ['evidence', Array.isArray(d.evidence_sources) ? d.evidence_sources.length + ' items' : false],
    ['contradictions', Array.isArray(d.contradictions) ? d.contradictions.length + ' items' : false],
    ['trust_score', d.trust_score ? d.trust_score.level : false],
    ['recommendation', d.recommendation || false],
    ['related_topics', Array.isArray(d.related_topics) ? d.related_topics.length + ' items' : false],
    ['internal_debate', d.internal_debate && d.internal_debate.conclusion ? 'present' : false],
    ['future_relevance', d.future_relevance ? d.future_relevance.level : false],
    ['visual_indicators', d.visual_indicators ? 'present' : false],
    ['researcher_focus', typeof d.researcher_focus === 'string' && d.researcher_focus.length > 5 ? 'present' : false],
    ['new_research_idea', d.new_research_idea && d.new_research_idea.title ? 'present' : false],
  ];
  fields.forEach(([name, val]) => {
    if (val === false || val === undefined) {
      addLog('DATA', `${name}: missing`, 'warn');
    } else if (val === true) {
      addLog('DATA', `${name}: ok`, 'data');
    } else {
      addLog('DATA', `${name}: ${val}`, 'data');
    }
  });
}

// ===== Error State =====
function showError(message) {
  resultsArea.innerHTML = `
    <div class="section-card error-card">
      <div class="error-title">Analysis Failed</div>
      <div class="error-message">${esc(message)}</div>
      <button class="btn-retry" onclick="resultsArea.innerHTML=emptyStateHTML()">Dismiss</button>
    </div>
  `;
}

// ===== Escape HTML =====
function esc(s) {
  if (!s) return '';
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

// ===== Safe access =====
function safe(val, fallback) { return (val !== undefined && val !== null && val !== '') ? val : fallback; }

// ===== Safe array =====
function safeArray(val) { return Array.isArray(val) && val.length > 0 ? val : null; }

// ===== Result Rendering =====
function renderResult() {
  if (!currentResult) return;

  const tabs = ['overview', 'critique', 'break', 'simulation', 'evidence', 'intelligence'];
  const labels = {
    overview: 'Overview',
    critique: 'Critique',
    break: 'Break',
    simulation: 'Simulation',
    evidence: 'Evidence',
    intelligence: 'Intelligence',
  };

  const tabsHTML = `
    <div class="result-tabs">
      ${tabs.map(t =>
        `<button class="tab-btn ${activeTab === t ? 'active' : ''}" onclick="switchTab('${t}')">${labels[t]}</button>`
      ).join('')}
    </div>
  `;

  let contentHTML = '';
  if (activeTab === 'overview') contentHTML = renderOverview();
  else if (activeTab === 'critique') contentHTML = renderCritique();
  else if (activeTab === 'break') contentHTML = renderBreak();
  else if (activeTab === 'simulation') contentHTML = renderSimulation();
  else if (activeTab === 'evidence') contentHTML = renderEvidence();
  else if (activeTab === 'intelligence') contentHTML = renderIntelligence();

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

  // Recommendation + Trust
  const trustLevel = safe(d.trust_score?.level, 'Low');
  const trustClass = trustLevel.toLowerCase() === 'high' ? 'trust-high' : trustLevel.toLowerCase() === 'medium' ? 'trust-medium' : 'trust-low';

  html += `
    <div class="recommendation-card">
      <div style="flex:1">
        <div class="rec-label">Final Recommendation</div>
        <div class="rec-text">${esc(safe(d.recommendation, 'No recommendation available.'))}</div>
      </div>
      <div class="trust-badge ${trustClass}">${trustLevel.toUpperCase()}</div>
    </div>
  `;

  // Decision Highlights
  const highlights = d.decision_highlights || {};
  const strengths = safeArray(highlights.strengths);
  const risks = safeArray(highlights.risks);
  const uncertainties = safeArray(highlights.uncertainties);

  if (strengths || risks || uncertainties) {
    html += `<div class="section-card">`;
    html += `<div class="section-header"><span class="section-title">Decision Highlights</span></div>`;

    if (strengths) {
      html += `<div class="highlights-group">`;
      html += `<div class="highlights-label highlights-label-strength">Strengths</div>`;
      strengths.forEach(s => {
        html += `<div class="highlight-item">\u2713 ${esc(typeof s === 'string' ? s : JSON.stringify(s))}</div>`;
      });
      html += `</div>`;
    }
    if (risks) {
      html += `<div class="highlights-group">`;
      html += `<div class="highlights-label highlights-label-risk">Risks</div>`;
      risks.forEach(r => {
        html += `<div class="highlight-item">\u2022 ${esc(typeof r === 'string' ? r : JSON.stringify(r))}</div>`;
      });
      html += `</div>`;
    }
    if (uncertainties) {
      html += `<div class="highlights-group">`;
      html += `<div class="highlights-label highlights-label-uncertainty">Uncertainties</div>`;
      uncertainties.forEach(u => {
        html += `<div class="highlight-item">? ${esc(typeof u === 'string' ? u : JSON.stringify(u))}</div>`;
      });
      html += `</div>`;
    }

    html += `</div>`;
  }

  // Why This Decision
  const reasons = safeArray(d.why_this_decision) || ['No specific reasoning factors available.'];
  html += `
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">Why This Decision</span>
        <span class="section-count">${reasons.length}</span>
      </div>
      ${reasons.map((r, i) => `
        <div class="insight-item">
          <div class="insight-num">${i + 1}</div>
          <div class="insight-text">${esc(typeof r === 'string' ? r : JSON.stringify(r))}</div>
        </div>
      `).join('')}
    </div>
  `;

  // Summary
  html += `
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">Summary</span>
      </div>
      <div class="summary-text">${esc(safe(d.summary, 'No summary available.'))}</div>
    </div>
  `;

  // Insights
  const insights = safeArray(d.insights) || ['No strong signal found.'];
  html += `
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">Key Insights</span>
        <span class="section-count">${insights.length}</span>
      </div>
      ${insights.map((insight, i) => `
        <div class="insight-item">
          <div class="insight-num">${i + 1}</div>
          <div class="insight-text">${esc(typeof insight === 'string' ? insight : JSON.stringify(insight))}</div>
        </div>
      `).join('')}
    </div>
  `;

  return html;
}

// ===== Critique Tab =====
function renderCritique() {
  const d = currentResult;
  let html = '';

  const critique = safeArray(d.critique) || [{issue: 'No significant weaknesses identified.', severity: 'minor', explanation: ''}];
  html += `
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">Critical Analysis</span>
        <span class="section-count">${critique.length}</span>
      </div>
      ${critique.map(c => {
        const isObj = typeof c === 'object';
        const issue = isObj ? safe(c.issue, 'No data') : c;
        const severity = isObj ? safe(c.severity, 'moderate') : 'moderate';
        const explanation = isObj ? c.explanation : null;

        return `
          <div class="critique-item ${severity}">
            <div class="critique-header">
              <div class="severity-dot ${severity}"></div>
              <span class="severity-label">${severity.toUpperCase()}</span>
            </div>
            <div class="critique-issue">${esc(issue)}</div>
            ${explanation ? `<div class="critique-explanation">${esc(explanation)}</div>` : ''}
          </div>
        `;
      }).join('')}
    </div>
  `;

  // Trust Score
  const trustLevel = safe(d.trust_score?.level, 'Low');
  const trustCls = trustLevel.toLowerCase() === 'high' ? 'trust-high' : trustLevel.toLowerCase() === 'medium' ? 'trust-medium' : 'trust-low';
  const confidenceBasis = safe(d.trust_score?.confidence_basis, '');

  html += `
    <div class="trust-card ${trustCls}">
      <div class="trust-card-header">
        <div>
          <div class="trust-card-label">${trustLevel.toUpperCase()} CONFIDENCE</div>
          <div class="trust-card-sublabel">Trust Assessment</div>
        </div>
      </div>
      <div class="trust-card-reason">${esc(safe(d.trust_score?.reason, 'No assessment available.'))}</div>
      ${confidenceBasis ? `<div class="trust-card-basis">${esc(confidenceBasis)}</div>` : ''}
    </div>
  `;

  return html;
}

// ===== Break Tab =====
function renderBreak() {
  const d = currentResult;
  const scenarios = safeArray(d.failure_scenarios) || [{scenario: 'No critical failure scenarios identified.', likelihood: 'low', impact: ''}];

  return `
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">Failure Scenarios</span>
        <span class="section-count">${scenarios.length}</span>
      </div>
      ${scenarios.map(f => {
        const isObj = typeof f === 'object';
        const scenario = isObj ? safe(f.scenario, 'No data') : f;
        const likelihood = isObj ? safe(f.likelihood, 'medium') : 'medium';
        const impact = isObj ? f.impact : null;

        return `
          <div class="failure-item">
            <div class="failure-header">
              <span class="risk-badge ${likelihood}">${likelihood.toUpperCase()} RISK</span>
            </div>
            <div class="failure-text">${esc(scenario)}</div>
            ${impact ? `<div class="failure-impact"><strong>Impact:</strong> ${esc(impact)}</div>` : ''}
          </div>
        `;
      }).join('')}
    </div>
  `;
}

// ===== Simulation Tab =====
function renderSimulation() {
  const d = currentResult;
  const sim = d.simulation || {};
  let html = '';

  const outcome = safe(sim.outcome, safe(sim.overall_robustness, ''));
  if (outcome) {
    const rob = outcome.toLowerCase();
    const cls = rob.includes('strong') ? 'trust-high' : rob.includes('fragile') ? 'trust-low' : 'trust-medium';

    html += `
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">Simulation Results</span>
        </div>
        <div class="robustness-badge ${cls}">Outcome: ${esc(outcome)}</div>
      </div>
    `;
  }

  const vars = sim.variables || {};
  const varEntries = Object.entries(vars).filter(([, v]) => v && v !== 'No data');

  if (varEntries.length) {
    html += `<div class="section-card">`;
    html += `<div class="section-header"><span class="section-title">Variables</span></div>`;
    varEntries.forEach(([key, value]) => {
      const label = key.replace(/_/g, ' ');
      const text = (typeof value === 'string' ? value : '').toLowerCase();
      let impactLevel = 50;
      let barClass = 'moderate';
      if (text.includes('severe') || text.includes('significant') || text.includes('critical') || text.includes('fundamental')) {
        impactLevel = 80; barClass = 'high';
      } else if (text.includes('minimal') || text.includes('stable') || text.includes('low impact') || text.includes('strong')) {
        impactLevel = 25; barClass = 'low';
      }

      html += `
        <div class="sim-metric">
          <div class="sim-metric-header">
            <span class="sim-metric-label">${esc(label)}</span>
            <span class="sim-metric-value" style="color: ${barClass === 'high' ? 'var(--red)' : barClass === 'low' ? 'var(--accent)' : 'var(--amber)'}">${impactLevel}%</span>
          </div>
          <div class="impact-bar"><div class="impact-bar-fill ${barClass}" style="width: ${impactLevel}%"></div></div>
          <div class="sim-metric-explanation">${esc(typeof value === 'string' ? value : JSON.stringify(value))}</div>
        </div>
      `;
    });
    html += `</div>`;
  }

  if (sim.explanation) {
    html += `
      <div class="section-card">
        <div class="section-header"><span class="section-title">Explanation</span></div>
        <div class="summary-text">${esc(sim.explanation)}</div>
      </div>
    `;
  }

  if (!html) {
    html = '<div class="section-card"><div class="no-data">No simulation data available.</div></div>';
  }

  return html;
}

// ===== Evidence Tab =====
function renderEvidence() {
  const d = currentResult;
  let html = '';

  const evidence = safeArray(d.evidence_sources) || [{claim: 'No specific evidence could be identified for this topic.', basis: 'N/A', relevance: 'N/A'}];

  html += `
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">Evidence & Sources</span>
        <span class="section-count">${evidence.length}</span>
      </div>
      ${evidence.map(e => {
        const isObj = typeof e === 'object';
        const claim = isObj ? safe(e.claim, safe(e.source, 'No data')) : e;
        const basis = isObj ? safe(e.basis, safe(e.platform, '')) : '';
        const relevance = isObj ? safe(e.relevance, '') : '';

        return `
          <div class="evidence-item">
            <div class="evidence-claim">${esc(claim)}</div>
            ${basis ? `<div class="evidence-basis"><span class="evidence-basis-label">Basis:</span> ${esc(basis)}</div>` : ''}
            ${relevance ? `<div class="evidence-relevance"><span class="evidence-relevance-label">Relevance:</span> ${esc(relevance)}</div>` : ''}
          </div>
        `;
      }).join('')}
    </div>
  `;

  const contradictions = safeArray(d.contradictions) || [{finding_a: 'N/A', finding_b: 'N/A', reason: 'No contradictions identified \u2014 the field may have general consensus on this topic.'}];

  html += `
    <div class="section-card">
      <div class="section-header">
        <span class="section-title">Contradictions in Research</span>
        <span class="section-count">${contradictions.length}</span>
      </div>
      ${contradictions.map(c => {
        const isObj = typeof c === 'object';
        const findingA = isObj ? safe(c.finding_a, 'N/A') : c;
        const findingB = isObj ? safe(c.finding_b, 'N/A') : '';
        const reason = isObj ? safe(c.reason, '') : '';

        const hasFindings = findingA !== 'N/A' && findingB !== 'N/A';

        if (hasFindings) {
          return `
            <div class="contradiction-item">
              <div class="contradiction-claims">
                <div class="contradiction-claim claim-a">
                  <div class="claim-label">Claim A</div>
                  <div class="claim-text">${esc(findingA)}</div>
                </div>
                <div class="contradiction-vs">vs</div>
                <div class="contradiction-claim claim-b">
                  <div class="claim-label">Claim B</div>
                  <div class="claim-text">${esc(findingB)}</div>
                </div>
              </div>
              ${reason ? `<div class="contradiction-reason"><span class="contradiction-reason-label">Why they differ:</span> ${esc(reason)}</div>` : ''}
            </div>
          `;
        } else {
          return `
            <div class="contradiction-item">
              <div class="contradiction-consensus">${esc(reason || 'No contradictions identified.')}</div>
            </div>
          `;
        }
      }).join('')}
    </div>
  `;

  return html;
}

// ===== Text-based bar builder =====
function textBar(score, max) {
  const s = Math.max(0, Math.min(max, parseInt(score) || 0));
  return '\u2588'.repeat(s) + '\u2591'.repeat(max - s);
}

// ===== Intelligence Tab =====
function renderIntelligence() {
  const d = currentResult;
  let html = '';

  // --- Visual Indicators ---
  const vi = d.visual_indicators || {};
  const indicators = ['reliability', 'novelty', 'impact', 'reproducibility', 'risk'];
  const hasIndicators = indicators.some(k => parseInt(vi[k]) > 0);

  if (hasIndicators) {
    html += `
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">Visual Indicators</span>
        </div>
        <div class="indicator-grid">
          ${indicators.map(k => {
            const val = Math.max(0, Math.min(5, parseInt(vi[k]) || 0));
            const colorClass = k === 'risk' ? (val >= 4 ? 'ind-low' : val >= 2 ? 'ind-mid' : 'ind-high') : (val >= 4 ? 'ind-high' : val >= 2 ? 'ind-mid' : 'ind-low');
            return `
              <div class="indicator-row">
                <span class="indicator-label">${esc(k.charAt(0).toUpperCase() + k.slice(1))}</span>
                <span class="indicator-bar ${colorClass}">${textBar(val, 5)}</span>
                <span class="indicator-val">${val}/5</span>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

  // --- Internal Debate ---
  const debate = d.internal_debate || {};
  if (debate.argument_for || debate.argument_against || debate.conclusion) {
    html += `
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">Internal Debate</span>
        </div>
        ${debate.argument_for ? `
          <div class="debate-block debate-for">
            <div class="debate-label debate-label-for">Argument For</div>
            <div class="debate-text">${esc(debate.argument_for)}</div>
          </div>` : ''}
        ${debate.argument_against ? `
          <div class="debate-block debate-against">
            <div class="debate-label debate-label-against">Argument Against</div>
            <div class="debate-text">${esc(debate.argument_against)}</div>
          </div>` : ''}
        ${debate.conclusion ? `
          <div class="debate-conclusion">
            <span class="debate-conclusion-label">Conclusion:</span> ${esc(debate.conclusion)}
          </div>` : ''}
      </div>
    `;
  }

  // --- Future Relevance ---
  const fr = d.future_relevance || {};
  if (fr.level && fr.level !== 'Unknown') {
    const frClass = fr.level.toLowerCase() === 'high' ? 'trust-high' : fr.level.toLowerCase() === 'medium' ? 'trust-medium' : 'trust-low';
    html += `
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">Future Relevance</span>
        </div>
        <div class="future-row">
          <span class="robustness-badge ${frClass}">${esc(fr.level.toUpperCase())}</span>
          ${fr.reasoning ? `<span class="future-reasoning">${esc(fr.reasoning)}</span>` : ''}
        </div>
      </div>
    `;
  }

  // --- Related Topics ---
  const topics = safeArray(d.related_topics);
  if (topics) {
    html += `
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">Related Topics</span>
          <span class="section-count">${topics.length}</span>
        </div>
        <div class="related-topics-list">
          ${topics.map(t => `<span class="related-topic-tag">${esc(typeof t === 'string' ? t : JSON.stringify(t))}</span>`).join('')}
        </div>
      </div>
    `;
  }

  // --- Global Research Context ---
  const grc = d.global_research_context || {};
  const regions = safeArray(grc.active_regions);
  if (regions || grc.summary) {
    html += `
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">Global Research Context</span>
        </div>
        ${regions ? `<div class="region-list">${regions.map(r => `<span class="region-tag">${esc(typeof r === 'string' ? r : JSON.stringify(r))}</span>`).join('')}</div>` : ''}
        ${grc.summary ? `<div class="summary-text" style="margin-top:6px">${esc(grc.summary)}</div>` : ''}
      </div>
    `;
  }

  // --- Researcher Focus ---
  const rf = d.researcher_focus;
  if (rf && typeof rf === 'string' && rf.trim()) {
    html += `
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">Researcher Focus</span>
        </div>
        <div class="summary-text">${esc(rf)}</div>
      </div>
    `;
  }

  // --- New Research Idea ---
  const nri = d.new_research_idea || {};
  if (nri.title || nri.explanation) {
    html += `
      <div class="section-card idea-card">
        <div class="section-header">
          <span class="section-title">New Research Idea</span>
        </div>
        ${nri.title ? `<div class="idea-title">${esc(nri.title)}</div>` : ''}
        ${nri.explanation ? `<div class="idea-explanation">${esc(nri.explanation)}</div>` : ''}
      </div>
    `;
  }

  if (!html) {
    html = '<div class="section-card"><div class="no-data">No intelligence data available.</div></div>';
  }

  return html;
}

// ===== Empty State =====
function emptyStateHTML() {
  return `
    <div class="empty-state">
      <div class="empty-orb">S</div>
      <div class="empty-title">Research Decision Engine</div>
      <div class="empty-desc">Enter a research topic or paste a paper abstract to get an opinionated analysis, critique, and clear decision.</div>
      <div class="capabilities-grid">
        <div class="capability-card"><div class="capability-label">Deep Analysis</div><div class="capability-desc">Extract insights</div></div>
        <div class="capability-card"><div class="capability-label">Peer Critique</div><div class="capability-desc">Find weaknesses</div></div>
        <div class="capability-card"><div class="capability-label">Break Papers</div><div class="capability-desc">Failure modes</div></div>
        <div class="capability-card"><div class="capability-label">Simulate</div><div class="capability-desc">Stress-test</div></div>
      </div>
    </div>
  `;
}

// Initialize
resultsArea.innerHTML = emptyStateHTML();
addLog('SYSTEM', 'Engine initialized', 'ok');
addLog('SYSTEM', 'Ready for analysis', 'info');
