// The dashboard page: reads the server's event stream (server.ts) and draws the
// state. The map is top-down with X to the right and Z up. Room coordinates
// are unsigned 16-bit, as the collision and camera zone tests read them.
const $ = (id) => document.getElementById(id);
const hex = (n) => n.toString(16).toUpperCase();
const u16 = (v) => (v < 0 ? v + 65536 : v);

let items = {};
let state;
let map; // the current room's RoomMap from /room, or null while it loads
let mapKey = '';
let area = -1; // the floor area she was last seen in (rdt.ts floor())
let prevBanks = [];
const trail = [];

const itemName = (id) => items[id] ?? `item ${hex(id)}`;

function send(line) {
  return fetch('/cmd', { method: 'POST', body: line }).then(async (r) => {
    if (!r.ok) addLog({ at: Date.now(), frame: state?.frame ?? 0, level: 'error', text: `${line}: ${await r.text()}` });
  });
}

// ---- log ---------------------------------------------------------------------

function addLog(e) {
  const li = document.createElement('li');
  li.className = e.level;
  li.dataset.level = e.level;
  const t = document.createElement('span');
  t.className = 't';
  t.textContent = `${new Date(e.at).toLocaleTimeString()} f${e.frame}`;
  li.append(t, e.text);
  if ($('problems-only').checked && e.level === 'info') li.hidden = true;
  const log = $('log');
  const atBottom = log.scrollTop + log.clientHeight >= log.scrollHeight - 4;
  log.append(li);
  while (log.childElementCount > 1000) log.firstElementChild.remove();
  if (atBottom) log.scrollTop = log.scrollHeight;
}

$('problems-only').addEventListener('change', (ev) => {
  for (const li of $('log').children) li.hidden = ev.target.checked && li.dataset.level === 'info';
});

// ---- panels ------------------------------------------------------------------

function row(dl, label, value) {
  const dt = document.createElement('dt');
  const dd = document.createElement('dd');
  dt.textContent = label;
  dd.textContent = value;
  dl.append(dt, dd);
}

function slots(ol, list) {
  ol.replaceChildren(
    ...list
      .filter((it) => it.id !== 0)
      .map((it) => {
        const li = document.createElement('li');
        li.textContent = `${itemName(it.id)}${it.qty > 1 ? ` x${it.qty}` : ''}`;
        return li;
      }),
  );
}

function renderPanels(s) {
  $('room').textContent = `ROOM ${s.label}`;
  $('screen').textContent = s.screen;
  $('camera').textContent = `cam ${s.camera}`;
  $('frame').textContent = `frame ${s.frame}`;
  $('god').checked = s.god;

  const p = s.player;
  const pct = p.maxHp > 0 ? Math.max(0, Math.min(100, (100 * p.hp) / p.maxHp)) : 0;
  $('hp-bar').style.width = `${pct}%`;
  $('hp-bar').style.background = pct > 66 ? 'var(--ok)' : pct > 33 ? 'var(--warn)' : 'var(--bad)';
  $('hp-text').textContent = `${p.hp} / ${p.maxHp}`;
  const dl = $('player');
  dl.replaceChildren();
  row(dl, 'position', `${u16(p.x)}, ${p.y}, ${u16(p.z)}`);
  row(dl, 'angle', `${((p.angle % 4096) + 4096) % 4096}`);
  // g_EquippedItemId is the bag slot, counted from one, not an item id.
  const held = s.items[p.weapon - 1];
  row(dl, 'weapon', p.weapon ? `slot ${p.weapon}: ${held ? itemName(held.id) : '?'}` : 'none');
  row(dl, 'character', `id ${p.id}, model ${s.charModel}`);
  row(dl, 'collision flags', `0x${hex(p.cf)}`);
  row(dl, 'msf', `0x${hex(s.msf)} / 0x${hex(s.msf2)}`);
  row(dl, 'message', s.messageId >= 0 ? `${s.messageId} (choice ${s.messageChoice})` : 'none');

  $('enemies').tBodies[0].replaceChildren(
    ...s.enemies.map((e, i) => {
      const tr = document.createElement('tr');
      if (e.hp <= 0) tr.className = 'down';
      for (const v of [i, hex(e.type), hex(e.status), e.hp, u16(e.x), u16(e.z)]) {
        const td = document.createElement('td');
        td.textContent = v;
        tr.append(td);
      }
      return tr;
    }),
  );

  slots($('items'), s.items);
  slots($('box'), s.box);

  $('bgm').replaceChildren(
    ...(s.bgm?.channels ?? [])
      .filter((c) => c.file)
      .map((c) => {
        const li = document.createElement('li');
        li.textContent = `${c.file}${c.playing ? ' (playing)' : ''}`;
        return li;
      }),
  );

  // Flag banks: a bank that changed since the last state is highlighted.
  $('banks').replaceChildren(
    ...s.banks.map((b, i) => {
      const div = document.createElement('div');
      div.textContent = `${i}: ${b}`;
      if (prevBanks[i] !== undefined && prevBanks[i] !== b) div.className = 'changed';
      return div;
    }),
  );
  prevBanks = s.banks;
}

