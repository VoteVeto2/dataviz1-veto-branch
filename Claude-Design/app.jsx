/* App: The Committee — sentiment constellation + trip ribbon */
const { useState, useMemo, useEffect, useRef } = React;

const D = window.DATA;

// === helpers ===
const TOPIC_ORDER = [
  "affordable_housing","new_crane_lomark","low_volume_crane","fish_vacuum","deep_fishing_dock",
  "waterfront_market","seafood_festival","heritage_walking_tour","expanding_tourist_wharf",
  "marine_life_deck","concert",
  "renaming_park_himark","name_harbor_area","name_inspection_office","statue_john_smoth"
];

// classify topics into clusters for arc grouping
const TOPIC_CLUSTER = {
  affordable_housing: "Workers",
  new_crane_lomark: "Industry",
  low_volume_crane: "Industry",
  fish_vacuum: "Industry",
  deep_fishing_dock: "Industry",
  waterfront_market: "Tourism",
  seafood_festival: "Tourism",
  heritage_walking_tour: "Tourism",
  expanding_tourist_wharf: "Tourism",
  marine_life_deck: "Tourism",
  concert: "Tourism",
  renaming_park_himark: "Civic",
  name_harbor_area: "Civic",
  name_inspection_office: "Civic",
  statue_john_smoth: "Civic"
};
const CLUSTER_ORDER = ["Workers","Industry","Tourism","Civic"];

const PEOPLE = D.people;
const TOPICS = D.topics
  .filter(t => TOPIC_ORDER.includes(t.id))
  .sort((a,b) => TOPIC_ORDER.indexOf(a.id) - TOPIC_ORDER.indexOf(b.id));

// short labels
const SHORT_LABEL = {
  affordable_housing: "Affordable Housing",
  new_crane_lomark: "New Crane (Lomark)",
  low_volume_crane: "Low-Volume Crane",
  fish_vacuum: "Fish Vacuum",
  deep_fishing_dock: "Deep-Maintenance Dock",
  waterfront_market: "Waterfront Market",
  seafood_festival: "Seafood Festival",
  heritage_walking_tour: "Heritage Walking Tour",
  expanding_tourist_wharf: "Tourist Wharf",
  marine_life_deck: "Marine Life Deck",
  concert: "Summer Concert",
  renaming_park_himark: "Rename Park (Himark)",
  name_harbor_area: "Name Harbor (Port Grove)",
  name_inspection_office: "Name Inspection Office",
  statue_john_smoth: "Statue of John Smoth"
};

// sentiment to color
function sentimentColor(s) {
  // s ∈ [-1, 1]
  if (s == null) return "var(--neutral)";
  // pos green, neg red, mid neutral
  const t = (s + 1) / 2; // 0..1
  // interpolate 3-stop: red -> straw -> green using oklch
  // L 0.65->0.78, C 0.18->0.14, H 25->150
  const L = 0.62 + t * 0.18;
  const C = 0.08 + Math.abs(s) * 0.14;
  const H = s < 0 ? 25 : 150;
  return `oklch(${L.toFixed(3)} ${C.toFixed(3)} ${H})`;
}

function strokeWidth(s) {
  return 0.6 + Math.abs(s) * 3.0;
}

// sentiment vector helpers
function vecFor(personId) {
  const v = D.sentimentMatrix[personId] || {};
  return TOPICS.map(t => v[t.id] ?? null);
}
function cosineLike(a, b) {
  // pearson-like over shared topics
  let n = 0, sa = 0, sb = 0, ssa = 0, ssb = 0, sab = 0;
  for (let i = 0; i < a.length; i++) {
    if (a[i] == null || b[i] == null) continue;
    n++;
    sa += a[i]; sb += b[i];
    ssa += a[i]*a[i]; ssb += b[i]*b[i];
    sab += a[i]*b[i];
  }
  if (n < 2) return null;
  const denom = Math.sqrt((ssa - sa*sa/n) * (ssb - sb*sb/n));
  if (denom < 1e-9) return null;
  return (sab - sa*sb/n) / denom;
}

