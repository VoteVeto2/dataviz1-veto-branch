"""Builder module for Dashboard 1 – Board Sentiment Bias Map.

Produces a self-contained HTML string (SVG + CSS + JS) suitable for
embedding in a marimo ``mo.iframe()`` call.  This module does **not**
import marimo; it is a pure-Python helper.
"""

import json
import math
import re
from collections import Counter, defaultdict

import pandas as pd
import svg


# ── custom svg.py subclasses for data-* attributes ─────────────────────────

class _DataRect(svg.Rect):
    def __init__(self, data_fill, data_people="", data_topic="", **kwargs):
        self._data_fill = data_fill
        self._data_people = data_people
        self._data_topic = data_topic
        super().__init__(**kwargs)

    def as_str(self):
        s = super().as_str()
        s = re.sub(r'\s-data-[a-z_]+="[^"]*"', '', s)
        attrs = (
            f' data-fill="{self._data_fill}"'
            f' data-people="{self._data_people}"'
            f' data-topic="{self._data_topic}"'
        )
        return s.replace("/>", f'{attrs}/>', 1)


class _DataPolygon(svg.Polygon):
    def __init__(self, data_fill, data_people="", data_topic="", **kwargs):
        self._data_fill = data_fill
        self._data_people = data_people
        self._data_topic = data_topic
        super().__init__(**kwargs)

    def as_str(self):
        s = super().as_str()
        s = re.sub(r'\s-data-[a-z_]+="[^"]*"', '', s)
        attrs = (
            f' data-fill="{self._data_fill}"'
            f' data-people="{self._data_people}"'
            f' data-topic="{self._data_topic}"'
        )
        return s.replace("/>", f'{attrs}/>', 1)


class _DataG(svg.G):
    def __init__(self, data_targets="", data_topics="", data_pid="", **kwargs):
        self._data_targets = data_targets
        self._data_topics = data_topics
        self._data_pid = data_pid
        super().__init__(**kwargs)

    def as_str(self):
        s = super().as_str()
        s = re.sub(r'\s-data-[a-z_]+="[^"]*"', '', s)
        attrs = (
            f' data-targets="{self._data_targets}"'
            f' data-topics="{self._data_topics}"'
            f' data-pid="{self._data_pid}"'
        )
        return s.replace("<g ", f"<g{attrs} ", 1)


# ── colour / text helpers ──────────────────────────────────────────────────

def _interp(t, c0, c1):
    r, g, b = (int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))
    return f"rgb({r},{g},{b})"


def _color_for(s):
    t = min(abs(s), 1.0)
    return _interp(t, (255, 255, 255),
                   (46, 204, 113) if s >= 0 else (231, 76, 60))


def _text_ink(s):
    return "#111" if abs(s) < 0.55 else "white"


def _safe_id(s):
    return str(s).replace(" ", "_").replace(".", "_").replace("-", "_")


def _fmt_sent(val, prec=2):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "N/A"
    res = f"{val:+.{prec}f}"
    if prec == 1:
        return res.replace("+0.0", "0.0").replace("-0.0", "0.0")
    return res


# ── glyph builders ─────────────────────────────────────────────────────────

_SCALE = 1.3


def _person_glyph(px, py, fill, s=_SCALE):
    return svg.G(elements=[
        svg.Circle(cx=px, cy=py - 5 * s, r=3 * s,
                   fill=fill, stroke="#333", stroke_width=0.8),
        svg.Path(d=(f"M {px - 5 * s} {py + 7 * s} L {px - 5 * s} {py} "
                     f"A {5 * s} {4 * s} 0 0 1 {px + 5 * s} {py} "
                     f"L {px + 5 * s} {py + 7 * s} Z"),
                 fill=fill, stroke="#333", stroke_width=0.8),
    ])


def _king_crown(px, py):
    c = py - 12
    return svg.G(elements=[
        svg.Path(d=(f"M {px - 7} {c + 3} L {px - 7} {c - 1} L {px - 4} {c - 4} "
                     f"L {px - 2} {c - 1} L {px} {c - 6} L {px + 2} {c - 1} "
                     f"L {px + 4} {c - 4} L {px + 7} {c - 1} L {px + 7} {c + 3} Z"),
                 fill="#f1c40f", stroke="#8b6914", stroke_width=0.7),
        svg.Circle(cx=px - 4, cy=c - 4.5, r=0.8, fill="#e74c3c"),
        svg.Circle(cx=px, cy=c - 6.5, r=1.0, fill="#3498db"),
        svg.Circle(cx=px + 4, cy=c - 4.5, r=0.8, fill="#e74c3c"),
    ])