// ---- map ---------------------------------------------------------------------

const canvas = $('map');
const ctx = canvas.getContext('2d');

async function loadMap(s) {
  const key = `${s.stage}:${s.room}:${s.player.cf}`;
  if (key === mapKey) return;
  mapKey = key;
  map = null;
  trail.length = 0;
  const r = await fetch(`/room?stage=${s.stage}&room=${s.room}&cf=${s.player.cf}`);
  const body = await r.json();
  if (mapKey !== key) return;
  $('map-error').textContent = r.ok ? '' : body.error;
  map = r.ok ? body : null;
  area = -1;
  if (map) {
    map.floor.byRow = new Map();
    for (const run of map.floor.runs) {
      if (!map.floor.byRow.has(run[1])) map.floor.byRow.set(run[1], []);
      map.floor.byRow.get(run[1]).push(run);
    }
  }
  draw();
}

/** The floor area under (x, z), or -1 on a wall or off the grid. */
function areaAt(f, x, z) {
  const row = Math.floor((z - f.z0) / f.cell);
  const col = Math.floor((x - f.x0) / f.cell);
  const run = f.byRow.get(row)?.find((r) => col >= r[2] && col <= r[3]);
  return run ? run[0] : -1;
}

/** Frame the floor area she is in; with none known yet, the whole room. */
function bounds(m) {
  let x0 = Infinity, z0 = Infinity, x1 = -Infinity, z1 = -Infinity;
  const add = (x, z) => {
    x0 = Math.min(x0, x); x1 = Math.max(x1, x);
    z0 = Math.min(z0, z); z1 = Math.max(z1, z);
  };
  const a = m.floor.areas[area];
  if (a) {
    const margin = 1200;
    add(a.x0 - margin, a.z0 - margin);
    add(a.x1 + margin, a.z1 + margin);
  } else {
    for (const sh of m.shapes) { add(sh.xMin, sh.zMin); add(sh.xMax, sh.zMax); }
    for (const zn of m.zones) for (const [x, z] of zn.quad) add(x, z);
  }
  if (state) add(u16(state.player.x), u16(state.player.z));
  return { x0, z0, x1, z1 };
}

