import os, json
from datetime import date
import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="Promotion Dashboard — Pratyush Ranjan", page_icon="🌟", layout="wide")

# ---------- Styles ----------
st.markdown("""
<style>
/* Force a light color scheme so dark-mode users don't get light text */
:root { color-scheme: light; }

/* Exterior area */
html, body, [data-testid="stAppViewContainer"], .main {
    background-color: rgba(252, 251, 247, 0.5) !important; /* #FCFBF7 @ 50% */
    color: #111827 !important; /* slate-900 equivalent for strong contrast */
}

/* Interior content area */
.block-container { 
    max-width: 1200px; 
    background-color: #FCFBF7;
    color: #111827 !important;
}

/* Make common text elements clearly readable regardless of theme */
h1, h2, h3, h4, h5, h6, p, li, span, div, label, code, pre, blockquote {
    color: #111827 !important;
}
a { color: #4F46E5 !important; }
small, .caption, .stCaption, .st-emotion-cache-1n76uvr { color: #475569 !important; }

/* Utility & layout */
.section-title { font-size:20px; font-weight:700; margin:0 0 8px 0; }
.divider-dark { height: 2px; background: #444; margin: 10px 0 16px 0; border-radius: 999px; }

.pill { display:inline-flex; align-items:center; gap:6px; padding:6px 12px; border-radius:999px;
        background:#4F46E515; color:#4F46E5; font-weight:600; font-size:12px; margin-right:6px; }
.tag { display:inline-block; font-size:12px; padding:3px 8px; border-radius:999px;
       border:1px solid #e5e7eb; margin-right:6px; color:#475569 !important; }
blockquote { margin:0; font-size:14px; color:#334155 !important; }
hr { border: none; border-top: 1px solid #e5e7eb; margin: 10px 0; }
@media (max-width: 900px){ .block-container{ padding-left:14px; padding-right:14px; } }
</style>
""", unsafe_allow_html=True)

# ---------- Load content ----------
def load_content(path="data/content.json"):
    if not os.path.exists(path):
        st.error("data/content.json not found. Create it and restart.")
        st.stop()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
C = load_content()

# ---------- Helpers ----------
SECTION_ICONS = {"Overview":"📌","Relationship Building":"🤝","Problem Solving":"🧩",
                 "Communication":"🗣️","Commercial Craft":"💼","Data & AI SME Expertise":"🧠"}
SECTION_COLORS = {"Overview":"#0ea5e9","Relationship Building":"#22c55e",
                  "Problem Solving":"#6366f1","Communication":"#f59e0b",
                  "Commercial Craft":"#ec4899","Data & AI SME Expertise":"#14b8a6"}

def timeline_gantt(ranges):
    if not ranges:
        st.warning("Add timeline_ranges in data/content.json to render the bar timeline.")
        return
    df = pd.DataFrame(ranges)
    for col in ["lane","start","end","label"]:
        if col not in df.columns:
            st.error(f"timeline_ranges missing '{col}'"); return
    df["start"]=pd.to_datetime(df["start"], errors="coerce")
    df["end"]=pd.to_datetime(df["end"], errors="coerce").fillna(pd.to_datetime(date.today()))
    lanes=df["lane"].unique().tolist(); lanes.sort(key=lambda x:(str(x).startswith("Internal"),str(x)))
    df["lane"]=pd.Categorical(df["lane"], categories=lanes, ordered=True)
    df["group"]=df["lane"].astype(str).map(lambda x:"Internal" if x.startswith("Internal") else "Client")
    chart=alt.Chart(df).properties(height=220)
    bars=chart.mark_bar(cornerRadius=6, stroke="white", strokeWidth=0.6).encode(
        x=alt.X("start:T", title="", axis=alt.Axis(format="%b %Y")),
        x2=alt.X2("end:T"),
        y=alt.Y("lane:N", title="", axis=alt.Axis(labelLimit=420)),
        color=alt.Color("group:N", title="Work type",
                        scale=alt.Scale(domain=["Client","Internal"], range=["#6366F1","#94A3B8"]),
                        legend=alt.Legend(orient="bottom", direction="horizontal")),
        tooltip=[alt.Tooltip("label:N", title="Work"),
                 alt.Tooltip("lane:N", title="Lane"),
                 alt.Tooltip("start:T", title="Start"),
                 alt.Tooltip("end:T", title="End")]
    ).configure_view(stroke=None)
    st.altair_chart(bars, use_container_width=True)

def bullet_preview(items, n=2):
    out=[]
    for x in items:
        s=str(x).strip()
        if not s or s.endswith(":"): continue
        out.append(s)
        if len(out)==n: break
    return out