// === Constellation ===
function Constellation({ hovered, setHovered, selected, setSelected, mode }) {
  const W = 1100, H = 700;
  const cx = W/2, cy = H/2 + 6;

  // person positions: small inner ring on the LEFT 1/3
  const personR = 92;
  const personCx = 320, personCy = cy;
  const personPos = useMemo(() => {
    const N = PEOPLE.length;
    return PEOPLE.map((p, i) => {
      const a = -Math.PI/2 + (i / N) * Math.PI * 2;
      return {
        id: p.id, name: p.name, role: p.role,
        x: personCx + Math.cos(a) * personR,
        y: personCy + Math.sin(a) * personR,
        a
      };
    });
  }, []);

  // topic positions: big arc on the right
  const topicPos = useMemo(() => {
    if (mode === "arc") {
      // grouped vertical columns on right
      const startX = 760, gap = 22;
      const groups = CLUSTER_ORDER.map(c => TOPICS.filter(t => TOPIC_CLUSTER[t.id] === c));
      const out = [];
      let y = 80;
      groups.forEach((grp, gi) => {
        if (gi > 0) y += 32;
        out.push({ kind:"clusterLabel", cluster: CLUSTER_ORDER[gi], x: startX, y: y - 16 });
        grp.forEach((t, i) => {
          out.push({
            id: t.id, x: startX, y, cluster: CLUSTER_ORDER[gi]
          });
          y += gap;
        });
      });
      return out;
    }
    // arc mode: big right-side arc centered on personCx
    const arcStart = -Math.PI*0.55, arcEnd = Math.PI*0.55;
    const R = 335;
    const N = TOPICS.length;
    return TOPICS.map((t, i) => {
      const a = arcStart + (i / (N - 1)) * (arcEnd - arcStart);
      return {
        id: t.id,
        x: personCx + Math.cos(a) * R,
        y: personCy + Math.sin(a) * R,
        a,
        cluster: TOPIC_CLUSTER[t.id]
      };
    });
  }, [mode]);

  // edges
  const edges = useMemo(() => {
    const out = [];
    for (const p of personPos) {
      const sm = D.sentimentMatrix[p.id] || {};
      for (const t of (mode === "columns" ? topicPos.filter(x => !x.kind) : topicPos)) {
        if (sm[t.id] === undefined) continue;
        const s = sm[t.id];
        out.push({
          personId: p.id, topicId: t.id, s,
          x1: p.x, y1: p.y, x2: t.x, y2: t.y
        });
      }
    }
    return out;
  }, [personPos, topicPos, mode]);

  function isEdgeHighlighted(e) {
    if (selected) {
      if (selected.kind === "person") return e.personId === selected.id;
      if (selected.kind === "topic") return e.topicId === selected.id;
    }
    if (hovered) {
      if (hovered.kind === "person") return e.personId === hovered.id;
      if (hovered.kind === "topic") return e.topicId === hovered.id;
    }
    return null; // null = no focus → edges hidden by default
  }

  function dim(kind, id) {
    const s = selected || hovered;
    if (!s) return false;
    if (s.kind === kind) return s.id !== id;
    if (kind === "person" && s.kind === "topic") {
      const sm = D.sentimentMatrix[id] || {};
      return sm[s.id] === undefined;
    }
    if (kind === "topic" && s.kind === "person") {
      const sm = D.sentimentMatrix[s.id] || {};
      return sm[id] === undefined;
    }
    return false;
  }

  return (
    <svg className="constellation" viewBox={`0 0 ${W} ${H}`}>
      {/* faint guide rings around people */}
      <circle className="ring" cx={personCx} cy={personCy} r={personR + 60} />
      <circle className="ring" cx={personCx} cy={personCy} r={personR + 160} />

      {/* edges */}
      <g>
        {edges.map((e, i) => {
          const hl = isEdgeHighlighted(e);
          const isDim = hl === false || hl === null;
          // Default state: no edges shown. Only on hover/select do related edges appear.
          const opacity = hl === true ? 0.92 : 0;
          const w = strokeWidth(e.s) * (hl ? 1.25 : 1);
          // curved path for elegance
          const mx = (e.x1 + e.x2) / 2;
          const my = (e.y1 + e.y2) / 2;
          // slight outward bend
          const dx = e.x2 - e.x1, dy = e.y2 - e.y1;
          const nx = -dy, ny = dx;
          const len = Math.hypot(nx, ny) || 1;
          const bend = 18;
          const ctrlX = mx + (nx/len) * bend;
          const ctrlY = my + (ny/len) * bend;
          return (
            <path
              key={i}
              className={`edge ${isDim ? 'dim' : ''}`}
              d={`M ${e.x1} ${e.y1} Q ${ctrlX} ${ctrlY} ${e.x2} ${e.y2}`}
              stroke={sentimentColor(e.s)}
              strokeWidth={w}
              opacity={opacity}
            />
          );
        })}
      </g>

      {/* topic nodes / cluster labels */}
      <g>
        {topicPos.map((tp, i) => {
          if (tp.kind === "clusterLabel") {
            return (
              <text key={`cl-${i}`} x={tp.x - 14} y={tp.y}
                className="ring-label" textAnchor="start">
                — {tp.cluster}
              </text>
            );
          }
          const t = TOPICS.find(x => x.id === tp.id);
          const isHover = hovered && hovered.kind === "topic" && hovered.id === tp.id;
          const isSel = selected && selected.kind === "topic" && selected.id === tp.id;
          const cls = `node-topic ${isSel || isHover ? 'active' : ''} ${dim('topic', tp.id) ? 'dim' : ''}`;
          // anchor: arc mode → outward; columns mode → left of dot
          const labelAnchor = mode === "arc" ? "start" : "start";
          const labelDx = mode === "arc"
            ? Math.cos(tp.a) >= 0 ? 14 : -14
            : 14;
          const finalAnchor = mode === "arc"
            ? (Math.cos(tp.a) >= 0 ? "start" : "end")
            : "start";
          return (
            <g key={tp.id} className={cls}
               onMouseEnter={() => setHovered({ kind: "topic", id: tp.id })}
               onMouseLeave={() => setHovered(null)}
               onClick={() => setSelected(s =>
                 s && s.kind === "topic" && s.id === tp.id ? null : { kind:"topic", id: tp.id }
               )}>
              <circle cx={tp.x} cy={tp.y} r={isHover || isSel ? 6 : 3.5} />
              <text x={tp.x + labelDx} y={tp.y + 4} textAnchor={finalAnchor}>
                {SHORT_LABEL[tp.id] || t.short}
              </text>
            </g>
          );
        })}
      </g>

      {/* people nodes */}
      <g>
        {personPos.map((p, i) => {
          const isHover = hovered && hovered.kind === "person" && hovered.id === p.id;
          const isSel = selected && selected.kind === "person" && selected.id === p.id;
          const cls = `node-person ${isSel || isHover ? 'active' : ''} ${dim('person', p.id) ? 'dim' : ''}`;
          // count opinions
          const sm = D.sentimentMatrix[p.id] || {};
          const opinionCount = Object.keys(sm).length;
          // label outward from center of person ring
          const lx = p.x + Math.cos(p.a) * 26;
          const ly = p.y + Math.sin(p.a) * 26;
          const anchor = Math.cos(p.a) >= 0 ? "start" : "end";
          return (
            <g key={p.id} className={cls}
               onMouseEnter={() => setHovered({ kind: "person", id: p.id })}
               onMouseLeave={() => setHovered(null)}
               onClick={() => setSelected(s =>
                 s && s.kind === "person" && s.id === p.id ? null : { kind:"person", id: p.id }
               )}>
              <circle className="halo" cx={p.x} cy={p.y} r={18 + opinionCount * 1.2} />
              <circle className="dot" cx={p.x} cy={p.y} r={isHover || isSel ? 8 : 5} />
              <text className="name" x={lx} y={ly - 2} textAnchor={anchor}>{p.name}</text>
              <text className="role" x={lx} y={ly + 11} textAnchor={anchor}>{p.role}</text>
            </g>
          );
        })}
      </g>

    </svg>
  );
}