def _queen_crown(px, py):
    c = py - 12
    return svg.G(elements=[
        svg.Path(d=(f"M {px - 6} {c + 3} L {px - 6} {c} L {px - 4} {c - 3} "
                     f"L {px - 2} {c} L {px - 1} {c - 5} L {px + 1} {c - 5} "
                     f"L {px + 2} {c} L {px + 4} {c - 3} "
                     f"L {px + 6} {c} L {px + 6} {c + 3} Z"),
                 fill="#ecf0f1", stroke="#7f8c8d", stroke_width=0.7),
        svg.Circle(cx=px, cy=c - 5.5, r=1.0, fill="#9b59b6"),
    ])


def _chest(px, py):
    bx, by = px + 10, py + 3
    return svg.G(elements=[
        svg.Ellipse(cx=bx, cy=by, rx=5, ry=1.8,
                    fill="#a0522d", stroke="#333", stroke_width=0.5),
        svg.Rect(x=bx - 5, y=by, width=10, height=6,
                 fill="#8b4513", stroke="#333", stroke_width=0.5),
        svg.Rect(x=bx - 1, y=by + 1, width=2, height=2,
                 fill="#f1c40f", stroke="#333", stroke_width=0.3),
        svg.Circle(cx=bx - 1.5, cy=by - 1.5, r=1.0,
                   fill="#f1c40f", stroke="#333", stroke_width=0.3),
        svg.Circle(cx=bx + 1.5, cy=by - 1.5, r=0.8,
                   fill="#f1c40f", stroke="#333", stroke_width=0.3),
    ])


def _halo(px, py, has_crown):
    return svg.Ellipse(cx=px, cy=py - (18 if has_crown else 12),
                       rx=7, ry=2.0, fill="none",
                       stroke="#f1c40f", stroke_width=1.5)


def _devil_horns(px, py, s=_SCALE):
    head_cy = py - 5 * s
    head_top = head_cy - 3 * s
    return svg.G(elements=[
        svg.Path(d=f"M {px - 3} {head_top} L {px - 1.5} {head_top - 5} L {px - 0.5} {head_top} Z",
                 fill="#c0392b", stroke="#8b2820", stroke_width=0.4),
        svg.Path(d=f"M {px + 0.5} {head_top} L {px + 1.5} {head_top - 5} L {px + 3} {head_top} Z",
                 fill="#c0392b", stroke="#8b2820", stroke_width=0.4),
    ])


# ── CSS ─────────────────────────────────────────────────────────────────────

_CSS = """\
<style>
body {
   font-family: sans-serif;
   display: flex;
   justify-content: center;
   margin: 0;
   padding-top: 20px;
}
.glow-target {
   filter: drop-shadow(0 0 5px #e74c3c) drop-shadow(0 0 5px #e74c3c);
   stroke: #c0392b !important;
   stroke-width: 2.5px !important;
}
.glow-dishonest {
   filter: drop-shadow(0 0 5px #e74c3c);
}
.blur-out {
   opacity: 0.15 !important;
   filter: blur(1.5px);
}
[id^="person_"] {
   transition: opacity 0.3s, filter 0.3s;
}
#reason-panel {
   position: fixed; bottom: 8px; left: 50%; transform: translateX(-50%);
   max-width: 700px; max-height: 160px; overflow-y: auto;
   background: rgba(253,248,244,0.96); border: 1px solid #E8DDD4;
   border-radius: 8px; padding: 8px 12px; font-size: 11px;
   color: #3D3229; display: none; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
   z-index: 100;
}
#reason-panel .rp-title { font-weight: bold; margin-bottom: 4px; }
#reason-panel .rp-line { margin: 2px 0; line-height: 1.4; }
</style>
<div id="reason-panel"></div>
"""

# ── JS ──────────────────────────────────────────────────────────────────────