function draw() {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
    canvas.width = w * dpr;
    canvas.height = h * dpr;
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  if (!map || !state) return;

  const here = areaAt(map.floor, u16(state.player.x), u16(state.player.z));
  if (here >= 0) area = here;
  const b = bounds(map);
  const pad = 24;
  const scale = Math.min((w - 2 * pad) / (b.x1 - b.x0 || 1), (h - 2 * pad) / (b.z1 - b.z0 || 1));
  const ox = (w - (b.x1 - b.x0) * scale) / 2;
  const oy = (h - (b.z1 - b.z0) * scale) / 2;
  const X = (x) => ox + (x - b.x0) * scale;
  const Y = (z) => h - oy - (z - b.z0) * scale;

  // Floor: where her centre can stand; the area she is in brighter.
  const f = map.floor;
  for (const [id, row, c0, c1] of f.runs) {
    ctx.fillStyle = id === area ? '#1d2a33' : '#141a20';
    const x = f.x0 + c0 * f.cell, z = f.z0 + row * f.cell;
    ctx.fillRect(X(x), Y(z + f.cell), (c1 - c0 + 1) * f.cell * scale + 0.5, f.cell * scale + 0.5);
  }

  // Collision.
  ctx.fillStyle = '#3a4350';
  for (const sh of map.shapes) {
    if (sh.kind === 'circle') {
      ctx.beginPath();
      ctx.arc(X((sh.xMin + sh.xMax) / 2), Y((sh.zMin + sh.zMax) / 2), ((sh.xMax - sh.xMin) / 2) * scale, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.fillRect(X(sh.xMin), Y(sh.zMax), (sh.xMax - sh.xMin) * scale, (sh.zMax - sh.zMin) * scale);
    }
  }

  // Switch zones: the current camera's bright and labelled, the rest faint.
  ctx.font = '11px ui-monospace, monospace';
  for (const zn of map.zones) {
    const live = zn.from === state.camera;
    ctx.beginPath();
    zn.quad.forEach(([x, z], i) => (i ? ctx.lineTo(X(x), Y(z)) : ctx.moveTo(X(x), Y(z))));
    ctx.closePath();
    ctx.strokeStyle = live ? '#6fb3ff' : 'rgba(111,179,255,0.12)';
    ctx.lineWidth = live ? 1.5 : 1;
    if (live) {
      ctx.fillStyle = 'rgba(111,179,255,0.08)';
      ctx.fill();
    }
    ctx.stroke();
    if (live) {
      const cx = zn.quad.reduce((a, [x]) => a + x, 0) / 4;
      const cz = zn.quad.reduce((a, [, z]) => a + z, 0) / 4;
      ctx.fillStyle = '#6fb3ff';
      ctx.fillText(`-> cam ${zn.to}`, X(cx) - 22, Y(cz) + 4);
    }
  }

  // Cameras: eye and a line towards the target; the live one in yellow.
  map.cameras.forEach((c, i) => {
    const live = i === state.camera;
    const ex = X(u16(c.x)), ey = Y(u16(c.z));
    const len = Math.hypot(c.targetX - c.x, c.targetZ - c.z) || 1;
    const reach = Math.min(len, 2500) / len;
    ctx.strokeStyle = live ? '#e7b84b' : 'rgba(231,184,75,0.25)';
    ctx.lineWidth = live ? 2 : 1;
    ctx.beginPath();
    ctx.moveTo(ex, ey);
    ctx.lineTo(X(u16(c.x) + (c.targetX - c.x) * reach), Y(u16(c.z) + (c.targetZ - c.z) * reach));
    ctx.stroke();
    ctx.fillStyle = live ? '#e7b84b' : 'rgba(231,184,75,0.4)';
    ctx.beginPath();
    ctx.arc(ex, ey, live ? 5 : 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillText(String(i), ex + 6, ey - 6);
  });

  // Trail.
  ctx.strokeStyle = '#2f7d5a';
  ctx.lineWidth = 2;
  ctx.beginPath();
  trail.forEach(([x, z], i) => (i ? ctx.lineTo(X(x), Y(z)) : ctx.moveTo(X(x), Y(z))));
  ctx.stroke();

  // Enemies.
  for (const e of state.enemies) {
    const down = e.hp <= 0;
    ctx.fillStyle = down ? '#5b3a3a' : '#ef6461';
    ctx.beginPath();
    ctx.arc(X(u16(e.x)), Y(u16(e.z)), 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#d7dce2';
    ctx.fillText(`${hex(e.type)} ${e.hp}`, X(u16(e.x)) + 9, Y(u16(e.z)) + 4);
  }

  // Player: an arrow along (cos a, -sin a) in X/Z, which is (cos a, sin a) on screen with Z up.
  const p = state.player;
  const a = (p.angle * 2 * Math.PI) / 4096;
  const px = X(u16(p.x)), py = Y(u16(p.z));
  const dx = Math.cos(a), dy = Math.sin(a);
  ctx.fillStyle = '#4fc38a';
  ctx.beginPath();
  ctx.moveTo(px + dx * 14, py + dy * 14);
  ctx.lineTo(px - dx * 7 - dy * 7, py - dy * 7 + dx * 7);
  ctx.lineTo(px - dx * 7 + dy * 7, py - dy * 7 - dx * 7);
  ctx.closePath();
  ctx.fill();
}

window.addEventListener('resize', draw);
$('clear-trail').addEventListener('click', () => {
  trail.length = 0;
  draw();
});

// ---- stream ------------------------------------------------------------------

function onState(s) {
  state = s;
  renderPanels(s);
  if (s.play) {
    const last = trail.at(-1);
    const x = u16(s.player.x), z = u16(s.player.z);
    if (!last || Math.hypot(last[0] - x, last[1] - z) > 60) trail.push([x, z]);
    if (trail.length > 5000) trail.splice(0, 1000);
  }
  loadMap(s);
  draw();
}

function setLink(on) {
  $('link').classList.toggle('on', on);
  if (!on) $('room').textContent = 'waiting for the game';
}

const events = new EventSource('/events');
events.addEventListener('hello', (ev) => {
  const hello = JSON.parse(ev.data);
  items = hello.items;
  $('log').replaceChildren();
  hello.log.forEach(addLog);
  setLink(hello.connected);
  $('keyboard').checked = hello.keyboard;
  if (hello.state) onState(hello.state);
});
events.addEventListener('state', (ev) => onState(JSON.parse(ev.data)));
events.addEventListener('log', (ev) => addLog(JSON.parse(ev.data)));
events.addEventListener('link', (ev) => setLink(JSON.parse(ev.data).connected));
events.onerror = () => setLink(false);

$('god').addEventListener('change', (ev) => send(`god ${ev.target.checked ? 1 : 0}`));
$('keyboard').addEventListener('change', (ev) => send(`keyboard ${ev.target.checked ? 1 : 0}`));
$('cmd').addEventListener('submit', (ev) => {
  ev.preventDefault();
  const line = $('cmd-line').value.trim();
  if (line) send(line);
  $('cmd-line').value = '';
});