// === Right rail ===
function Rail({ hovered, selected, setSelected }) {
  const focus = selected || hovered;
  if (!focus) {
    return (
      <aside className="rail">
        <p className="sub">Briefing</p>
        <h2 className="hint">
          A volunteer committee of six debated fifteen town matters across sixteen
          meetings. Hover the constellation to see who agrees with whom — click
          to pin a person or a topic.
        </h2>
        <RailLegend />
        <RailGlobal />
      </aside>
    );
  }
  if (focus.kind === "person") return <PersonPanel id={focus.id} setSelected={setSelected} />;
  return <TopicPanel id={focus.id} setSelected={setSelected} />;
}

function RailLegend() {
  return (
    <div>
      <p className="sub">How to read</p>
      <div style={{display:"flex", flexDirection:"column", gap:10, fontSize:13, color:"var(--ink-2)", lineHeight:1.5}}>
        <div><span style={{color:"var(--ink)"}}>Line color</span> shows sentiment from <span style={{color:"oklch(0.65 0.18 25)"}}>opposed</span> through <span style={{color:"var(--ink-3)"}}>neutral</span> to <span style={{color:"oklch(0.78 0.14 150)"}}>in favor</span>.</div>
        <div><span style={{color:"var(--ink)"}}>Line weight</span> shows conviction.</div>
        <div><span style={{color:"var(--ink)"}}>Halo size</span> on each member shows how many topics they've weighed in on.</div>
      </div>
    </div>
  );
}

