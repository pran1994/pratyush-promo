import os, json, base64
from datetime import date
import pandas as pd
import altair as alt
import streamlit as st

# ────────────────────────────────────────────────────────────────────────────────
# Page config
# ────────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Promotion Dashboard", page_icon="🌟", layout="wide")

# ────────────────────────────────────────────────────────────────────────────────
# Styles
# ────────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* overall bg */
body { background-color: #FCFBF7; }
.block-container { max-width: 1200px; background-color: #FCFBF7; }

/* hero + section headings */
.hero { padding:22px 26px; border-radius:18px;
        background:linear-gradient(135deg,#4F46E520,#06B6D420);
        border:1px solid #e5e7eb; }
.section-title { font-size:20px; font-weight:700; margin:0 0 8px 0; }
.divider-dark { height:3px; background:#1f2937; opacity:.1; border-radius:999px; }

/* chips + tags */
.pill { display:inline-flex; align-items:center; gap:6px; padding:6px 12px;
       border-radius:999px; background:#4F46E515; color:#4F46E5; font-weight:600;
       font-size:12px; margin-right:6px; }
.tag { display:inline-block; font-size:12px; padding:3px 8px; border-radius:999px;
       border:1px solid #e5e7eb; margin-right:6px; color:#475569; }

/* intro block (no card/box) */
.intro-wrap h1 { font-size:34px; margin:0 0 8px 0; }
.intro-lead { color:#374151; font-size:15px; line-height:1.35; }

/* deep-dive spacing: clear visual separation from coloured rule */
.dd-sep { height:24px; }  /* increased from 6px to 24px for more space above colored line */
.dd-rule { height:4px; border-radius:999px; margin:4px 0 22px 0; }  /* reduced top margin from 8px to 4px */

/* small helper for logo column in timeline */
.logo-cell { text-align:center; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────────
# Load content
# ────────────────────────────────────────────────────────────────────────────────
def load_content(path="data/content.json"):
    if not os.path.exists(path):
        st.error("data/content.json not found. Create it and restart.")
        st.stop()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

C = load_content()

# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────
SECTION_ICONS = {
    "Overview":"📌","Relationship Building":"🤝","Problem Solving":"🧩",
    "Communication":"🗣️","Commercial Craft":"💼","Data & AI SME Expertise":"🧠"
}
SECTION_COLORS = {
    "Overview":"#0ea5e9","Relationship Building":"#22c55e","Problem Solving":"#6366f1",
    "Communication":"#f59e0b","Commercial Craft":"#ec4899","Data & AI SME Expertise":"#14b8a6"
}

def bullet_preview(items, n=2):
    out=[]
    for x in items:
        s=str(x).strip()
        if not s or s.endswith(":"): continue
        out.append(s)
        if len(out)==n: break
    return out

def render_grouped(items):
    if not items:
        return
    groups=[]; cur=[]; found=False
    for raw in items:
        s=str(raw).strip()
        if not s: continue
        if s.endswith(":"):
            found=True
            if cur: groups.append(cur)
            cur=[s]
        else:
            if not cur and found: cur=["Details:"]
            cur.append(s)
    if cur: groups.append(cur)
    if not found:
        for s in items:
            s=str(s).strip()
            if s: st.markdown(f"- {s}")
        return
    for grp in groups:
        if not grp: continue
        st.markdown(f"**{grp[0]}**")
        for bullet in grp[1:]:
            bullet=str(bullet).strip()
            if bullet: st.markdown(f"- {bullet}")

# image helpers (for Altair mark_image)
def _first_existing(paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None

def img_to_data_url(path):
    if not path or not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lstrip(".").lower() or "png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{ext};base64,{b64}"

# ────────────────────────────────────────────────────────────────────────────────
# Timeline with logo axis (no configure_* on subcharts!)
# ────────────────────────────────────────────────────────────────────────────────
def timeline_gantt_with_logo_axis(ranges):
    if not ranges:
        st.warning("Add timeline_ranges in data/content.json to render the timeline.")
        return

    # build dataframe
    df = pd.DataFrame(ranges)
    for col in ["lane","start","end","label"]:
        if col not in df.columns:
            st.error(f"timeline_ranges missing '{col}'"); return

    df["start"] = pd.to_datetime(df["start"], errors="coerce")
    df["end"]   = pd.to_datetime(df["end"],   errors="coerce").fillna(pd.to_datetime(date.today()))

    # client vs internal, pretty org label
    df["is_client"] = ~df["lane"].astype(str).str.startswith("Internal")
    df["org"] = df["lane"].astype(str).str.replace("Client — ","", regex=False)
    df.loc[~df["is_client"], "org"] = df.loc[~df["is_client"], "lane"]

    # keep original ordering: clients (sorted by name) on top, then internals
    lanes = df["lane"].tolist()
    # unique in original order:
    seen = set(); ordered_lanes=[]
    for l in lanes:
        if l not in seen:
            seen.add(l); ordered_lanes.append(l)
    y_order = [l.replace("Client — ","") if not l.startswith("Internal") else l for l in ordered_lanes]

    # icon map (tries several likely paths)
    logo_candidates = {
        "AEMO":          ["assets/aemo.png","data/assets/aemo.png","aemo.png"],
        "Australia Post":["assets/auspost.png","data/assets/auspost.png","auspost.png"],
        "IAG":           ["assets/iag.png","data/assets/iag.png","iag.png"],
        "Vanguard":      ["assets/vanguard.png","data/assets/vanguard.png","vanguard.png"],
    }
    df["icon"] = None
    for org, candidates in logo_candidates.items():
        path = _first_existing(candidates)
        if path:
            data_url = img_to_data_url(path)
            df.loc[df["org"]==org, "icon"] = data_url

    # color grouping
    df["group"] = df["is_client"].map({True:"Client", False:"Internal"})

    # bars (main timeline)
    bars = (
        alt.Chart(df)
        .mark_bar(cornerRadius=6, stroke="white", strokeWidth=0.6)
        .encode(
            x=alt.X("start:T", title="", axis=alt.Axis(format="%b %Y")),
            x2=alt.X2("end:T"),
            y=alt.Y("org:N", sort=y_order, title="", axis=alt.Axis(labels=False)), # Hide labels
            color=alt.Color(
                "group:N", title="Work type",
                scale=alt.Scale(domain=["Client","Internal"], range=["#6366F1","#94A3B8"]),
                legend=alt.Legend(orient="bottom", direction="horizontal")
            ),
            tooltip=[
                alt.Tooltip("org:N", title="Organisation"),
                alt.Tooltip("start:T", title="Start"),
                alt.Tooltip("end:T", title="End"),
            ],
        )
        .properties(width=980, height=240)
    )

    # logo column (clients only); tooltip shows ONLY organisation
    df_logo = df[(df["is_client"]) & (df["icon"].notna())].copy()
    logos = (
        alt.Chart(df_logo)
        .mark_image()
        .encode(
            y=alt.Y("org:N", sort=y_order, title=""),
            x=alt.value(26),  # center inside narrow column
            url=alt.Url("icon:N"),
            tooltip=[alt.Tooltip("org:N", title="Organisation")]
        )
        .properties(width=60, height=240)
    )

    # concat WITHOUT configure on subcharts; apply on final chart only
    chart = alt.hconcat(logos, bars, spacing=8).resolve_scale(y='shared')
    chart = chart.configure_view(stroke=None)

    st.altair_chart(chart, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────────
# Hero
# ────────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1 style="margin:0 0 6px 0;">🌟 Promotion Summary</h1>
  <div style="color:#475569; font-size:14px;">{summary}</div>
  <div style="margin-top:10px;">
    <span class="pill">Delivery Leadership</span>
    <span class="pill">Stakeholder Trust</span>
    <span class="pill">Commercial Impact</span>
    <span class="pill">Data & AI</span>
  </div>
</div>
""".format(summary=C.get("summary","")), unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────────
# Intro (no white card)
# ────────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='intro-wrap'>", unsafe_allow_html=True)
cols = st.columns([1,1.6])
with cols[0]:
    # show provided picture if available
    pic_candidates = ["assets/intro_photo.png","data/assets/intro_photo.png","intro_photo.png"]
    pic = _first_existing(pic_candidates)
    if pic:
        st.image(pic, use_container_width=True)
with cols[1]:
    st.markdown("<h1>Hi, I am Pratyush! 👋 </h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='intro-lead'>"
        "I am a Business Technical Consultant with over five years of experience leading key data transformations across finance, insurance, logistics, and sports. "
        "I have worked with organisations such as Vanguard, IAG, Australia Post, and the AFL."
        " Here is a quick summary of how I meet the criteria for a Senior Consultant at Mantel."
        "</div><br>",
        unsafe_allow_html=True
    )
    # bullets from prompt
    bullets = [
        "Data & AI Delivery Leadership: Run complex reporting and transformation streams end-to-end, from scoping to clean client handover.",
        "Stakeholder Engagement: Trusted by senior stakeholders for clear communication and proactive updates, even in high-pressure situations.",
        "Structured Problem Solving: Diagnose tricky grain/data issues and design pragmatic fixes without losing momentum.",
        "Commercial Craft: Shape proposals and pitches by combining technical understanding with business storytelling.",
        "Internal Enablement: Curate pathways like the dbt learning program to scale skills internally.",
        "AI/ML Integration: Leverage LLM-powered solutions to reduce manual work and accelerate insights.",
    ]
    for b in bullets:
        st.markdown(f"- {b}")
st.markdown("</div>", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────────
# Journey Timeline (with logo axis)
# ────────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Journey at Mantel 🛤️</div>", unsafe_allow_html=True)
st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
timeline_gantt_with_logo_axis(C.get("timeline_ranges", []))

# ────────────────────────────────────────────────────────────────────────────────
# Highlights (kept concise)
# ────────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>Highlights ✨</div>", unsafe_allow_html=True)
st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
highs = C.get("highlights", [])
if highs:
    cols = st.columns(min(3, len(highs)))
    for i, h in enumerate(highs):
        with cols[i % len(cols)]:
            title = h.get('title','')
            meta = h.get('metric', '')
            ctx = h.get('context','')
            link = h.get('link', '')
            
            # Display title without link
            st.markdown(f"**{title}**")
                
            if meta: 
                st.markdown(f"<span class='tag'>{meta}</span>", unsafe_allow_html=True)
            if ctx:  
                st.markdown(f"<div style='margin:.25rem 0 1rem 0; color:#475569;'>{ctx}</div>", unsafe_allow_html=True)
            # Add link below description if available
            if link:
                st.markdown(f"[Link]({link})")
else:
    st.caption("No highlights available yet.")

# ────────────────────────────────────────────────────────────────────────────────
# KPI Deep-Dives
# ────────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-title'>KPI Deep-Dives 📊</div>", unsafe_allow_html=True)
st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
matrix = C.get("matrix", {})
if matrix:
    for k, bullets in matrix.items():
        icon = SECTION_ICONS.get(k,"📄")
        color = SECTION_COLORS.get(k,"#4F46E5")
        st.markdown(
            f"<div style='display:flex; align-items:center; gap:8px; margin:2px 0 6px 0;'>"
            f"<div style='font-size:20px'>{icon}</div><div style='font-weight:700'>{k}</div></div>",
            unsafe_allow_html=True
        )
        prev = bullet_preview(bullets, 2)
        if prev:
            for p in prev: st.markdown(f"• {p}")
        with st.expander("Details"):
            render_grouped(bullets)
        st.markdown(f"<div class='dd-sep'></div><div class='dd-rule' style='background:{color}'></div>", unsafe_allow_html=True)
else:
    st.caption("No KPI details available yet.")

# ────────────────────────────────────────────────────────────────────────────────
# Certifications & Achievements 🏆 + Client Quote
# ────────────────────────────────────────────────────────────────────────────────
ach = C.get("achievements", [])
if ach:
    st.markdown("<div class='section-title'>Certifications & Achievements 🏆</div>", unsafe_allow_html=True)
    st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
    cols = st.columns(min(3, len(ach)))
    for i, a in enumerate(ach):
        with cols[i % len(cols)]:
            icon=a.get("icon","🎓"); title=a.get("title",""); issuer=a.get("issuer","")
            when=a.get("date",""); note=a.get("note",""); link=a.get("link")
            line = f"{icon} **{title}** — {issuer}" + (f" · {when}" if when else "")
            if link: line = f"[{line}]({link})"
            st.markdown(line, unsafe_allow_html=True)
            if note: st.caption(note)

    # optional: what clients say (first testimonial)
    fs = C.get("feedback_section", {})
    tlist = fs.get("testimonials", []) if isinstance(fs, dict) else []
    if tlist:
        t = tlist[0]
        who = " — ".join([x for x in [t.get("name"), t.get("org")] if x])
        st.markdown("")
        st.markdown("*What clients say*")
        st.markdown(f"> “{t.get('quote','')}” — **{who}**")

# ────────────────────────────────────────────────────────────────────────────────
# Tabs: Feedback (quotes only) + Growth Plan
# ────────────────────────────────────────────────────────────────────────────────
tabs = st.tabs(["Feedback", "Growth Plan"])

with tabs[0]:
    st.subheader("Feedback 💬")
    st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
    fs = C.get("feedback_section", {})
    quotes = fs.get("quotes", []) if isinstance(fs, dict) else []
    if quotes:
        for q in quotes:
            who = " — ".join([x for x in [q.get("name"), q.get("org")] if x])
            st.markdown(f"> “{q.get('quote','')}”  \n— **{who}**")
            st.write("")
    else:
        st.info("No feedback quotes available yet.")

with tabs[1]:
    st.subheader("Growth Plan 📈")
    for g in C.get("growth", []):
        st.markdown(f"- {g}")

