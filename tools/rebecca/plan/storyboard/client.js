(() => {
  'use strict';
  const storageKey = 'rebecca-storyboard-edits-v1';
  const status = document.querySelector('#save-status');
  const fields = [...document.querySelectorAll('textarea[data-field]')];
  // Notes on an earlier version of a scene stay saved and show read-only.
  const history = [...document.querySelectorAll('.old-note')];
  const keyOf = (el) => JSON.stringify([el.dataset.room, el.dataset.field]);
  let edits = new Map();
  let stored = [];
  try {
    const value = JSON.parse(localStorage.getItem(storageKey) || '[]');
    if (!Array.isArray(value)) throw new Error('Saved edits are not a list');
    for (const row of value) {
      if (!row || typeof row !== 'object' || !['room', 'field', 'old', 'value', 'mode'].every((k) => typeof row[k] === 'string') || !['edit', 'note'].includes(row.mode)) throw new Error('Invalid saved edit');
    }
    stored = value;
    edits = new Map(stored.map((e) => [JSON.stringify([e.room, e.field]), e]));
  } catch {
    status.textContent = 'Saved edits could not be read. Copy before clearing.';
  }
  function fitGoal(el) {
    if (!el.closest('.goals')) return;
    el.style.height = 'auto';
    el.style.height = `${Math.max(86, el.scrollHeight + 2)}px`;
  }
  function fillFields() {
    for (const el of fields) {
      const edit = edits.get(keyOf(el));
      el.value = edit ? edit.value : el.dataset.mode === 'edit' ? el.dataset.old : '';
      el.classList.toggle('edited', Boolean(edit));
      el.parentElement.querySelector('.source-warning')?.remove();
      if (edit && edit.old !== el.dataset.old) {
        const warning = document.createElement('small');
        warning.className = 'source-warning';
        warning.textContent = 'Source changed since this edit. Copy includes both source versions.';
        el.after(warning);
      }
    }
  }
  function fillHistory() {
    for (const el of history) {
      const edit = edits.get(keyOf(el));
      el.querySelector('.words').textContent = edit ? edit.value : '';
      el.hidden = !edit;
    }
    for (const box of document.querySelectorAll('.note-history')) box.hidden = !box.querySelector('.old-note:not([hidden])');
  }
  function savedStatus() {
    const stale = [...edits].filter(([key, e]) => {
      const current = fields.find((el) => keyOf(el) === key);
      if (history.some((el) => keyOf(el) === key)) return false;
      return !current || current.dataset.old !== e.old;
    }).length;
    return edits.size ? `${edits.size} edits saved here${stale ? ` · ${stale} need source review` : ''}` : 'Edits stay in this browser';
  }
  function save() {
    try {
      localStorage.setItem(storageKey, JSON.stringify([...edits.values()]));
      status.textContent = savedStatus();
    } catch {
      status.textContent = 'Storage is full or blocked. Copy your edits now.';
    }
  }
  for (const el of fields) el.addEventListener('input', () => {
    const key = keyOf(el);
    const previous = edits.get(key);
    if (el.value === (el.dataset.mode === 'edit' ? el.dataset.old : '')) edits.delete(key);
    else edits.set(key, { room: el.dataset.room, field: el.dataset.field, old: previous?.old ?? el.dataset.old, value: el.value, mode: el.dataset.mode });
    // Audit rows and scene rows share the same edit, as do both item tables.
    for (const other of fields) if (other !== el && keyOf(other) === key) {
      other.value = el.value;
      other.classList.toggle('edited', edits.has(key));
    }
    el.classList.toggle('edited', edits.has(key));
    fitGoal(el);
    save();
  });
  fillFields();
  fillHistory();
  if (edits.size) status.textContent = savedStatus();

  function showView() {
    const id = location.hash.slice(1) || 'flow';
    const target = document.getElementById(id);
    const valid = target && (target.classList.contains('view') || target.classList.contains('scene'));
    const selected = valid ? target : document.querySelector('#flow');
    for (const video of document.querySelectorAll('video')) if (!selected.contains(video)) video.pause();
    for (const el of document.querySelectorAll('.view,.scene')) el.hidden = el !== selected;
    for (const a of document.querySelectorAll('.views a')) {
      if (a.hash === `#${selected.id}`) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    }
    for (const el of selected.querySelectorAll('.goals textarea')) fitGoal(el);
    window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', showView);
  showView();
  document.querySelector('#act-filter').addEventListener('change', (event) => {
    for (const el of document.querySelectorAll('.act')) el.hidden = event.target.value !== 'all' && el.dataset.act !== event.target.value;
  });
  document.querySelector('#map-toggle').addEventListener('click', (event) => {
    const enabled = event.currentTarget.getAttribute('aria-pressed') !== 'true';
    event.currentTarget.setAttribute('aria-pressed', String(enabled));
    event.currentTarget.textContent = enabled ? 'Show play order' : 'Show branches';
    document.querySelector('#map-key').hidden = !enabled;
    for (const el of document.querySelectorAll('.branch-map')) el.hidden = !enabled;
    for (const el of document.querySelectorAll('.route-cards')) el.hidden = enabled;
  });
  const quote = (s) => s.split('\n').map((line) => `> ${line}`).join('\n');
  function markdown() {
    const rooms = new Map();
    for (const edit of edits.values()) {
      if (!rooms.has(edit.room)) rooms.set(edit.room, []);
      rooms.get(edit.room).push(edit);
    }
    if (!edits.size) return '# Rebecca\'s day edits\n\nNo edits yet.\n';
    return '# Rebecca\'s day edits\n\n' + [...rooms].map(([room, rows]) => `## ${room}\n\n` + rows.map((e) => {
      const current = fields.find((el) => el.dataset.room === e.room && el.dataset.field === e.field);
      const earlier = history.find((el) => el.dataset.room === e.room && el.dataset.field === e.field);
      if (earlier) return `### scene notes on version ${earlier.dataset.version}, before the latest rebuild\n\n${quote(e.value)}\n`;
      const change = !current ? '\nSource warning: this field is no longer on the page.\n' : current.dataset.old !== e.old ? `\nCurrent source value:\n${quote(current.dataset.old || 'Empty')}\n` : '';
      return `### ${e.field.replace(/^scene notes v(\d+)$/, 'scene notes on version $1')}\n\nOld value:\n${quote(e.old || 'Empty')}\n${change}\n${e.mode === 'edit' ? 'New value' : 'Note'}:\n${quote(e.value)}\n`;
    }).join('\n')).join('\n');
  }
  const exportDialog = document.querySelector('#export-dialog');
  document.querySelector('#copy').addEventListener('click', async () => {
    const content = markdown();
    document.querySelector('#export-text').value = content;
    exportDialog.showModal();
    try {
      await navigator.clipboard.writeText(content);
      document.querySelector('#copy-result').textContent = 'Copied. Paste this markdown back to the agent.';
    } catch {
      document.querySelector('#copy-result').textContent = 'Clipboard is blocked. Select and copy the markdown below.';
      document.querySelector('#export-text').select();
    }
  });
  document.querySelector('#close-export').addEventListener('click', () => exportDialog.close());
  const clearDialog = document.querySelector('#clear-dialog');
  document.querySelector('#clear').addEventListener('click', () => clearDialog.showModal());
  document.querySelector('#cancel-clear').addEventListener('click', () => clearDialog.close());
  document.querySelector('#confirm-clear').addEventListener('click', () => {
    edits.clear();
    fillFields();
    fillHistory();
    save();
    clearDialog.close();
  });
})();