function RailGlobal() {
  // global stats
  const totalOpinions = useMemo(() =>
    Object.values(D.sentimentMatrix).reduce((s,v) => s + Object.keys(v).length, 0), []);
  const totalTrips = D.trips.length;
  const totalDiscussions = Object.values(D.discussionsByTopic).reduce((s, ds) => s + ds.length, 0);

  return (
    <div>
      <p className="sub">By the numbers</p>
      <div className="stat-row">
        <div className="stat"><div className="num">{PEOPLE.length}</div><div className="lbl">Members</div></div>
        <div className="stat"><div className="num">{TOPICS.length}</div><div className="lbl">Topics</div></div>
        <div className="stat"><div className="num">{totalOpinions}</div><div className="lbl">Opinions</div></div>
        <div className="stat"><div className="num">{totalTrips}</div><div className="lbl">Field trips</div></div>
        <div className="stat"><div className="num">{totalDiscussions}</div><div className="lbl">Discussions</div></div>
        <div className="stat"><div className="num">16</div><div className="lbl">Meetings</div></div>
      </div>
    </div>
  );
}

function PersonPanel({ id, setSelected }) {
  const p = PEOPLE.find(x => x.id === id);
  const sm = D.sentimentMatrix[id] || {};
  const opinions = Object.entries(sm).sort((a,b) => b[1] - a[1]);
  const tripCount = D.trips.filter(t => t.traveler === id).length;
  const meanS = opinions.length ? opinions.reduce((s,[,v]) => s+v, 0) / opinions.length : 0;

  // compatibility with others
  const me = vecFor(id);
  const compat = PEOPLE.filter(o => o.id !== id).map(o => ({
    name: o.name, v: cosineLike(me, vecFor(o.id))
  })).filter(x => x.v != null).sort((a,b) => b.v - a.v);

  // top opinion: pick highest-magnitude with reason
  const flagshipKey = opinions
    .map(([k,v]) => ({ k, v, mag: Math.abs(v) }))
    .sort((a,b) => b.mag - a.mag)[0];
  const flagshipReasonArr = flagshipKey ? D.reasonByPersonTopic[`${id}|${flagshipKey.k}`] || [] : [];
  const flagshipReason = flagshipReasonArr[0];

  return (
    <aside className="rail">
      <div>
        <p className="sub">Member · {p.role}</p>
        <h2 style={{fontSize:34, lineHeight:1}}>{p.name}</h2>
      </div>

      <div className="stat-row">
        <div className="stat"><div className="num">{opinions.length}</div><div className="lbl">Opinions</div></div>
        <div className="stat"><div className="num">{tripCount}</div><div className="lbl">Field trips</div></div>
        <div className="stat"><div className="num" style={{color: sentimentColor(meanS)}}>{meanS.toFixed(2)}</div><div className="lbl">Avg sentiment</div></div>
        <div className="stat"><div className="num">{opinions.filter(([,v]) => v > 0).length}/{opinions.filter(([,v]) => v < 0).length}</div><div className="lbl">Pro / Against</div></div>
      </div>

      {flagshipReason && (
        <div>
          <p className="sub">On {SHORT_LABEL[flagshipKey.k]}</p>
          <div className="reason">{flagshipReason}</div>
        </div>
      )}

      <div>
        <p className="sub">Stance, ranked</p>
        <div className="opinions">
          {opinions.map(([k,v]) => (
            <div key={k} className="opinion-row" onClick={() => setSelected({kind:"topic", id:k})}>
              <span className="swatch" style={{background: sentimentColor(v)}}></span>
              <span className="label">{SHORT_LABEL[k] || k}</span>
              <span className="val">{v >= 0 ? "+" : ""}{v.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>

      <div>
        <p className="sub">Aligned with</p>
        <div className="compat">
          {compat.map(c => (
            <div key={c.name} className="compat-row">
              <span className="name">{c.name}</span>
              <span className="bar"><span className="fill" style={{
                width: `${(c.v + 1) * 50}%`,
                background: c.v >= 0
                  ? "linear-gradient(90deg, var(--neutral), var(--pos))"
                  : "linear-gradient(90deg, var(--neg), var(--neutral))"
              }}></span></span>
              <span className="v">{c.v >= 0 ? "+" : ""}{c.v.toFixed(2)}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}

function TopicPanel({ id, setSelected }) {
  const t = TOPICS.find(x => x.id === id);
  const opinions = PEOPLE.map(p => ({
    p, v: D.sentimentMatrix[p.id]?.[id]
  })).filter(o => o.v !== undefined).sort((a,b) => b.v - a.v);

  const meanS = opinions.length ? opinions.reduce((s,o)=>s+o.v,0)/opinions.length : 0;
  const trav = D.discussionsByTopic[id] || [];
  const meetings = new Set(trav.map(d => d.meeting).filter(Boolean));
  const industries = (t.industries || "[]").replace(/[\[\]']/g,'').split(',').map(s=>s.trim()).filter(Boolean);

  // a top reason
  let topReason = null;
  for (const o of opinions) {
    const k = `${o.p.id}|${id}`;
    const arr = D.reasonByPersonTopic[k];
    if (arr && arr.length) { topReason = { who: o.p.name, sent: o.v, txt: arr[0] }; break; }
  }

  return (
    <aside className="rail">
      <div>
        <p className="sub">Topic · {TOPIC_CLUSTER[id]}</p>
        <h2>{t.long}</h2>
      </div>

      <div className="stat-row">
        <div className="stat"><div className="num">{opinions.length}</div><div className="lbl">Voices</div></div>
        <div className="stat"><div className="num">{meetings.size}</div><div className="lbl">Meetings</div></div>
        <div className="stat"><div className="num" style={{color: sentimentColor(meanS)}}>{meanS >=0 ? "+" : ""}{meanS.toFixed(2)}</div><div className="lbl">Avg sentiment</div></div>
        <div className="stat"><div className="num">{trav.length}</div><div className="lbl">Discussions</div></div>
      </div>

      {industries.length > 0 && (
        <div>
          <p className="sub">Industries involved</p>
          <div style={{display:"flex", gap:8, flexWrap:"wrap"}}>
            {industries.map(i => (
              <span key={i} style={{
                fontFamily:"var(--mono)", fontSize:10, letterSpacing:"0.14em",
                textTransform:"uppercase", padding:"4px 8px",
                border:"1px solid var(--line-2)", borderRadius:999, color:"var(--ink-2)"
              }}>{i}</span>
            ))}
          </div>
        </div>
      )}

      {topReason && (
        <div>
          <p className="sub">{topReason.who} · {topReason.sent >= 0 ? "+" : ""}{topReason.sent.toFixed(2)}</p>
          <div className="reason" style={{
            borderLeftColor: sentimentColor(topReason.sent)
          }}>{topReason.txt}</div>
        </div>
      )}

      <div>
        <p className="sub">Where the committee stands</p>
        <div className="opinions">
          {opinions.map(o => (
            <div key={o.p.id} className="opinion-row" onClick={() => setSelected({kind:"person", id:o.p.id})}>
              <span className="swatch" style={{background: sentimentColor(o.v)}}></span>
              <span className="label">{o.p.name} <span style={{color:"var(--ink-4)"}}>· {o.p.role}</span></span>
              <span className="val">{o.v >= 0 ? "+" : ""}{o.v.toFixed(2)}</span>
            </div>
          ))}
          {opinions.length < PEOPLE.length && (
            <div style={{fontSize:11, color:"var(--ink-4)", fontFamily:"var(--mono)", letterSpacing:"0.1em", textTransform:"uppercase", marginTop:6}}>
              {PEOPLE.length - opinions.length} member{PEOPLE.length - opinions.length === 1 ? "" : "s"} silent
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}

// === Trip ribbon ===
function TripRibbon({ selected, setSelected, hovered, setHovered }) {
  const W = 1500, laneH = 28, leftPad = 130, rightPad = 30, topPad = 30;
  const H = topPad + laneH * PEOPLE.length + 30;

  const trips = D.trips.filter(t => t.date && PEOPLE.find(p => p.id === t.traveler));
  const dates = trips.map(t => +new Date(t.date));
  const dMin = +new Date("2040-03-25");
  const dMax = +new Date("2040-08-05");
  const xFor = (date) => leftPad + ((+new Date(date) - dMin) / (dMax - dMin)) * (W - leftPad - rightPad);

  // lane index — sort by trip count desc for visual rhythm
  const peopleOrdered = useMemo(() => {
    const counts = Object.fromEntries(PEOPLE.map(p => [p.id, trips.filter(t => t.traveler === p.id).length]));
    return [...PEOPLE].sort((a,b) => counts[b.id] - counts[a.id]);
  }, []);
  const laneFor = (pid) => topPad + peopleOrdered.findIndex(p => p.id === pid) * laneH + laneH/2;

  // month ticks
  const months = [];
  for (let m = 3; m <= 8; m++) {
    const d = new Date(`2040-${String(m).padStart(2,'0')}-01`);
    months.push({
      d, x: xFor(d),
      label: d.toLocaleDateString('en-US', { month: 'short' })
    });
  }

  // active filter
  const activePerson = selected?.kind === "person" ? selected.id : (hovered?.kind === "person" ? hovered.id : null);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet">
      {/* lanes */}
      {peopleOrdered.map((p, i) => {
        const y = topPad + i * laneH + laneH/2;
        const dimmed = activePerson && activePerson !== p.id;
        return (
          <g key={p.id} opacity={dimmed ? 0.25 : 1}>
            <text className="lane-label" x={leftPad - 14} y={y + 4} textAnchor="end">{p.name}</text>
            <line className="lane-baseline" x1={leftPad} y1={y} x2={W - rightPad} y2={y} />
          </g>
        );
      })}

      {/* month ticks */}
      {months.map((m, i) => (
        <g key={i}>
          <line className="month-tick" x1={m.x} y1={topPad - 10} x2={m.x} y2={H - 14} />
          <text className="month-label" x={m.x + 4} y={H - 4}>{m.label} '40</text>
        </g>
      ))}

      {/* trip dots */}
      {trips.map((t, i) => {
        const y = laneFor(t.traveler);
        const x1 = xFor(t.date);
        // bar width: proportional to stops
        const w = Math.max(2.2, 1.2 + Math.min(t.stops, 12) * 0.7);
        const dimmed = activePerson && activePerson !== t.traveler;
        return (
          <circle
            key={`${t.id}-${i}`}
            className="trip-bar"
            cx={x1}
            cy={y}
            r={w}
            opacity={dimmed ? 0.12 : 0.85}
            onMouseEnter={(e) => setHovered({ kind: "trip", id: t.id, x: e.clientX, y: e.clientY })}
            onMouseMove={(e) => setHovered({ kind: "trip", id: t.id, x: e.clientX, y: e.clientY })}
            onMouseLeave={() => setHovered(null)}
            onClick={() => setSelected({ kind:"person", id: t.traveler })}
          />
        );
      })}
    </svg>
  );
}

function TripTooltip({ hovered }) {
  if (!hovered || hovered.kind !== "trip") return null;
  const t = D.trips.find(x => x.id === hovered.id);
  if (!t) return null;
  return (
    <div className="tooltip" style={{ left: hovered.x + 16, top: hovered.y + 16 }}>
      <div className="tt-h">{t.traveler}</div>
      <div className="tt-m">{t.date} · {t.start}–{t.end} · {t.stops} stop{t.stops === 1 ? "" : "s"}</div>
      <div style={{marginTop:6, fontSize:12, color:"var(--ink-2)"}}>
        {t.places.slice(0,5).join(" → ")}{t.places.length > 5 ? ` +${t.places.length - 5} more` : ""}
      </div>
    </div>
  );
}

// === App ===
function App() {
  const [hovered, setHovered] = useState(null);
  const [selected, setSelected] = useState(null);
  const [mode, setMode] = useState("arc"); // arc | columns

  // tweaks integration (very lightweight)
  useEffect(() => {
    const handler = (ev) => {
      const m = ev.data;
      if (!m || typeof m !== 'object') return;
      if (m.type === '__activate_edit_mode') window.__tweaksOn?.(true);
      if (m.type === '__deactivate_edit_mode') window.__tweaksOn?.(false);
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  return (
    <div className="shell">
      <header className="masthead">
        <div>
          <div className="eyebrow">Oceanus Council · Field Notebook · Q2 2040</div>
          <h1 className="title">The Committee, <em>charted.</em></h1>
          <p className="dek">
            Six volunteers, fifteen town matters, ninety-nine recorded opinions and
            five hundred and thirty-six field trips. A constellation of who said
            what, and who actually went there to look.
          </p>
        </div>
        <div className="masthead-meta">
          <div><b>Source</b> · committee minutes</div>
          <div><b>Period</b> · 2040-03-31 → 2040-07-29</div>
          <div><b>Hover</b> a member or topic</div>
        </div>
      </header>

      <main className="stage">
        <div className="legend">
          <div className="row">
            <span>Sentiment</span>
            <span className="ramp"></span>
          </div>
          <div className="marks" style={{marginLeft:78}}>
            <span>opposed</span><span>neutral</span><span>in favor</span>
          </div>
        </div>

        <div className="mode-toggle" role="tablist">
          <button className={mode === "arc" ? "on" : ""} onClick={() => setMode("arc")}>Constellation</button>
          <button className={mode === "columns" ? "on" : ""} onClick={() => setMode("columns")}>Cluster</button>
        </div>

        <Constellation
          hovered={hovered} setHovered={setHovered}
          selected={selected} setSelected={setSelected}
          mode={mode}
        />
      </main>

      <Rail hovered={hovered} selected={selected} setSelected={setSelected} />

      <section className="ribbon">
        <div className="ribbon-head">
          <h3 className="h">Where they actually went.</h3>
          <span className="sub">536 field trips, Mar – Aug 2040 · dot size = stops on trip · click a dot to focus the traveler</span>
        </div>
        <TripRibbon
          selected={selected} setSelected={setSelected}
          hovered={hovered} setHovered={setHovered}
        />
      </section>

      <footer className="colophon">
        <span>Visualised from 26 source tables</span>
        <span>Click any node to pin · click again to release</span>
        <span>Press <b style={{color:"var(--ink-2)"}}>esc</b> to clear focus</span>
      </footer>

      <TripTooltip hovered={hovered} />
    </div>
  );
}

// esc to clear
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    window.__clearFocus?.();
  }
});

const root = ReactDOM.createRoot(document.getElementById('app'));
function Mount() {
  // wrap App to expose clearFocus
  const ref = useRef();
  return <App />;
}
root.render(<App />);