def derive_highlights(C):
    if "highlights" in C and C["highlights"]:
        return C["highlights"]
    return []

# ---------- Top (Hero) ----------
st.markdown(f"""
<div style="padding:22px 26px; border-radius:18px; background:linear-gradient(135deg,#4F46E520,#06B6D420); border:1px solid #e5e7eb;">
  <h1 style="margin:0 0 6px 0;">🌟 Promotion Dashboard — {C.get('name','Your Name')}</h1>
  <div style="color:#475569; font-size:14px;">{C.get('summary','')}</div>
  <div style="margin-top:10px;">
    <span class="pill">Delivery Leadership</span>
    <span class="pill">Stakeholder Trust</span>
    <span class="pill">Commercial Impact</span>
    <span class="pill">Data & AI</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- Journey Timeline ----------
st.markdown("<div class='section-title'>Journey at Mantel</div>", unsafe_allow_html=True)
st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
timeline_gantt(C.get("timeline_ranges", []))

# ---------- Highlights ----------
highs = C.get("highlights", []) or derive_highlights(C)
st.markdown("<div class='section-title'>Highlights</div>", unsafe_allow_html=True)
st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
if highs:
    num_cols = min(3, len(highs))
    cols = st.columns(num_cols)
    for i, h in enumerate(highs):
        with cols[i % num_cols]:
            st.markdown(f"**{h.get('title','')}**")
            meta = h.get("metric", "")
            ctx  = h.get("context", "")
            if meta:
                st.markdown(f"<span class='tag'>{meta}</span>", unsafe_allow_html=True)
            if ctx:
                st.markdown(f"<div style='margin:.25rem 0 1rem 0;'>{ctx}</div>", unsafe_allow_html=True)
else:
    st.info("No highlights available.")

# ---------- KPI Deep-Dives ----------
st.markdown("<div class='section-title'>KPI Deep-Dives</div>", unsafe_allow_html=True)
st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
matrix=C.get("matrix",{})
if matrix:
    for k, bullets in matrix.items():
        if not bullets: continue
        icon=SECTION_ICONS.get(k,"📄"); color=SECTION_COLORS.get(k,"#4F46E5")
        st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin:2px 0 6px 0;'><div style='font-size:20px'>{icon}</div><div style='font-weight:700'>{k}</div></div>", unsafe_allow_html=True)
        prev=bullet_preview(bullets,2)
        if prev:
            for p in prev: st.markdown(f"• {p}")
        with st.expander("Details"):
            for b in bullets:
                b=str(b).strip()
                if b.endswith(":"): st.markdown(f"**{b}**")
                else: st.markdown(f"- {b}")
        st.markdown(f"<div style='height:3px; border-radius:999px; background:{color}; margin:8px 0 12px 0; opacity:.65;'></div>", unsafe_allow_html=True)
else:
    st.info("No KPI details available.")

# ---------- Certifications & Achievements ----------
ach = C.get("achievements", [])
if ach:
    st.markdown("<div class='section-title'>Certifications & Achievements</div>", unsafe_allow_html=True)
    st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
    num_cols = min(3, len(ach))
    cols = st.columns(num_cols)
    for i, a in enumerate(ach):
        with cols[i % num_cols]:
            icon = a.get("icon", "🎓")
            title = a.get("title", "")
            issuer = a.get("issuer", "")
            when = a.get("date", "")
            note = a.get("note", "")
            link = a.get("link")
            label = f"{icon} **{title}** — {issuer}" + (f" · {when}" if when else "")
            if link: label = f"[{label}]({link})"
            st.markdown(label, unsafe_allow_html=True)
            if note: st.markdown(f"<span style='color:#475569'>{note}</span>", unsafe_allow_html=True)

# ---------- Tabs: Feedback (quotes only) + Growth Plan ----------
tabs = st.tabs(["Feedback", "Growth Plan"])

with tabs[0]:
    st.subheader("Feedback")
    st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
    fs = C.get("feedback_section", {})
    quotes = fs.get("quotes", []) if isinstance(fs, dict) else []
    if not quotes:
        st.info("No feedback quotes available yet.")
    else:
        for q in quotes:
            quote = str(q.get("quote","")).strip()
            name  = str(q.get("name","")).strip()
            if quote:
                tail = f" — **{name}**" if name else ""
                st.markdown(f"> “{quote}”{tail}")

with tabs[1]:
    st.subheader("Growth Plan")
    for g in C.get("growth", []):
        st.markdown(f"- {g}")

# ---------- Appendix ----------
st.markdown("<div class='section-title'>Appendix</div>", unsafe_allow_html=True)
st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
st.caption("(No appendix image available)")
st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
