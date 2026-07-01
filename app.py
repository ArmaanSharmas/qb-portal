import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(__file__))
from data.players import (
    PLAYERS, TIER_CONFIG, GRADE_COLORS, PORTAL_PROB_COLORS, BUILD_TIER_LABELS,
    UPSIDE_COLORS, AVAILABILITY_COLORS, SYSTEM_FIT_COLORS,
)

st.set_page_config(
    page_title="QB Portal Scouting Report — 2026",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

.main .block-container {
    padding-top: 1.4rem;
    padding-bottom: 2rem;
    max-width: 1380px;
}

.report-header {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2e4a 100%);
    padding: 1.5rem 2rem;
    border-radius: 8px;
    margin-bottom: 1.2rem;
    border-left: 5px solid #b8952a;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

.tier-badge {
    display: inline-block; padding: 2px 8px; border-radius: 3px;
    font-size: 0.66rem; font-weight: 700; letter-spacing: 0.4px;
    color: white; text-transform: uppercase;
}
.portal-pill {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.65rem; font-weight: 700; color: white;
    text-transform: uppercase; letter-spacing: 0.4px;
}
.stat-chip {
    background: #eef0f3; border-radius: 3px; padding: 3px 8px;
    font-size: 0.71rem; font-weight: 500; color: #374151;
    display: inline-block; margin: 1px;
}
.contingent-badge {
    display: inline-block; padding: 2px 8px; border-radius: 3px;
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.3px;
    color: #92400e; background: #fef3c7; border: 1px solid #fcd34d;
    text-transform: uppercase;
}

.section-title {
    font-size: 0.67rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.5px; color: #64748b;
    margin: 1.2rem 0 0.5rem 0; padding-bottom: 3px;
    border-bottom: 1px solid #e2e8f0;
}

.player-row-card {
    background: white; border: 1px solid #e2e8f0; border-radius: 5px;
    padding: 0.85rem 1rem; margin-bottom: 0.4rem;
    border-left: 3px solid #1d4ed8;
}

.summary-box {
    background: rgba(128,128,128,0.07); border-left: 3px solid #b8952a;
    padding: 0.85rem 1rem; border-radius: 0 5px 5px 0;
    font-size: 0.87rem; line-height: 1.65;
}

.metric-box {
    background: #f8fafc; border-radius: 6px;
    padding: 0.7rem 0.9rem; text-align: center; border: 1px solid #e2e8f0;
}
.metric-box .value { font-size: 1.3rem; font-weight: 700; line-height: 1.2; }
.metric-box .label {
    font-size: 0.63rem; color: #64748b; text-transform: uppercase;
    letter-spacing: 0.8px; margin-top: 2px;
}
.metric-box .mdesc { font-size: 0.61rem; color: #94a3b8; margin-top: 3px; }

.player-detail-header {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2e4a 100%);
    padding: 1.4rem 1.8rem; border-radius: 8px; margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def grade_color(grade):
    return GRADE_COLORS.get(grade, "#374151")

def build_tier_label(tier_num):
    return BUILD_TIER_LABELS.get(tier_num, f"Tier {tier_num}")

def format_adv_metric(name, val):
    if name in ('Pressure%', 'SRATE'):
        return f"{val:.1f}%"
    elif name == 'EPA/DB':
        return f"{val:+.3f}"
    return str(val)

def stars_display(n):
    if n is None:
        return "—"
    return "★" * n

UPSIDE_ORDER    = {"High": 3, "Moderate": 2, "Low": 1}
AVAIL_ORDER     = {"High": 3, "Moderate": 2, "Low": 1}


def _render_player_card(p):
    tier_cfg     = TIER_CONFIG[p["tier"]]
    status_color = "#1a4a2e" if p["status"] == "Monitor" else "#1d4ed8"
    up_color     = UPSIDE_COLORS.get(p["upside"], "#374151")
    av_color     = AVAILABILITY_COLORS.get(p["availability"], "#374151")
    sf_color     = SYSTEM_FIT_COLORS.get(p["systemFit"], "#374151")

    epa_str  = f"EPA/DB: {p['epaPerDropback']:+.3f}" if p["epaPerDropback"] is not None else "EPA/DB: —"
    adot_str = f"ADOT: {p['adot']}" if p["adot"] is not None else "ADOT: —"
    stars_str = stars_display(p.get("stars"))

    contingent_html = ""
    if p.get("contingent"):
        contingent_html = '<span class="contingent-badge">Only if displaced</span>'

    st.markdown(f"""
    <div class="player-row-card" style="border-left-color:{tier_cfg['color']};">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
            <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:2px; flex-wrap:wrap;">
                    <span style="font-size:0.97rem; font-weight:700; color:#0d1b2a;">{p['name']}</span>
                    {contingent_html}
                </div>
                <div style="font-size:0.78rem; color:#4b5563; margin-bottom:6px;">
                    {p['school']} &nbsp;·&nbsp; {p['conference']} &nbsp;·&nbsp; {p['currentRole']} &nbsp;·&nbsp;
                    {p['class']} &nbsp;·&nbsp; {p['eligibilityYears']} yrs eligibility
                </div>
                <div style="display:flex; gap:5px; flex-wrap:wrap; align-items:center; margin-bottom:5px;">
                    <span class="tier-badge" style="background:{status_color}">{p['status']}</span>
                    <span class="stat-chip">{p['hometown']}</span>
                    <span class="stat-chip">Stars: {stars_str}</span>
                    <span class="stat-chip" style="color:{up_color}; font-weight:700;">Upside: {p['upside']}</span>
                    <span class="stat-chip" style="color:{av_color}; font-weight:700;">Avail: {p['availability']}</span>
                    <span class="stat-chip" style="color:{sf_color}; font-weight:700;">Fit: {p['systemFit']}</span>
                </div>
                <div style="font-size:0.77rem; color:#64748b; font-style:italic;">{p['notes']}</div>
            </div>
            <div style="text-align:right; flex-shrink:0; min-width:130px;">
                <div style="font-size:0.72rem; color:#64748b; margin-bottom:4px;">{epa_str} &nbsp; {adot_str}</div>
                <div style="font-size:0.68rem; color:#94a3b8; margin-top:4px;">Verified: {p['lastVerified']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Report Header ─────────────────────────────────────────────────────────────
proj_total = sum(1 for p in PLAYERS if p["status"] == "Projection")
mon_total  = sum(1 for p in PLAYERS if p["status"] == "Monitor")

st.markdown(f"""
<div class="report-header">
    <div>
        <div style="font-size:1.5rem; font-weight:700; color:#ffffff; margin-bottom:0.25rem; letter-spacing:0.2px;">
            Pre-Season QB Portal Scouting Report
        </div>
        <div style="color:rgba(255,255,255,0.72); font-size:0.75rem; letter-spacing:1.2px; text-transform:uppercase;">
            2026 Season &nbsp;·&nbsp; Prepared June 2026
        </div>
    </div>
    <div style="display:flex; gap:2rem;">
        <div style="text-align:right;">
            <div style="font-size:1.9rem; font-weight:700; color:#ffffff; line-height:1;">{len(PLAYERS)}</div>
            <div style="font-size:0.62rem; text-transform:uppercase; letter-spacing:0.8px; color:rgba(255,255,255,0.62); margin-top:2px;">Players</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:1.9rem; font-weight:700; color:#ffffff; line-height:1;">{proj_total}</div>
            <div style="font-size:0.62rem; text-transform:uppercase; letter-spacing:0.8px; color:rgba(255,255,255,0.62); margin-top:2px;">Projection</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:1.9rem; font-weight:700; color:#ffffff; line-height:1;">{mon_total}</div>
            <div style="font-size:0.62rem; text-transform:uppercase; letter-spacing:0.8px; color:rgba(255,255,255,0.62); margin-top:2px;">Monitor</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_ov, tab_prof, tab_stats, tab_nil, tab_method = st.tabs(
    ["Overview", "Player Profile", "Stats Comparison",
     "NIL Market Context", "Methodology & Limitations"]
)


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_ov:
    # ── Summary counts (computed from data, never hardcoded) ──
    t2_count   = sum(1 for p in PLAYERS if p["tier"] == 2)
    cont_count = sum(1 for p in PLAYERS if p["contingent"])

    qc1, qc2, qc3, qc4, qc5 = st.columns(5)
    for col, (label, value) in zip(
        [qc1, qc2, qc3, qc4, qc5],
        [
            ("Total Players",    len(PLAYERS)),
            ("Projection",       proj_total),
            ("Monitor",          mon_total),
            ("Tier 2",           t2_count),
            ("Only If Displaced", cont_count),
        ],
    ):
        col.markdown(f"""
        <div class="metric-box" style="margin-bottom:1rem;">
            <div class="value" style="color:#0d1b2a;">{value}</div>
            <div class="label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Filter + sort controls ──
    fc1, fc2, fc3, fc4, fc5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2])
    with fc1:
        f_tier = st.selectbox("Tier", ["All", "2", "3", "4"], label_visibility="visible")
    with fc2:
        f_status = st.selectbox("Status", ["All", "Projection", "Monitor"])
    with fc3:
        f_avail = st.selectbox("Availability", ["All", "High", "Moderate", "Low"])
    with fc4:
        f_upside = st.selectbox("Upside", ["All", "High", "Moderate", "Low"])
    with fc5:
        sort_by = st.selectbox("Sort by", ["Tier", "Upside", "Availability"])

    # Apply filters
    filtered = PLAYERS[:]
    if f_tier != "All":
        filtered = [p for p in filtered if p["tier"] == int(f_tier)]
    if f_status != "All":
        filtered = [p for p in filtered if p["status"] == f_status]
    if f_avail != "All":
        filtered = [p for p in filtered if p["availability"] == f_avail]
    if f_upside != "All":
        filtered = [p for p in filtered if p["upside"] == f_upside]

    # Apply sort
    if sort_by == "Upside":
        filtered = sorted(filtered, key=lambda p: (-UPSIDE_ORDER.get(p["upside"], 0), p["tier"]))
    elif sort_by == "Availability":
        filtered = sorted(filtered, key=lambda p: (-AVAIL_ORDER.get(p["availability"], 0), p["tier"]))
    # default: Tier (natural order in PLAYERS list, grouped by tier)

    if not filtered:
        st.info("No players match the current filters.")
    else:
        if sort_by == "Tier":
            # Group by tier
            tiers_present = sorted({p["tier"] for p in filtered})
            for tier_num in tiers_present:
                tier_players = [p for p in filtered if p["tier"] == tier_num]
                cfg = TIER_CONFIG[tier_num]
                st.markdown(f"""
                <div style="background:{cfg['color']}12; border-left:3px solid {cfg['color']};
                            padding:5px 10px; border-radius:0 4px 4px 0; margin:1.1rem 0 0.4rem 0;">
                    <span style="font-size:0.73rem; font-weight:700; color:{cfg['color']};
                                 text-transform:uppercase; letter-spacing:0.8px;">
                        {cfg['label']} &nbsp;({len(tier_players)})
                    </span>
                </div>
                """, unsafe_allow_html=True)
                for p in tier_players:
                    _render_player_card(p)
        else:
            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
            for p in filtered:
                _render_player_card(p)


# ══════════════════════════════════════════════════════════════════════════════
# PLAYER PROFILE
# ══════════════════════════════════════════════════════════════════════════════
with tab_prof:
    player_names = [p["name"] for p in PLAYERS]
    selected_name = st.selectbox("Select Player", player_names)
    p = next(x for x in PLAYERS if x["name"] == selected_name)

    tier_cfg       = TIER_CONFIG[p["tier"]]
    portal_color   = PORTAL_PROB_COLORS.get(p["portal_probability"], "#374151")
    approach_color = "#1a4a2e" if p["status"] == "Monitor" else "#1d4ed8"
    up_color       = UPSIDE_COLORS.get(p["upside"], "#374151")
    av_color       = AVAILABILITY_COLORS.get(p["availability"], "#374151")
    sf_color       = SYSTEM_FIT_COLORS.get(p["systemFit"], "#374151")

    contingent_badge = ""
    if p.get("contingent"):
        contingent_badge = '<span class="contingent-badge" style="font-size:0.72rem; padding:3px 9px;">Only if displaced</span>'

    st.markdown(f"""
    <div class="player-detail-header">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
            <div>
                <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:3px;">
                    <span style="font-size:1.75rem; font-weight:700; color:#ffffff;">{p['name']}</span>
                    {contingent_badge}
                </div>
                <div style="font-size:0.88rem; color:rgba(255,255,255,0.75); margin-bottom:8px;">
                    {p['school']} &nbsp;·&nbsp; {p['conference']} &nbsp;·&nbsp; {p['currentRole']} &nbsp;·&nbsp; {p['class']}
                </div>
                <div style="display:flex; gap:7px; flex-wrap:wrap;">
                    <span class="tier-badge" style="background:{tier_cfg['color']}">{tier_cfg['label']}</span>
                    <span class="tier-badge" style="background:{approach_color}">{p['status']} List</span>
                    <span style="font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:3px;
                                 background:{up_color}22; color:{up_color}; border:1px solid {up_color}55;">
                        Upside: {p['upside']}
                    </span>
                    <span style="font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:3px;
                                 background:{av_color}22; color:{av_color}; border:1px solid {av_color}55;">
                        Avail: {p['availability']}
                    </span>
                    <span style="font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:3px;
                                 background:{sf_color}22; color:{sf_color}; border:1px solid {sf_color}55;">
                        System Fit: {p['systemFit']}
                    </span>
                </div>
            </div>
            <div style="text-align:right; font-size:0.81rem; line-height:1.9;">
                <div style="color:rgba(255,255,255,0.75);">Hometown: <span style="color:#ffffff; font-weight:500;">{p['hometown']}</span></div>
                <div style="color:rgba(255,255,255,0.75);">Eligibility: <span style="color:#ffffff; font-weight:500;">{p['eligibilityYears']} years</span></div>
                <div style="color:rgba(255,255,255,0.75);">Stars: <span style="color:#ffffff; font-weight:500;">{stars_display(p.get('stars'))}</span></div>
                <div style="color:rgba(255,255,255,0.75);">Portal Status: <span style="color:#ffffff; font-weight:500;">{p['portal_status']}</span></div>
                <div style="color:rgba(255,255,255,0.50); font-size:0.72rem;">Verified: {p['lastVerified']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="summary-box">{p["summary"]}</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    ptab1, ptab2, ptab3, ptab4 = st.tabs(["Profile", "Advanced Stats", "Traits", "Evaluation"])

    # ── Profile
    with ptab1:
        col_phys, col_rec = st.columns(2)

        with col_phys:
            st.markdown('<div class="section-title">Physical Profile</div>', unsafe_allow_html=True)
            phys = p["physical"]
            bt = phys.get("build_tier", 4)
            bt_colors = {1: "#1e5c2e", 2: "#1a4a7a", 3: "#b45309", 4: "#991b1b"}
            bt_color = bt_colors.get(bt, "#374151")
            for label, val in [
                ("Height",     phys["height"]),
                ("Weight",     phys["weight"]),
                ("Hand Size",  phys["hand_size"]),
                ("Build Tier", build_tier_label(bt)),
                ("Build Note", phys["build_note"]),
            ]:
                ca, cb = st.columns([1, 2])
                ca.markdown(f"<div style='font-size:0.77rem; font-weight:600; opacity:0.5; padding:3px 0;'>{label}</div>", unsafe_allow_html=True)
                if label == "Build Tier":
                    cb.markdown(f"<div style='font-size:0.81rem; font-weight:700; color:{bt_color}; padding:3px 0;'>{val}</div>", unsafe_allow_html=True)
                else:
                    cb.markdown(f"<div style='font-size:0.81rem; padding:3px 0;'>{val}</div>", unsafe_allow_html=True)

        with col_rec:
            st.markdown('<div class="section-title">Recruiting Profile</div>', unsafe_allow_html=True)
            rec = p["recruiting"]
            for label, val in [
                ("Rating",        rec["rating"]),
                ("National Rank", rec["national_rank"]),
                ("QB Rank",       rec["qb_rank"]),
                ("State Rank",    rec["state_rank"]),
                ("Awards",        rec["awards"]),
                ("Camp / Notes",  rec["camp"]),
            ]:
                ca, cb = st.columns([1, 2])
                ca.markdown(f"<div style='font-size:0.77rem; font-weight:600; opacity:0.5; padding:3px 0;'>{label}</div>", unsafe_allow_html=True)
                cb.markdown(f"<div style='font-size:0.81rem; padding:3px 0;'>{val}</div>", unsafe_allow_html=True)

        if p["hs_stats"]:
            st.markdown('<div class="section-title">High School Statistics</div>', unsafe_allow_html=True)
            hs_data = []
            for row in p["hs_stats"]:
                hs_data.append({
                    "Season":   row["season"],
                    "Cmp%":     f"{row['cmp_pct']:.1f}%" if row["cmp_pct"]          else "—",
                    "Pass Yds": f"{row['yards']:,}"       if row["yards"]            else "—",
                    "TD":       row["td"]                 if row["td"]               else "—",
                    "INT":      row["int"]                if row["int"] is not None  else "—",
                    "Rush Yds": f"{row['rush_yds']:,}"    if row.get("rush_yds")     else "—",
                    "Rush TD":  row["rush_td"]            if row.get("rush_td")      else "—",
                })
            st.dataframe(pd.DataFrame(hs_data), use_container_width=True, hide_index=True)

    # ── Advanced Stats
    with ptab2:
        adv = p.get("advanced_stats")
        if not adv:
            st.info("No CFBGraphs advanced statistics available. Either no meaningful college dropbacks exist yet, or this player competes at the FCS level.")
        else:
            if adv.get("epa_db") is not None:
                metric_colors_mid = {
                    "good":    "#1e5c2e",
                    "neutral": "#b45309",
                    "poor":    "#991b1b",
                }
                metrics = {
                    "EPA/DB":    (adv["epa_db"],      -0.3,  0.4,  "Primary efficiency rate"),
                    "ADOT":      (adv["adot"],          5.0, 15.0,  "Avg depth of target"),
                    "Pressure%": (adv["pressure_pct"], 15.0, 55.0,  "% dropbacks under pressure"),
                    "SRATE":     (adv["srate"],         30.0, 75.0, "Success rate %"),
                }
                cols_m = st.columns(4)
                for i, (name, (val, vmin, vmax, desc)) in enumerate(metrics.items()):
                    if val is None:
                        cols_m[i].markdown(f"""
                        <div class="metric-box">
                            <div class="value" style="opacity:0.35;">—</div>
                            <div class="label">{name}</div>
                            <div class="mdesc">{desc}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        continue
                    pct = max(0, min(100, (val - vmin) / (vmax - vmin) * 100))
                    if name == "Pressure%":
                        color = metric_colors_mid["good"] if val < 30 else metric_colors_mid["neutral"] if val < 40 else metric_colors_mid["poor"]
                    else:
                        color = metric_colors_mid["good"] if pct > 65 else metric_colors_mid["neutral"] if pct > 35 else metric_colors_mid["poor"]
                    cols_m[i].markdown(f"""
                    <div class="metric-box">
                        <div class="value" style="color:{color};">{format_adv_metric(name, val)}</div>
                        <div class="label">{name}</div>
                        <div class="mdesc">{desc}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                others = [
                    x for x in PLAYERS
                    if x.get("advanced_stats") and x["advanced_stats"].get("epa_db") is not None
                    and x["name"] != p["name"]
                ]
                if others:
                    st.markdown('<div class="section-title">Comparison to Other Players with Stats</div>', unsafe_allow_html=True)
                    comp_names = [p["name"]] + [x["name"] for x in others]
                    comp_epa   = [adv["epa_db"]] + [x["advanced_stats"]["epa_db"] for x in others]
                    comp_adot  = [adv["adot"]]   + [x["advanced_stats"]["adot"]   for x in others]

                    cc1, cc2 = st.columns(2)
                    with cc1:
                        fig1 = go.Figure(go.Bar(
                            x=comp_names, y=comp_epa,
                            marker_color=["#1d4ed8" if n == p["name"] else "#c8d4e3" for n in comp_names],
                            text=[f"{v:+.3f}" for v in comp_epa],
                            textposition="outside", textfont=dict(size=10),
                        ))
                        fig1.add_hline(y=0, line_color="#cbd5e1", line_width=1)
                        fig1.update_layout(
                            title=dict(text="EPA / Dropback", font=dict(size=12), x=0),
                            height=280, margin=dict(l=20, r=20, t=40, b=80),
                            xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
                            yaxis=dict(tickfont=dict(size=9)),
                            plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                    with cc2:
                        fig2 = go.Figure(go.Bar(
                            x=comp_names, y=comp_adot,
                            marker_color=["#b8952a" if n == p["name"] else "#e8d8a0" for n in comp_names],
                            text=[f"{v:.1f}" for v in comp_adot],
                            textposition="outside", textfont=dict(size=10),
                        ))
                        fig2.update_layout(
                            title=dict(text="Avg Depth of Target (ADOT)", font=dict(size=12), x=0),
                            height=280, margin=dict(l=20, r=20, t=40, b=80),
                            xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
                            yaxis=dict(tickfont=dict(size=9)),
                            plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
                        )
                        st.plotly_chart(fig2, use_container_width=True)

            st.markdown('<div class="section-title">Context Note</div>', unsafe_allow_html=True)
            st.markdown(
                f"<div style='font-size:0.85rem; line-height:1.65; background:rgba(128,128,128,0.07); padding:0.8rem 1rem; border-radius:6px;'>{adv['note']}</div>",
                unsafe_allow_html=True,
            )
            if adv.get("dropbacks"):
                st.caption(f"Sample size: {adv['dropbacks']} dropbacks")

    # ── Traits
    with ptab3:
        grade_to_num = {
            "Elite": 5, "Very Good": 4, "Good": 3, "Positive": 3,
            "Developing": 2, "Unknown": 1, "Below Average": 1,
            "Concern": 1, "Neutral": 2, "Clear": 3,
        }
        trait_names   = [t[0] for t in p["traits"]]
        trait_vals    = [grade_to_num.get(t[1], 1) for t in p["traits"]]
        tnames_closed = trait_names + [trait_names[0]]
        tvals_closed  = trait_vals  + [trait_vals[0]]

        fig_radar = go.Figure(go.Scatterpolar(
            r=tvals_closed, theta=tnames_closed, fill="toself",
            fillcolor="rgba(26,46,74,0.10)",
            line=dict(color="#1d4ed8", width=2),
            marker=dict(size=5, color="#1d4ed8"),
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 5],
                                tickvals=[1, 2, 3, 4, 5],
                                ticktext=["1", "2", "3", "4", "5"],
                                tickfont=dict(size=8), gridcolor="#e2e8f0"),
                angularaxis=dict(tickfont=dict(size=9)),
                bgcolor="white",
            ),
            showlegend=False, height=370,
            margin=dict(l=60, r=60, t=30, b=30),
            paper_bgcolor="white",
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        for trait, grade, note in p["traits"]:
            gc = grade_color(grade)
            st.markdown(f"""
            <div style="display:flex; align-items:flex-start; gap:10px; padding:6px 0; border-bottom:1px solid rgba(128,128,128,0.15);">
                <div style="min-width:130px; font-size:0.81rem; font-weight:600;">{trait}</div>
                <div style="min-width:90px;">
                    <span style="font-size:0.73rem; font-weight:700; color:{gc}; background:{gc}1a; padding:2px 7px; border-radius:3px;">{grade}</span>
                </div>
                <div style="font-size:0.79rem; opacity:0.72; flex:1;">{note}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Evaluation
    with ptab4:
        st.markdown('<div class="section-title">College Evaluation</div>', unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-size:0.87rem; line-height:1.7;'>{p['college_eval']}</div>",
            unsafe_allow_html=True,
        )
        st.markdown('<div class="section-title">Portal Likelihood</div>', unsafe_allow_html=True)
        pc = PORTAL_PROB_COLORS.get(p["portal_probability"], "#374151")
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:0.6rem;">
            <span class="portal-pill" style="background:{pc}; font-size:0.78rem; padding:6px 14px;">
                {p['portal_probability']} Probability
            </span>
        </div>
        <div style="font-size:0.86rem; line-height:1.7; background:rgba(128,128,128,0.07);
                    padding:0.9rem 1.1rem; border-radius:6px; border-left:3px solid {pc};">
            {p['portal_note']}
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STATS COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
with tab_stats:
    st.markdown("### Advanced Stats Comparison")
    st.caption("Only players with CFBGraphs FBS data. FCS players and those with no college dropbacks are excluded.")

    stats_players = [
        p for p in PLAYERS
        if p.get("advanced_stats") and p["advanced_stats"].get("epa_db") is not None
    ]

    if len(stats_players) < 2:
        st.info("Not enough players with advanced stats data to compare.")
    else:
        names      = [p["name"]                          for p in stats_players]
        epa_vals   = [p["advanced_stats"]["epa_db"]      for p in stats_players]
        adot_vals  = [p["advanced_stats"]["adot"]         for p in stats_players]
        pres_vals  = [p["advanced_stats"]["pressure_pct"] for p in stats_players]
        srate_vals = [p["advanced_stats"]["srate"]        for p in stats_players]
        db_vals    = [p["advanced_stats"]["dropbacks"]    for p in stats_players]
        schools    = [p["school"]                         for p in stats_players]
        tiers      = [p["tier"]                           for p in stats_players]

        tier_colors_map = {1: "#1e5c2e", 2: "#1d4ed8", 3: "#b45309", 4: "#991b1b"}
        marker_colors = [tier_colors_map.get(t, "#64748b") for t in tiers]

        st.markdown('<div class="section-title">Stats Summary Table</div>', unsafe_allow_html=True)
        df = pd.DataFrame({
            "Player":    names,
            "School":    schools,
            "Dropbacks": db_vals,
            "EPA/DB":    [f"{v:+.3f}" for v in epa_vals],
            "ADOT":      [str(v) if v is not None else "—" for v in adot_vals],
            "Pressure%": [f"{v:.1f}%" if v is not None else "—" for v in pres_vals],
            "SRATE":     [f"{v:.1f}%" if v is not None else "—" for v in srate_vals],
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        sc1, sc2 = st.columns(2)

        with sc1:
            st.markdown('<div class="section-title">EPA/DB vs ADOT — Efficiency vs Aggressiveness</div>', unsafe_allow_html=True)
            fig_s = go.Figure()
            fig_s.add_vline(x=0, line_color="#cbd5e1", line_width=1, line_dash="dash")
            fig_s.add_trace(go.Scatter(
                x=epa_vals, y=adot_vals,
                mode="markers+text", text=names,
                textposition="top center", textfont=dict(size=9, color="#374151"),
                marker=dict(
                    size=[max(8, d / 8) for d in db_vals],
                    color=marker_colors,
                    line=dict(color="white", width=1.5),
                    opacity=0.88,
                ),
                hovertemplate="<b>%{text}</b><br>EPA/DB: %{x:.3f}<br>ADOT: %{y:.1f}<extra></extra>",
            ))
            fig_s.update_layout(
                height=350,
                xaxis=dict(title="EPA / Dropback", zeroline=False, gridcolor="#f1f5f9",
                           tickfont=dict(size=9), title_font=dict(size=11, color="#374151")),
                yaxis=dict(title="ADOT (yards)", gridcolor="#f1f5f9",
                           tickfont=dict(size=9), title_font=dict(size=11, color="#374151")),
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=40, r=20, t=20, b=40), showlegend=False,
            )
            st.plotly_chart(fig_s, use_container_width=True)
            st.caption("Bubble size = dropback volume. Color = tier. Top-right = positive EPA + high ADOT (ideal).")

        with sc2:
            st.markdown('<div class="section-title">Pressure% vs Success Rate</div>', unsafe_allow_html=True)
            pres_srate_data = [
                (p_val, s_val, n, c, d)
                for p_val, s_val, n, c, d in zip(pres_vals, srate_vals, names, marker_colors, db_vals)
                if p_val is not None and s_val is not None
            ]
            ps_pres, ps_srate, ps_names, ps_colors, ps_dbs = (
                zip(*pres_srate_data) if pres_srate_data else ([], [], [], [], [])
            )
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(
                x=list(ps_pres), y=list(ps_srate),
                mode="markers+text", text=list(ps_names),
                textposition="top center", textfont=dict(size=9, color="#374151"),
                marker=dict(
                    size=[max(8, d / 8) for d in ps_dbs],
                    color=list(ps_colors),
                    line=dict(color="white", width=1.5),
                    opacity=0.88,
                ),
                hovertemplate="<b>%{text}</b><br>Pressure%%: %{x:.1f}%%<br>SRATE: %{y:.1f}%%<extra></extra>",
            ))
            fig_p.update_layout(
                height=350,
                xaxis=dict(title="Pressure% (lower = cleaner pocket)", zeroline=False,
                           gridcolor="#f1f5f9", tickfont=dict(size=9),
                           title_font=dict(size=11, color="#374151")),
                yaxis=dict(title="Success Rate %", gridcolor="#f1f5f9",
                           tickfont=dict(size=9), title_font=dict(size=11, color="#374151")),
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=40, r=20, t=20, b=40), showlegend=False,
            )
            st.plotly_chart(fig_p, use_container_width=True)
            st.caption("Top-left = low pressure, high SRATE (clean execution). Top-right = resilient under pressure.")

        st.markdown('<div class="section-title">EPA/DB Ranking — Color = Tier</div>', unsafe_allow_html=True)
        sorted_data = sorted(zip(epa_vals, names, marker_colors, db_vals), reverse=True)
        s_epa, s_names, s_colors, s_dbs = zip(*sorted_data)
        fig_b = go.Figure(go.Bar(
            x=list(s_names), y=list(s_epa),
            marker_color=list(s_colors),
            text=[f"{v:+.3f}" for v in s_epa],
            textposition="outside", textfont=dict(size=10),
            hovertemplate="<b>%{x}</b><br>EPA/DB: %{y:.3f}<extra></extra>",
        ))
        fig_b.add_hline(y=0, line_color="#cbd5e1", line_width=1)
        fig_b.update_layout(
            height=300,
            xaxis=dict(tickfont=dict(size=10)),
            yaxis=dict(gridcolor="#f1f5f9", tickfont=dict(size=9)),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=40, r=20, t=20, b=50), showlegend=False,
        )
        st.plotly_chart(fig_b, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# NIL MARKET CONTEXT
# ══════════════════════════════════════════════════════════════════════════════
with tab_nil:
    st.markdown("### NIL Market Context")
    st.caption("Estimated portal QB market ranges based on 2024-25 cycle data. Figures reflect total package value across the portal window.")

    st.markdown('<div class="section-title">Portal QB Market Tiers</div>', unsafe_allow_html=True)

    nil_tiers = [
        {
            "tier":    "Elite Portal QB",
            "profile": "Multi-year Power Four starter with advanced stats. Proven production at the highest level, multiple years of eligibility remaining, no significant injury history. Immediate plug-and-play starter at any program.",
            "range":   "$2M – $5M+",
            "color":   "#1e5c2e",
        },
        {
            "tier":    "Proven Mid-Major Starter",
            "profile": "Full-season starter at G5 or lower P4 with verifiable production — completion percentage, TD/INT ratio, YPA. May have scheme limitations or measurable concerns but has demonstrated college-level execution under pressure.",
            "range":   "$500K – $1.5M",
            "color":   "#1d4ed8",
        },
        {
            "tier":    "High Pedigree / Limited Data",
            "profile": "Highly recruited prospect or Power Four backup with elite physical traits but insufficient college game reps to establish a statistical baseline. Value is forward-looking — programs are paying for upside and projection.",
            "range":   "$200K – $600K",
            "color":   "#b45309",
        },
        {
            "tier":    "Developmental Depth",
            "profile": "FCS, JUCO, or early-career player acquired to compete for a depth role or develop over 1-2 seasons. Limited immediate starting upside but fills roster and practice needs. Often walk-on or low-scholarship value.",
            "range":   "$50K – $200K",
            "color":   "#991b1b",
        },
    ]

    for row in nil_tiers:
        st.markdown(f"""
        <div style="display:flex; align-items:stretch; border:1px solid #e2e8f0; border-radius:7px;
                    margin-bottom:0.6rem; overflow:hidden;">
            <div style="width:4px; background:{row['color']}; flex-shrink:0;"></div>
            <div style="display:flex; align-items:center; gap:0; flex:1; flex-wrap:wrap;">
                <div style="min-width:190px; padding:0.85rem 1rem;">
                    <div style="font-size:0.82rem; font-weight:700; color:{row['color']}; text-transform:uppercase;
                                letter-spacing:0.4px; margin-bottom:3px;">{row['tier']}</div>
                    <div style="font-size:1.05rem; font-weight:700; letter-spacing:0.2px;">{row['range']}</div>
                </div>
                <div style="flex:1; padding:0.85rem 1rem; border-left:1px solid #e2e8f0; min-width:220px;">
                    <div style="font-size:0.82rem; line-height:1.6; opacity:0.85;">{row['profile']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="summary-box">
        The core value of pre-season evaluation is identifying Tier 2-3 talent before it becomes Tier 1 priced.
        A quarterback who enters the portal after a breakout season will attract multiple Power Four programs
        and price out within the first 48 hours. Programs that have completed this work before the portal window
        opens can move immediately — in the first 48 to 72 hours when the best targets are still available and
        before the market has fully re-priced the player's value. Pre-season evaluation converts reactive
        recruiting into a proactive process.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# METHODOLOGY & LIMITATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab_method:
    st.markdown("### Methodology & Limitations")

    col_method, col_limits = st.columns([3, 2])

    with col_method:
        st.markdown('<div class="section-title">Evaluation Framework</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.84rem; line-height:1.65; opacity:0.9; margin-bottom:1.2rem;">
            Player evaluations are structured across five domains. Each domain is assessed independently
            before a composite picture is formed.
        </div>
        """, unsafe_allow_html=True)

        domains = [
            (
                "Physical Profile",
                "#1d4ed8",
                "Height, weight, hand size, and build tier.",
                "Establishes the baseline NFL-viability ceiling and flags measurable concerns before any on-field evaluation begins. Build tier is assigned on a 1-4 scale where Tier 1 represents an NFL prototype at every measurable.",
            ),
            (
                "Throwing Ability",
                "#1d4ed8",
                "Arm strength, arm talent, release, and accuracy.",
                "Primary stats: ADOT and EPA/DB. ADOT measures how aggressively a quarterback is pushing the ball downfield. EPA/DB is the single most predictive college efficiency metric — it captures the value added (or lost) on every dropback relative to expectation.",
            ),
            (
                "Mental Game",
                "#1d4ed8",
                "Pre-snap reads, decision making, pocket presence, and pressure performance.",
                "Primary stats: EPA/DB, TD/INT ratio, success rate, and pressure percentage. Pressure percentage contextualizes all other efficiency numbers — positive EPA/DB under frequent pressure carries more weight than the same number behind a dominant offensive line.",
            ),
            (
                "Athleticism",
                "#1d4ed8",
                "Pocket mobility, scramble value, and designed rushing.",
                "Evaluated separately from passing ability. A quarterback who cannot threaten with his legs in any form is easier to defend schematically. Rush yards and rush TDs are tracked but weighted against the offensive system's designed run usage.",
            ),
            (
                "Supporting Cast",
                "#1d4ed8",
                "OL quality, receiver talent, scheme type, and competition level.",
                "The most important contextual adjustment. A 65% completion rate in an RPO spread with elite receivers behind a first-round OL is not the same as the same number in a pro-style system against a Power Four schedule. Every stat is evaluated within its context.",
            ),
        ]

        for name, color, short, detail in domains:
            st.markdown(f"""
            <div style="border:1px solid #e2e8f0; border-radius:7px; padding:0.85rem 1rem;
                        margin-bottom:0.55rem; border-left:3px solid {color};">
                <div style="font-size:0.82rem; font-weight:700; margin-bottom:4px;">{name}</div>
                <div style="font-size:0.76rem; font-weight:600; opacity:0.55; margin-bottom:5px;">{short}</div>
                <div style="font-size:0.79rem; line-height:1.6; opacity:0.82;">{detail}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_limits:
        st.markdown('<div class="section-title">Limitations</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.84rem; line-height:1.65; opacity:0.9; margin-bottom:1.2rem;">
            This report should be read with the following constraints in mind.
        </div>
        """, unsafe_allow_html=True)

        limitations = [
            (
                "Sample Size",
                "Most projection players have insufficient college dropbacks for statistically reliable evaluation. Trait assessment carries significant weight in the absence of volume data, which introduces subjectivity.",
            ),
            (
                "High School Stat Reliability",
                "Competition context varies enormously across HS programs and states. Raw numbers from HS are used directionally, not as comparables to college production.",
            ),
            (
                "No Tracking Data",
                "The full decision-execution model — which assigns predicted EPA to every route and isolates quarterback decisions from receiver performance — cannot be replicated with publicly available data.",
            ),
            (
                "Limited Access to Advanced Stats",
                "This report relies on free, publicly available data sources. As a result, important proprietary metrics are not included — PFF grades, turnover-worthy play rates, ball placement scores, and route-level targeting data are all unavailable. These gaps are most significant when evaluating decision-making and accuracy under pressure.",
            ),
            (
                "Scheme Dependence",
                "EPA/DB in an RPO spread is not directly comparable to the same number in a pro-style system. All efficiency metrics are adjusted for context where possible but perfect scheme normalization is not achievable.",
            ),
            (
                "Spring Practice Limitations",
                "Spring performance is a real signal — depth chart movement and coaching staff comments are meaningful data. However, spring reps carry substantially less certainty than game data against live competition.",
            ),
            (
                "Availability Is Speculative",
                "Upside and availability ratings are educated inference based on depth chart position, eligibility, and program context, not certainty. Players rated Low availability can enter the portal; players rated High may never.",
            ),
            (
                "Information Recency",
                "This report reflects evaluations as of June 2026. All ratings and portal projections should be revisited entering fall camp, after depth charts are finalized.",
            ),
        ]

        for title, body in limitations:
            st.markdown(f"""
            <div style="display:flex; gap:10px; padding:0.7rem 0;
                        border-bottom:1px solid rgba(128,128,128,0.15);">
                <div style="margin-top:3px; width:6px; height:6px; border-radius:50%;
                            background:#b8952a; flex-shrink:0;"></div>
                <div>
                    <div style="font-size:0.8rem; font-weight:700; margin-bottom:3px;">{title}</div>
                    <div style="font-size:0.78rem; line-height:1.6; opacity:0.75;">{body}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
