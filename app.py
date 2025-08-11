import os, json
from datetime import date
import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="Promotion Dashboard — Pratyush Ranjan", page_icon="🌟", layout="wide")

# ---------- Styles ----------
st.markdown("""
<style>
/* Exterior (outside content) gets 50% opacity of FCFBF7 */
html, body, [data-testid="stAppViewContainer"], .main {
    background-color: rgba(252, 251, 247, 0.5) !important; /* #FCFBF7 @ 50% */
}

/* Interior content area stays solid */
.block-container { 
    max-width: 1200px; 
    background-color: #FCFBF7;
}

/* Optional utility classes from your earlier design */
.card { background:#fff; border:1px solid #e5e7eb; border-radius:16px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
.card:hover { box-shadow:0 10px 28px rgba(0,0,0,.06); transition:box-shadow .12s ease; }
.hero { padding:22px 26px; border-radius:18px; background:linear-gradient(135deg,#4F46E520,#06B6D420); border:1px solid #e5e7eb; }
.kpi { text-align:center; padding:16px; border-radius:14px; border:1px solid #e5e7eb; background:#fff; }
.kpi h3 { margin:2px 0 0 0; font-size:28px; }
.kpi p { margin:0; color:#64748B; font-size:12px; }
.pill { display:inline-flex; align-items:center; gap:6px; padding:6px 12px; border-radius:999px; background:#4F46E515; color:#4F46E5; font-weight:600; font-size:12px; margin-right:6px; }
.subhead { font-weight:700; margin:.35rem 0 .15rem 0; }
.indent { margin-left:.75rem; }
.section-title { font-size:20px; font-weight:700; margin:0 0 8px 0; }
.tag { display:inline-block; font-size:12px; padding:3px 8px; border-radius:999px; border:1px solid #e5e7eb; margin-right:6px; color:#475569; }
.badge { display:inline-block; font-size:11px; padding:2px 8px; border-radius:999px; }
.badge-was { background:#fee2e2; color:#b91c1c; border:1px solid #fecaca; }
.badge-now { background:#dcfce7; color:#166534; border:1px solid #bbf7d0; }
.testimonial { background:#f8fafc; border:1px solid #e5e7eb; border-radius:16px; padding:16px; }
blockquote { margin:0; font-size:14px; color:#334155; }
.achip { display:inline-flex; align-items:center; gap:8px; padding:8px 12px; border:1px solid #e5e7eb; border-radius:999px; background:#ffffff; margin:6px 8px 0 0; }
.achip b { margin-right:2px; }
.ach-grid { display:flex; flex-wrap:wrap; }
hr { border: none; border-top: 1px solid #e5e7eb; margin: 10px 0; }

/* Dark divider used between sections (kept from previous versions) */
.divider-dark { height: 2px; background: #444; margin: 10px 0 16px 0; border-radius: 999px; }

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
ach = C.get("achievements", [])

# ---------- Helpers ----------
SECTION_ICONS = {"Overview":"📌","Relationship Building":"🤝","Problem Solving":"🧩","Communication":"🗣️","Commercial Craft":"💼","Data & AI SME Expertise":"🧠"}
SECTION_COLORS = {"Overview":"#0ea5e9","Relationship Building":"#22c55e","Problem Solving":"#6366f1","Communication":"#f59e0b","Commercial Craft":"#ec4899","Data & AI SME Expertise":"#14b8a6"}

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
        tooltip=[alt.Tooltip("label:N", title="Work"), alt.Tooltip("lane:N", title="Lane"),
                 alt.Tooltip("start:T", title="Start"), alt.Tooltip("end:T", title="End")]
    ).configure_view(stroke=None)
    st.altair_chart(bars, use_container_width=True)

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
    h=[]; m=C.get("metrics",[])
    if m:
        h.append({"title":"Breadth of Delivery","metric":f"{m[0][0]} projects • {m[1][0]} stakeholders","context":"Led multi-client delivery with consistent stakeholder outcomes."})
    mx=C.get("matrix",{})
    if "Problem Solving" in mx:
        prev=bullet_preview(mx["Problem Solving"],1)
        if prev: h.append({"title":"Diagnosis under pressure","metric":"SVOF ELT grain fix","context":prev[0]})
    if "Commercial Craft" in mx:
        prev=bullet_preview(mx["Commercial Craft"],1)
        if prev: h.append({"title":"Pre-sales momentum","metric":"AEMO / EPA / TNSW","context":prev[0]})
    return h[:3]

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
    # 3 columns on desktop; Streamlit will stack on small screens
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
                st.markdown(f"<div style='margin:.25rem 0 1rem 0; color:#475569;'>{ctx}</div>", unsafe_allow_html=True)
else:
    st.info("No highlights available.")

# ---------- KPI Deep-Dives ----------
st.markdown("<div class='section-title'>KPI Deep-Dives</div>", unsafe_allow_html=True)
st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
matrix=C.get("matrix",{})
if matrix:
    for k, bullets in matrix.items():
        if not bullets:
            continue
        icon=SECTION_ICONS.get(k,"📄"); color=SECTION_COLORS.get(k,"#4F46E5")
        st.markdown(f"<div style='display:flex; align-items:center; gap:8px; margin:2px 0 6px 0;'><div style='font-size:20px'>{icon}</div><div style='font-weight:700'>{k}</div></div>", unsafe_allow_html=True)
        prev=bullet_preview(bullets,2)
        if prev:
            for p in prev: st.markdown(f"• {p}")
        with st.expander("Details"):
            render_grouped(bullets)
        st.markdown(f"<div style='height:3px; border-radius:999px; background:{color}; margin:8px 0 12px 0; opacity:.65;'></div>", unsafe_allow_html=True)
else:
    st.info("No KPI details available.")

# ---------- Certifications & Achievements (columns) ----------
ach = C.get("achievements", [])
if ach:
    st.markdown("<div class='section-title'>Certifications & Achievements</div>", unsafe_allow_html=True)
    st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
    
    num_cols = min(3, len(ach))  # up to 3 per row
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
            if link:
                label = f"[{label}]({link})"
            st.markdown(label, unsafe_allow_html=True)
            if note:
                st.markdown(f"<span style='color:#475569'>{note}</span>", unsafe_allow_html=True)

    # --- Add testimonial QUOTE + NAME/ORG as a small italic sub-section ---
    fs = C.get("feedback_section", {})
    testi_list = fs.get("testimonials", []) if isinstance(fs, dict) else []
    quote_text = name_text = org_text = None
    if testi_list and isinstance(testi_list, list):
        first = testi_list[0]
        if isinstance(first, dict):
            quote_text = first.get("quote")
            name_text = first.get("name")
            org_text = first.get("org")
    if quote_text:
        st.markdown("")
        st.markdown("*What clients say*")
        tail = ""
        if name_text and org_text:
            tail = f" — **{name_text}, {org_text}**"
        elif name_text:
            tail = f" — **{name_text}**"
        elif org_text:
            tail = f" — **{org_text}**"
        st.markdown(f"> “{quote_text}”{tail}")

# ---------- Tabs: Feedback + Growth Plan ----------
tabs = st.tabs(["Feedback", "Growth Plan"])

with tabs[0]:
    st.subheader("Feedback")
    st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)

    fs=C.get("feedback_section", {})
    good = fs.get("good", []) if isinstance(fs, dict) else []
    improve = fs.get("improve", []) if isinstance(fs, dict) else []

    if good:
        st.markdown("#### Strengths Recognised")
        st.markdown("<div class='divider-dark' style='opacity:.3;'></div>", unsafe_allow_html=True)
        for card in good:
            st.markdown(f"**{card.get('title','')}**")
            synopsis = card.get("context","")
            if synopsis: st.markdown(synopsis)
            tag = card.get("tag","")
            if tag: st.markdown(f"<span class='tag'>{tag}</span>", unsafe_allow_html=True)
            evp = card.get("evidence_points", []) or []
            evs = card.get("evidence", "")
            if evp or evs:
                with st.expander("Evidence"):
                    if evp:
                        for b in evp: st.markdown(f"- {b}")
                    elif evs:
                        st.markdown(evs)

    if improve:
        st.markdown("#### Working on Feedback")
        st.markdown("<div class='divider-dark' style='opacity:.3;'></div>", unsafe_allow_html=True)
        for card in improve:
            st.markdown(f"**{card.get('title','')}**")
            was=card.get("was",""); now=card.get("now","")
            if was: st.markdown(f"<span class='badge badge-was'>Was</span> {was}", unsafe_allow_html=True)
            if now: st.markdown(f"<span class='badge badge-now'>Now</span> {now}", unsafe_allow_html=True)
            evp = card.get("evidence_points", []) or []
            evs = card.get("evidence", "")
            if evp or evs:
                with st.expander("Evidence"):
                    if evp:
                        for b in evp: st.markdown(f"- {b}")
                    elif evs:
                        st.markdown(evs)

with tabs[1]:
    st.subheader("Growth Plan")
    for g in C.get("growth", []):
        st.markdown(f"- {g}")

# ---------- Appendix (own section, after tabs) ----------
st.markdown("<div class='section-title'>Appendix</div>", unsafe_allow_html=True)
st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)

fs = C.get("feedback_section", {})
testis = fs.get("testimonials", []) if isinstance(fs, dict) else []
# Only render images (no text)
has_any_image = False
for t in testis:
    if isinstance(t, dict) and t.get("image"):
        img_path = t["image"]
        if os.path.exists(img_path):
            # Render smaller image: fixed width for neatness
            st.image(img_path, width=500, caption=t.get("image_caption",""))
            has_any_image = True
        else:
            st.caption(f"(Image not found: {img_path})")
if not has_any_image:
    st.caption("(No appendix image available)")

st.markdown("<div class='divider-dark'></div>", unsafe_allow_html=True)