_JS = """\
<script>
(function initGraph() {
  const persons = document.querySelectorAll('[id^="person_"]');
  if (persons.length === 0) {
      setTimeout(initGraph, 50);
      return;
  }

  const reasonPanel = document.getElementById('reason-panel');

  function showReasons(pid, targets) {
    if (!reasonPanel || typeof REASONS === 'undefined') return;
    let lines = [];
    (targets || []).forEach(function(t) {
      const key = pid + '|' + t;
      if (REASONS[key]) {
        REASONS[key].forEach(function(r) { lines.push('<div class="rp-line">' + r.replace(/</g,'&lt;') + '</div>'); });
      }
    });
    if (lines.length > 0) {
      reasonPanel.innerHTML = '<div class="rp-title">Sentiment reasons for ' + pid + '</div>' + lines.join('');
      reasonPanel.style.display = 'block';
    }
  }
  function hideReasons() {
    if (reasonPanel && !lockedId) reasonPanel.style.display = 'none';
  }

  let lockedId = null;

  function resetAll() {
    if (lockedId) return;
    hideReasons();

    document.querySelectorAll('[id^="edge_"]').forEach(e => e.style.display = 'none');
    document.querySelectorAll('[id^="person_"]').forEach(p => {
        p.classList.remove('blur-out');
        p.setAttribute('opacity', '1');
    });
    const centre = document.getElementById('centre_group');
    if (centre) centre.classList.remove('blur-out');
    document.querySelectorAll('[id^="node_"]').forEach(n => {
      n.setAttribute('fill', n.getAttribute('data-fill'));
      n.setAttribute('opacity', '1');
      n.setAttribute('stroke', '#999');
      n.classList.remove('glow-target');
    });
    document.querySelectorAll('.person-label').forEach(l => l.style.display = '');

    document.querySelectorAll('.group-sent').forEach(el => {
      el.textContent = el.getAttribute('data-default') || el.textContent;
      el.setAttribute('fill', el.getAttribute('data-default-fill') || el.getAttribute('fill'));
    });

    document.querySelectorAll('.target-sent').forEach(el => {
      el.textContent = el.getAttribute('data-default') || el.textContent;
      el.style.display = '';
    });
  }

  function forceReset() {
      const oldLocked = lockedId;
      lockedId = null;
      resetAll();
      lockedId = oldLocked;
  }

  function showPersonHighlight(pid) {
      forceReset();
      const g = document.getElementById('person_' + pid);
      if (!g) return;
      const targetIds = (g.getAttribute('data-targets') || '').split(';').map(function(s) { return s.split(':')[0]; }).filter(Boolean);
      showReasons(pid, targetIds);

      document.querySelectorAll('[id^="person_"]').forEach(p => {
          if (p.id !== 'person_' + pid) p.classList.add('blur-out');
      });
      const centre = document.getElementById('centre_group');
      if (centre) centre.classList.add('blur-out');

      const targetStrs = (g.getAttribute('data-targets') || '').split(';').filter(Boolean);
      const topicStrs  = (g.getAttribute('data-topics') || '').split(';').filter(Boolean);

      const targetMap = {};
      targetStrs.forEach(pair => {
          const parts = pair.split(':');
          if (parts.length >= 4) targetMap[parts[0]] = { color: parts[1], text: parts[2], is_gov: parts[3] === '1' };
      });
      const topicMap = {};
      topicStrs.forEach(pair => {
          const parts = pair.split(':');
          if (parts.length >= 3) topicMap[parts[0]] = { color: parts[1], text: parts[2] };
      });

      document.querySelectorAll('.person-label').forEach(l => {
          if (l.id !== 'text_' + pid) l.style.display = 'none';
      });

      document.querySelectorAll('[id^="edge_"]').forEach(e => e.style.display = 'none');
      Object.keys(topicMap).forEach(stop => {
        const edge = document.getElementById('edge_' + pid + '_' + stop);
        if (edge) edge.style.display = '';
      });

      document.querySelectorAll('.group-sent').forEach(el => {
        const stid = el.id.replace('group_sent_', '');
        if (topicMap[stid]) {
            el.textContent = topicMap[stid].text;
            el.setAttribute('fill', topicMap[stid].color);
        } else {
            el.textContent = 'N/A';
            el.setAttribute('fill', '#bbb');
        }
      });

      document.querySelectorAll('[id^="node_"]').forEach(n => {
        const stid = n.id.replace('node_', '');
        if (targetMap[stid]) {
          n.setAttribute('fill', targetMap[stid].color);
          n.setAttribute('opacity', '1');
          n.setAttribute('stroke', '#333');
          if (!targetMap[stid].is_gov) n.classList.add('glow-target');
        } else {
          n.setAttribute('fill', '#ccc');
          n.setAttribute('opacity', '0.35');
          n.setAttribute('stroke', '#999');
        }
      });

      document.querySelectorAll('.target-sent').forEach(el => {
        const stid = el.id.replace('target_text_bg_', '').replace('target_text_fg_', '');
        if (targetMap[stid]) {
            el.textContent = targetMap[stid].text;
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
      });
  }

  function showNodeHighlight(node) {
      forceReset();
      const peopleIds = (node.getAttribute('data-people') || '').split(',').filter(Boolean);
      const stop = node.getAttribute('data-topic');
      const stid = node.id.replace('node_', '');

      document.querySelectorAll('.person-label').forEach(l => l.style.display = 'none');
      document.querySelectorAll('[id^="person_"]').forEach(p => {
          const spid = p.getAttribute('data-pid');
          if (!peopleIds.includes(spid)) p.classList.add('blur-out');
      });
      const centre = document.getElementById('centre_group');
      if (centre) centre.classList.add('blur-out');
      document.querySelectorAll('[id^="node_"]').forEach(n => {
          if (n.id !== node.id) n.setAttribute('opacity', '0.2');
      });

        peopleIds.forEach(spid => {
          const edge = document.getElementById('edge_' + spid + '_' + stop);
          if (edge) edge.style.display = '';
          const label = document.getElementById('text_' + spid);
          if (label) label.style.display = '';
        });
  }

  document.querySelectorAll('.group-sent').forEach(el => {
      el.setAttribute('data-default', el.textContent);
      el.setAttribute('data-default-fill', el.getAttribute('fill'));
  });
  document.querySelectorAll('.target-sent').forEach(el => {
      el.setAttribute('data-default', el.textContent);
  });

  document.querySelectorAll('[id^="node_"]').forEach(node => {
    node.addEventListener('mouseenter', () => {
      if (!lockedId) showNodeHighlight(node);
    });
    node.addEventListener('mouseleave', resetAll);
    node.addEventListener('click', (e) => {
      e.stopPropagation();
      if (lockedId === node.id) {
        lockedId = null;
        resetAll();
      } else {
        lockedId = node.id;
        showNodeHighlight(node);
      }
    });
  });

  persons.forEach(g => {
    const pid = g.getAttribute('data-pid');
    g.addEventListener('mouseenter', () => {
      if (!lockedId) showPersonHighlight(pid);
    });
    g.addEventListener('mouseleave', resetAll);
    g.addEventListener('click', (e) => {
      e.stopPropagation();
      const fullId = 'person_' + pid;
      if (lockedId === fullId) {
        lockedId = null;
        resetAll();
      } else {
        lockedId = fullId;
        showPersonHighlight(pid);
      }
    });
  });

  document.addEventListener('click', () => {
      if (lockedId) {
          lockedId = null;
          resetAll();
      }
  });

  resetAll();
})();
</script>
"""


# ── public API ──────────────────────────────────────────────────────────────

def build_d1_html(bias_persons, nodes, participation_reasons):
    """Build Board Sentiment Bias Map. Returns HTML string (SVG + CSS + JS) for mo.iframe()."""

    persons = bias_persons.to_dict(orient="records")

    # ── data aggregation ────────────────────────────────────────────────
    agg = (
        nodes
        .groupby(["topic_id", "target_id", "target_type", "industry"])
        .agg(
            avg_sentiment=("sentiment", "mean"),
            avg_sentiment_raw=("sentiment_raw", "mean"),
            people=("people_id", lambda x: frozenset(x)),
        )
        .reset_index()
    )

    topics = {}
    for _, row in agg.iterrows():
        tid = row["topic_id"]
        if tid not in topics:
            topics[tid] = {"targets": [], "sentiments": [], "sentiments_raw": [], "industries": []}
        topics[tid]["targets"].append(row.to_dict())
        topics[tid]["sentiments"].append(row["avg_sentiment"])
        topics[tid]["sentiments_raw"].append(row["avg_sentiment_raw"])
        topics[tid]["industries"].append(row["industry"])

    for tid, t in topics.items():
        t["avg_sentiment"] = sum(t["sentiments"]) / len(t["sentiments"])
        t["avg_sentiment_raw"] = sum(t["sentiments_raw"]) / len(t["sentiments_raw"])
        t["industry"] = Counter(t["industries"]).most_common(1)[0][0]

    fishing_topics = [(tid, t) for tid, t in topics.items() if t["industry"] == "fishing"]
    tourism_topics = [(tid, t) for tid, t in topics.items() if t["industry"] == "tourism"]
    both_topics = [(tid, t) for tid, t in topics.items() if t["industry"] in ("both", "other")]
    both_topic_ids = {tid for tid, _ in both_topics}

    # ── canvas dimensions ───────────────────────────────────────────────
    CELL = 140
    MARGIN = 0
    R_CENTER = 30
    R_RING = 90
    R_CLOUD = 35

    W = max(1100, max(len(fishing_topics), len(tourism_topics), 1) * CELL + 2 * MARGIN)
    ZONE_H = CELL + 50
    CENTRE_H = R_RING * 2 + 100
    H = ZONE_H + CENTRE_H + ZONE_H + 2 * MARGIN

    FISH_Y = MARGIN
    TOUR_Y = MARGIN + ZONE_H + CENTRE_H
    cx = W / 2
    cy = MARGIN + ZONE_H + CENTRE_H / 2

    # ── topic placement ─────────────────────────────────────────────────
    def place_in_band(topic_list, band_y, band_h):
        n = len(topic_list)
        if n == 0:
            return {}
        out = {}
        for i, (tid, _) in enumerate(topic_list):
            x = MARGIN + CELL / 2 + i * ((W - 2 * MARGIN - CELL) / max(n - 1, 1))
            y = band_y + band_h / 2
            out[tid] = (x, y)
        return out

    cloud_pos = {}
    cloud_pos.update(place_in_band(fishing_topics, FISH_Y, ZONE_H))
    cloud_pos.update(place_in_band(tourism_topics, TOUR_Y, ZONE_H))

    # Neutral / Both topics centred vertically on the right
    NEUTRAL_X_START = cx + R_RING + 170
    for i, (tid, _) in enumerate(both_topics):
        cloud_pos[tid] = (NEUTRAL_X_START + 130, cy + 20)

    # ── target positions ────────────────────────────────────────────────
    target_pos = {}
    for tid, (gx, gy) in cloud_pos.items():
        tlist = topics[tid]["targets"]
        n = len(tlist)
        r = R_CLOUD if n > 1 else 0
        for j, t in enumerate(tlist):
            _angle = -math.pi / 2 + 2 * math.pi * j / max(n, 1)
            target_pos[t["target_id"]] = (
                gx + r * math.cos(_angle),
                gy + r * math.sin(_angle),
                t,
            )

    # ── person positions ────────────────────────────────────────────────
    person_pos = {}
    for i, p in enumerate(persons):
        pid = p.get("people_id", p.get("id", i))
        _angle = -math.pi / 2 + 2 * math.pi * i / len(persons)
        person_pos[pid] = (
            cx + R_RING * math.cos(_angle),
            cy + R_RING * math.sin(_angle),
            p,
        )

    # ── person -> topic & target sentiments ─────────────────────────────
    person_target_sent = nodes.groupby(["people_id", "target_id"])["sentiment"].mean().to_dict()
    person_target_raw = nodes.groupby(["people_id", "target_id"])["sentiment_raw"].mean().to_dict()
    person_target_gov = nodes.groupby(["people_id", "target_id"])["in_gov_data"].min().to_dict()
    person_topic_sent = nodes.groupby(["people_id", "topic_id"])["sentiment"].mean().to_dict()
    person_topic_raw = nodes.groupby(["people_id", "topic_id"])["sentiment_raw"].mean().to_dict()

    pid_to_targets = defaultdict(dict)
    pid_to_topics = defaultdict(dict)

    for (pid, tgt), sent in person_target_sent.items():
        if pid in person_pos:
            raw_s = person_target_raw.get((pid, tgt), sent)
            is_gov = person_target_gov.get((pid, tgt), True)
            pid_to_targets[pid][tgt] = (sent, raw_s, is_gov)

    for (pid, top), sent in person_topic_sent.items():
        if pid in person_pos:
            raw_s = person_topic_raw.get((pid, top), sent)
            pid_to_topics[pid][top] = (sent, raw_s)

    # ── z-order buckets ─────────────────────────────────────────────────
    bg, zone_labels, clouds, edges = [], [], [], []
    target_nodes, ring_layer, centre_layer, legend_layer = [], [], [], []

    mean_val = bias_persons["avg_sentiment"].mean()
    pale = _interp(
        min(abs(mean_val), 1.0) * 0.3,
        (255, 255, 255),
        (46, 204, 113) if mean_val >= 0 else (231, 76, 60),
    )

    bg.append(svg.Defs(elements=[
        svg.RadialGradient(id="g_mean", cx="50%", cy="50%", r="50%", elements=[
            svg.Stop(offset="0%", stop_color=pale),
            svg.Stop(offset="100%", stop_color=_color_for(mean_val)),
        ]),
        svg.LinearGradient(id="grad_legend", x1="0%", y1="0%", x2="100%", y2="0%", elements=[
            svg.Stop(offset="0%", stop_color="#e74c3c"),
            svg.Stop(offset="50%", stop_color="#ffffff"),
            svg.Stop(offset="100%", stop_color="#2ecc71"),
        ]),
    ]))

    bg += [
        svg.Rect(x=0, y=FISH_Y, width=W, height=ZONE_H,
                 fill="#3498db", opacity=0.05,
                 stroke="#2980b9", stroke_width=1, stroke_dasharray="6,4"),
        svg.Rect(x=0, y=TOUR_Y, width=W, height=ZONE_H,
                 fill="#f1c40f", opacity=0.05,
                 stroke="#f39c12", stroke_width=1, stroke_dasharray="6,4"),
        # Neutral area background
        svg.Rect(x=cx + R_RING + 180, y=cy - 90, width=260, height=180,
                 fill="#f0f0f0", opacity=0.6, rx=15, ry=15),
    ]

    # ── legend ──────────────────────────────────────────────────────────
    leg_x, leg_y = 15, cy - 60

    legend_layer += [
        svg.Text(x=leg_x, y=leg_y, text="Sentiment for fishing",
                 font_size=10, font_weight="bold", fill="#555"),
        svg.Rect(x=leg_x, y=leg_y + 8, width=90, height=8,
                 fill="url(#grad_legend)", stroke="#999", stroke_width=0.5),
        svg.Text(x=leg_x, y=leg_y + 28, text="-1",
                 font_size=9, fill="#555", text_anchor="middle"),
        svg.Text(x=leg_x + 45, y=leg_y + 28, text="0",
                 font_size=9, fill="#555", text_anchor="middle"),
        svg.Text(x=leg_x + 90, y=leg_y + 28, text="+1",
                 font_size=9, fill="#555", text_anchor="middle"),

        svg.Text(x=leg_x, y=leg_y + 50, text="Item Type",
                 font_size=10, font_weight="bold", fill="#555"),
        svg.Polygon(
            points=(
                f"{leg_x + 5},{leg_y + 62 - 6} "
                f"{leg_x + 5 + 6 * 0.951},{leg_y + 62 - 6 * 0.309} "
                f"{leg_x + 5 + 6 * 0.588},{leg_y + 62 + 6 * 0.809} "
                f"{leg_x + 5 - 6 * 0.588},{leg_y + 62 + 6 * 0.809} "
                f"{leg_x + 5 - 6 * 0.951},{leg_y + 62 - 6 * 0.309}"
            ),
            fill="#ccc", stroke="#999",
        ),
        svg.Text(x=leg_x + 15, y=leg_y + 65, text="Discussion",
                 font_size=10, fill="#555"),
        svg.Rect(x=leg_x - 1, y=leg_y + 75, width=10, height=10,
                 fill="#ccc", stroke="#999"),
        svg.Text(x=leg_x + 15, y=leg_y + 83, text="Plan",
                 font_size=10, fill="#555"),

        svg.Text(x=leg_x, y=leg_y + 110, text="Government vs Journalist data",
                 font_size=10, font_weight="bold", fill="#555"),
        _person_glyph(leg_x + 5, leg_y + 130, fill="#ccc"),
        _halo(leg_x + 5, leg_y + 130, has_crown=False),
        svg.Text(x=leg_x + 15, y=leg_y + 127, text="Complete",
                 font_size=10, fill="#555"),
        svg.G(class_="glow-dishonest", elements=[
            _person_glyph(leg_x + 5, leg_y + 155, fill="#ccc"),
            _devil_horns(leg_x + 5, leg_y + 155),
        ]),
        svg.Text(x=leg_x + 15, y=leg_y + 152, text="Incomplete",
                 font_size=10, fill="#555"),
    ]

    # ── zone labels ─────────────────────────────────────────────────────
    left_edge = 10
    zone_labels = [
        svg.Text(x=left_edge, y=FISH_Y + 10, text="Pro-fishing topics",
                 text_anchor="start", font_size=12, fill="#2980b9", font_weight="bold"),
        svg.Text(x=left_edge, y=TOUR_Y + 10, text="Pro-tourism topics",
                 text_anchor="start", font_size=12, fill="#d68910", font_weight="bold"),
    ]

    if both_topics:
        zone_labels.append(svg.Text(
            x=cx + R_RING + 190, y=cy - 75,
            text="Topic supporting both fishing and tourism",
            text_anchor="start", font_size=12, fill="#555", font_weight="bold",
        ))

    # ── topic clouds ────────────────────────────────────────────────────
    for tid, (gx, gy) in cloud_pos.items():
        t = topics[tid]
        n = len(t["targets"])
        blob_r = R_CLOUD + 5 + n * 2
        stid = _safe_id(tid)
        avg_s = t["avg_sentiment"]
        avg_s_raw = t["avg_sentiment_raw"]

        clouds += [
            svg.Circle(cx=gx, cy=gy, r=blob_r,
                       fill=_color_for(avg_s), opacity=0.18,
                       stroke=_color_for(avg_s), stroke_width=1.2, stroke_dasharray="4,3"),
            svg.Text(x=gx, y=gy - blob_r - 6, text=str(tid),
                     text_anchor="middle", font_size=10, fill="#444", font_weight="bold"),
            svg.Text(x=gx, y=gy, text=_fmt_sent(avg_s_raw),
                     id=f"group_sent_{stid}", class_="group-sent",
                     text_anchor="middle", dominant_baseline="central", font_size=12,
                     fill=_color_for(avg_s), font_weight="bold"),
        ]

    # ── edges (person -> topic) ─────────────────────────────────────────
    for pid, topics_dict in pid_to_topics.items():
        px, py, p = person_pos[pid]
        spid = _safe_id(pid)
        for top_id, (p_sent, p_raw) in topics_dict.items():
            if top_id not in cloud_pos:
                continue
            gx, gy = cloud_pos[top_id]
            stop = _safe_id(top_id)
            stroke_w = max(0.8, abs(p_sent) * 10)
            if top_id in both_topic_ids:
                col = "#999"
            else:
                col = _color_for(p_sent)

            t = topics[top_id]
            n = len(t["targets"])
            blob_r = R_CLOUD + 5 + n * 2

            dx, dy = px - gx, py - gy
            dist = math.hypot(dx, dy)
            if dist > 0:
                end_x = gx + (dx / dist) * blob_r
                end_y = gy + (dy / dist) * blob_r
            else:
                end_x, end_y = gx, gy

            edges.append(svg.Line(
                x1=px, y1=py, x2=end_x, y2=end_y,
                stroke=col, stroke_width=stroke_w, opacity=0.75,
                id=f"edge_{spid}_{stop}", style="display:none",
            ))

    # ── target nodes ────────────────────────────────────────────────────
    for tid_key, (tx, ty, data) in target_pos.items():
        fill = _color_for(data["avg_sentiment"])
        stid = _safe_id(tid_key)

        target_people = [_safe_id(pid) for pid in data.get("people", [])]
        topic_id = _safe_id(data["topic_id"])

        base = dict(id=f"node_{stid}", fill=fill, opacity="1",
                    stroke="#999", stroke_width=1.0)

        if data["target_type"] == "discussion":
            sz = 10
            c1, s1 = 0.951, 0.309
            c2, s2 = 0.588, 0.809
            pts = (
                f"{tx},{ty - sz} "
                f"{tx + sz * c1},{ty - sz * s1} "
                f"{tx + sz * c2},{ty + sz * s2} "
                f"{tx - sz * c2},{ty + sz * s2} "
                f"{tx - sz * c1},{ty - sz * s1}"
            )
            target_nodes.append(_DataPolygon(
                data_fill=fill,
                data_people=",".join(target_people),
                data_topic=topic_id,
                points=pts,
                **base,
            ))
        else:
            sz = 8
            target_nodes.append(_DataRect(
                data_fill=fill,
                data_people=",".join(target_people),
                data_topic=topic_id,
                x=tx - sz, y=ty - sz, width=sz * 2, height=sz * 2,
                **base,
            ))

        val_str = _fmt_sent(data["avg_sentiment_raw"], 1)

        target_nodes.append(svg.Text(
            x=tx, y=ty, text=val_str,
            id=f"target_text_bg_{stid}", class_="target-sent",
            font_size=7.5, fill="none",
            stroke="rgba(255, 255, 255, 0.8)", stroke_width=2, stroke_linejoin="round",
            text_anchor="middle", dominant_baseline="central",
            style="pointer-events:none;",
        ))
        target_nodes.append(svg.Text(
            x=tx, y=ty, text=val_str,
            id=f"target_text_fg_{stid}", class_="target-sent",
            font_size=7.5, fill="#111", font_weight="bold",
            text_anchor="middle", dominant_baseline="central",
            style="pointer-events:none;",
        ))

    # ── ring layer (person glyphs) ──────────────────────────────────────
    for pid, (px, py, p) in person_pos.items():
        role = p.get("role", "")
        honest = p.get("honesty", True)
        has_crown = role in ("Committee Chair", "Vice Chair")
        spid = _safe_id(pid)

        connected_targets = [
            f"{_safe_id(t)}:{_color_for(s_biased)}:{_fmt_sent(s_raw, 1)}:{1 if is_gov else 0}"
            for t, (s_biased, s_raw, is_gov) in pid_to_targets.get(pid, {}).items()
        ]
        connected_topics = [
            f"{_safe_id(t)}:{_color_for(s_biased)}:{_fmt_sent(s_raw)}"
            for t, (s_biased, s_raw) in pid_to_topics.get(pid, {}).items()
        ]

        p_sent = p.get("avg_sentiment", 0)
        g_els = [_person_glyph(px, py, _color_for(p_sent))]
        if role == "Treasurer":
            g_els.append(_chest(px, py))
        if not honest:
            g_els.append(_devil_horns(px, py))
        if role == "Committee Chair":
            g_els.append(_king_crown(px, py))
        elif role == "Vice Chair":
            g_els.append(_queen_crown(px, py))
        if honest:
            g_els.append(_halo(px, py, has_crown))

        name = p.get("name", "Unknown")
        g_els.append(svg.Text(
            x=px + 10, y=py + 3,
            text=f"{name} ({_fmt_sent(p_sent)})",
            font_size=9, fill="#333",
            id=f"text_{spid}", class_="person-label",
        ))

        ring_layer.append(_DataG(
            id=f"person_{spid}",
            elements=g_els,
            class_="glow-dishonest" if not honest else "",
            style="cursor:pointer",
            data_targets=";".join(connected_targets),
            data_topics=";".join(connected_topics),
            data_pid=spid,
        ))

    # ── centre layer ────────────────────────────────────────────────────
    centre_layer_elements = [
        svg.Circle(cx=cx, cy=cy, r=R_RING,
                   fill="none", stroke="#ddd", stroke_dasharray="3,3"),
        svg.Circle(cx=cx, cy=cy, r=R_CENTER,
                   fill="url(#g_mean)", stroke="#333", stroke_width=1.5),
        svg.Text(x=cx, y=cy, text=_fmt_sent(mean_val),
                 fill=_text_ink(mean_val), text_anchor="middle",
                 dominant_baseline="central", font_size=12, font_weight="bold"),
    ]
    centre_layer = [
        svg.G(id="centre_group", elements=centre_layer_elements,
              style="transition: opacity 0.3s, filter 0.3s"),
    ]

    # ── assemble SVG ────────────────────────────────────────────────────
    all_el = (
        bg + legend_layer + zone_labels + clouds
        + edges + target_nodes + ring_layer + centre_layer
    )
    svg_str = svg.SVG(height=H, width=W, elements=all_el).as_str()

    # ── reason lookup JSON ──────────────────────────────────────────────
    reason_lookup = {}
    if participation_reasons is not None and not participation_reasons.empty:
        for _, rr in participation_reasons[
            (participation_reasons["entity_type"] == "person")
            & (participation_reasons["reason"].notna())
        ].iterrows():
            rkey = f'{rr["entity_id"]}|{rr["target_id"]}'
            if rkey not in reason_lookup:
                reason_lookup[rkey] = []
            sent_str = (
                f'{rr["sentiment"]:+.1f}'
                if pd.notna(rr.get("sentiment"))
                else "?"
            )
            reason_lookup[rkey].append(
                f'[{sent_str}] {str(rr["reason"])[:120]}'
            )

    reason_script = "<script>var REASONS=" + json.dumps(reason_lookup) + ";</script>"

    return svg_str + _CSS + reason_script + _JS
