"""Goal-based financial planning website (ICT336 sample project).

Plan retirement, short-term and long-term goals. No login and no database: goals stay in the
browser session, and users keep their plan by downloading / uploading a CSV file.

Run locally:   streamlit run app.py
Deploy:        push this folder to GitHub, then create an app on Streamlit Community Cloud.
"""
import json
from datetime import datetime, timezone

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Goal Planner", page_icon="💰", layout="wide")

# ---------------------------------------------------------------- text (EN / TH)
TEXT = {
    "EN": {
        "title": "💰 Goal-Based Financial Planner",
        "subtitle": "Plan your savings and investments for retirement, short-term and long-term goals.",
        "note": "Sample project for ICT336. Returns are assumptions for teaching, not investment advice.",
        "tab_dash": "My goals", "tab_add": "Add a goal", "tab_ret": "Retirement planner",
        "tab_data": "Save / load plan",
        "types": {"retirement": "Retirement", "short": "Short-term", "long": "Long-term"},
        "type_help": "Short-term: within 3 years (trip, emergency fund). Long-term: more than 3 years (house, child's education).",
        "risks": {"conservative": "Conservative", "moderate": "Moderate", "aggressive": "Aggressive"},
        "goal_type": "Goal type", "goal_name": "Goal name", "target": "Target amount in today's money (฿)",
        "years": "Years until the goal", "current": "Money already saved for this goal (฿)",
        "monthly": "Monthly saving you plan to put in (฿)", "risk": "Risk you can accept",
        "inflation": "Inflation per year (%)", "ret": "Expected return per year (%)",
        "suggested": "Suggested portfolio for {y} years, {r} risk: expected return about {p:.1f}% per year",
        "save": "Save goal", "saved": "Saved “{n}”.", "need_name": "Please give the goal a name.",
        "no_goals": "You have no goals yet. Add one in “Add a goal” or “Retirement planner”, or load example goals or your saved CSV in “Save / load plan”.",
        "n_goals": "Goals", "total_target": "Total target (future ฿)", "monthly_plan": "Monthly saving planned",
        "monthly_need": "Monthly saving needed",
        "col_name": "Goal", "col_type": "Type", "col_years": "Years", "col_target": "Target (future ฿)",
        "col_proj": "Projected (฿)", "col_need": "Need / month", "col_plan": "Plan / month",
        "col_prog": "Funded", "col_status": "Status",
        "on_track": "✅ On track", "behind": "⚠️ Behind",
        "detail": "Details", "chart_x": "Year", "chart_y": "Amount (฿)",
        "line_proj": "Projected savings", "line_target": "Target",
        "gap": "To reach the target, save **฿{need:,.0f} per month** (you plan ฿{plan:,.0f}).",
        "ok": "Your plan reaches the target with ฿{extra:,.0f} to spare.",
        "alloc": "Suggested portfolio", "asset": "Asset", "weight": "Weight (%)",
        "update_monthly": "Change monthly saving (฿)", "update": "Update", "delete": "Delete goal",
        "deleted": "Deleted.",
        "assets": {"cash": "Deposits / money market", "bond": "Thai bonds",
                   "th_eq": "Thai equity", "gl_eq": "Global equity"},
        "r_age": "Your age now", "r_retire": "Retirement age", "r_life": "Plan money until age",
        "r_exp": "Monthly spending you want in retirement, in today's money (฿)",
        "r_other": "Other money at retirement (pension, PVD you already count) (฿)",
        "r_after": "Return per year after retirement (%)",
        "r_result": "You need about **฿{c:,.0f}** at age {a} "
                    "(spending ฿{m:,.0f} per month by then because of inflation).",
        "r_bad_age": "Retirement age must be above your age, and the plan-until age above retirement age.",
        "r_tips": "Tax-saving options in Thailand for retirement: provident fund (PVD), RMF, Thai ESG, "
                  "life-annuity insurance. Check the current limits before you invest.",
        "r_name": "Retirement at {a}",
        "data_info": "Your goals are kept only in this browser tab. Closing or refreshing the tab clears them, "
                     "so download the CSV file to keep your plan and upload it next time.",
        "session_info": "No login needed. Your goals stay in this browser tab only, and other people cannot see them.",
        "csv": "Download my goals (CSV)", "upload": "Upload a goals CSV saved earlier",
        "load": "Load this plan (replaces current goals)", "example": "Load example goals",
        "bad_csv": "This file is not a goals CSV from this app ({e}).",
    },
    "TH": {
        "title": "💰 วางแผนการเงินตามเป้าหมาย",
        "subtitle": "วางแผนการออมและการลงทุนสำหรับเกษียณ เป้าหมายระยะสั้น และเป้าหมายระยะยาว",
        "note": "โปรเจกต์ตัวอย่างวิชา ICT336 ผลตอบแทนเป็นสมมติฐานเพื่อการสอน ไม่ใช่คำแนะนำการลงทุน",
        "tab_dash": "เป้าหมายของฉัน", "tab_add": "เพิ่มเป้าหมาย", "tab_ret": "วางแผนเกษียณ",
        "tab_data": "บันทึก / โหลดแผน",
        "types": {"retirement": "เกษียณ", "short": "ระยะสั้น", "long": "ระยะยาว"},
        "type_help": "ระยะสั้น: ภายใน 3 ปี (ท่องเที่ยว เงินสำรองฉุกเฉิน) ระยะยาว: มากกว่า 3 ปี (ซื้อบ้าน การศึกษาลูก)",
        "risks": {"conservative": "รับความเสี่ยงได้ต่ำ", "moderate": "ปานกลาง", "aggressive": "รับความเสี่ยงได้สูง"},
        "goal_type": "ประเภทเป้าหมาย", "goal_name": "ชื่อเป้าหมาย", "target": "เงินที่ต้องการ คิดเป็นมูลค่าวันนี้ (฿)",
        "years": "อีกกี่ปีถึงเป้าหมาย", "current": "เงินที่เก็บไว้แล้วสำหรับเป้าหมายนี้ (฿)",
        "monthly": "เงินที่ตั้งใจออมต่อเดือน (฿)", "risk": "ระดับความเสี่ยงที่รับได้",
        "inflation": "เงินเฟ้อต่อปี (%)", "ret": "ผลตอบแทนที่คาดต่อปี (%)",
        "suggested": "พอร์ตแนะนำสำหรับ {y} ปี ความเสี่ยง{r}: ผลตอบแทนคาดประมาณ {p:.1f}% ต่อปี",
        "save": "บันทึกเป้าหมาย", "saved": "บันทึก “{n}” แล้ว", "need_name": "กรุณาตั้งชื่อเป้าหมาย",
        "no_goals": "ยังไม่มีเป้าหมาย เพิ่มได้ที่แท็บ “เพิ่มเป้าหมาย” หรือ “วางแผนเกษียณ” หรือโหลดเป้าหมายตัวอย่าง / ไฟล์ CSV ที่บันทึกไว้ในแท็บ “บันทึก / โหลดแผน”",
        "n_goals": "จำนวนเป้าหมาย", "total_target": "เป้าหมายรวม (มูลค่าอนาคต ฿)",
        "monthly_plan": "ออมตามแผนต่อเดือน", "monthly_need": "ต้องออมต่อเดือน",
        "col_name": "เป้าหมาย", "col_type": "ประเภท", "col_years": "ปี", "col_target": "เป้าหมาย (มูลค่าอนาคต ฿)",
        "col_proj": "คาดว่าจะมี (฿)", "col_need": "ต้องออม/เดือน", "col_plan": "ออมตามแผน/เดือน",
        "col_prog": "ความคืบหน้า", "col_status": "สถานะ",
        "on_track": "✅ ตามแผน", "behind": "⚠️ ยังไม่พอ",
        "detail": "รายละเอียด", "chart_x": "ปี", "chart_y": "จำนวนเงิน (฿)",
        "line_proj": "เงินออมที่คาดว่าจะมี", "line_target": "เป้าหมาย",
        "gap": "ต้องออม **฿{need:,.0f} ต่อเดือน** จึงจะถึงเป้า (ตอนนี้ตั้งใจออม ฿{plan:,.0f})",
        "ok": "แผนนี้ถึงเป้าหมาย และเหลือเกินมา ฿{extra:,.0f}",
        "alloc": "พอร์ตการลงทุนที่แนะนำ", "asset": "สินทรัพย์", "weight": "สัดส่วน (%)",
        "update_monthly": "แก้เงินออมต่อเดือน (฿)", "update": "อัปเดต", "delete": "ลบเป้าหมาย",
        "deleted": "ลบแล้ว",
        "assets": {"cash": "เงินฝาก / กองทุนตลาดเงิน", "bond": "ตราสารหนี้ไทย",
                   "th_eq": "หุ้นไทย", "gl_eq": "หุ้นต่างประเทศ"},
        "r_age": "อายุปัจจุบัน", "r_retire": "อายุที่จะเกษียณ", "r_life": "วางแผนให้เงินพอใช้ถึงอายุ",
        "r_exp": "ค่าใช้จ่ายต่อเดือนหลังเกษียณ คิดเป็นมูลค่าวันนี้ (฿)",
        "r_other": "เงินอื่นที่จะได้ตอนเกษียณ (บำนาญ, PVD) (฿)",
        "r_after": "ผลตอบแทนต่อปีหลังเกษียณ (%)",
        "r_result": "ต้องมีเงินประมาณ **฿{c:,.0f}** ตอนอายุ {a} ปี "
                    "(ค่าใช้จ่ายตอนนั้นจะเป็น ฿{m:,.0f} ต่อเดือน เพราะเงินเฟ้อ)",
        "r_bad_age": "อายุเกษียณต้องมากกว่าอายุปัจจุบัน และอายุที่วางแผนถึงต้องมากกว่าอายุเกษียณ",
        "r_tips": "ทางเลือกลดหย่อนภาษีเพื่อการเกษียณในไทย: กองทุนสำรองเลี้ยงชีพ (PVD), RMF, Thai ESG, "
                  "ประกันบำนาญ ตรวจสอบเพดานลดหย่อนปัจจุบันก่อนลงทุน",
        "r_name": "เกษียณอายุ {a} ปี",
        "data_info": "เป้าหมายเก็บไว้ในแท็บเบราว์เซอร์นี้เท่านั้น ถ้าปิดหรือรีเฟรชหน้าเว็บข้อมูลจะหายไป "
                     "จึงควรดาวน์โหลดไฟล์ CSV เก็บไว้ แล้วอัปโหลดกลับมาเมื่อต้องการใช้ต่อ",
        "session_info": "ไม่ต้อง login เป้าหมายอยู่ในแท็บเบราว์เซอร์นี้เท่านั้น คนอื่นมองไม่เห็น",
        "csv": "ดาวน์โหลดเป้าหมายของฉัน (CSV)", "upload": "อัปโหลดไฟล์ CSV เป้าหมายที่เคยบันทึกไว้",
        "load": "โหลดแผนนี้ (แทนที่เป้าหมายปัจจุบัน)", "example": "โหลดเป้าหมายตัวอย่าง",
        "bad_csv": "ไฟล์นี้ไม่ใช่ไฟล์ CSV เป้าหมายจากแอปนี้ ({e})",
    },
}

# ---------------------------------------------------------------- investment assumptions
# Expected yearly return of each asset class (teaching assumptions, not forecasts).
ASSET_RETURN = {"cash": 1.5, "bond": 2.5, "th_eq": 6.0, "gl_eq": 7.0}
# Portfolio weights (%) by time horizon and risk level.
ALLOCATION = {
    "short": {"conservative": [90, 10, 0, 0], "moderate": [70, 30, 0, 0], "aggressive": [50, 40, 5, 5]},
    "medium": {"conservative": [40, 50, 5, 5], "moderate": [20, 45, 15, 20], "aggressive": [10, 30, 25, 35]},
    "long": {"conservative": [10, 50, 20, 20], "moderate": [5, 30, 30, 35], "aggressive": [0, 15, 35, 50]},
}


def suggest_portfolio(years, risk):
    """Return (weights by asset, expected return %) for a goal horizon and risk level."""
    horizon = "short" if years <= 3 else "medium" if years <= 7 else "long"
    weights = dict(zip(ASSET_RETURN, ALLOCATION[horizon][risk]))
    expected = sum(weights[a] * ASSET_RETURN[a] for a in weights) / 100
    return weights, expected


# ---------------------------------------------------------------- finance formulas
def future_value(current, monthly, annual_return_pct, years):
    """Money after `years` from a lump sum plus a monthly deposit (end of each month)."""
    r, n = annual_return_pct / 100 / 12, round(years * 12)
    if r == 0:
        return current + monthly * n
    growth = (1 + r) ** n
    return current * growth + monthly * (growth - 1) / r


def monthly_needed(target_future, current, annual_return_pct, years):
    """Monthly deposit needed so that future_value(...) reaches target_future."""
    r, n = annual_return_pct / 100 / 12, max(round(years * 12), 1)
    growth = (1 + r) ** n
    gap = target_future - current * growth
    if gap <= 0:
        return 0.0
    return gap / n if r == 0 else gap * r / (growth - 1)


def retirement_corpus(monthly_expense_today, years_to_retire, years_in_retirement, inflation_pct, return_after_pct):
    """Money needed on retirement day to pay inflation-growing spending each year (paid at the start of the year)."""
    i, r = inflation_pct / 100, return_after_pct / 100
    first_year = monthly_expense_today * 12 * (1 + i) ** years_to_retire
    if abs(r - i) < 1e-9:
        return first_year * years_in_retirement, first_year / 12
    factor = (1 - ((1 + i) / (1 + r)) ** years_in_retirement) / (r - i) * (1 + r)
    return first_year * factor, first_year / 12


def goal_summary(g):
    """Add projected value, monthly need and progress to one goal row (a dict)."""
    target_future = g["target_amount"] * (1 + g["inflation"] / 100) ** g["years"]
    projected = future_value(g["current_saving"], g["monthly_saving"], g["expected_return"], g["years"])
    need = monthly_needed(target_future, g["current_saving"], g["expected_return"], g["years"])
    return {**g, "target_future": target_future, "projected": projected, "need": need,
            "progress": min(projected / target_future, 1.0) if target_future else 1.0,
            "on_track": projected >= target_future}


# ---------------------------------------------------------------- goal storage (no database)
# Goals live in st.session_state: they stay while the browser tab is open and are private to that tab.
# Users keep their plan by downloading it as CSV and uploading it again next time.
COLUMNS = ["id", "goal_type", "name", "target_amount", "years", "current_saving", "monthly_saving",
           "risk", "expected_return", "inflation", "details", "created_at"]
NUMBERS = ["target_amount", "years", "current_saving", "monthly_saving", "expected_return", "inflation"]


def load_goals():
    return st.session_state.setdefault("goals", [])


def add_goal(**goal):
    goals = load_goals()
    next_id = max((g["id"] for g in goals), default=0) + 1
    goals.append({**goal, "id": next_id, "details": json.dumps(goal.get("details") or {}),
                  "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})


def update_monthly(goal_id, monthly):
    for g in load_goals():
        if g["id"] == goal_id:
            g["monthly_saving"] = monthly


def delete_goal(goal_id):
    st.session_state["goals"] = [g for g in load_goals() if g["id"] != goal_id]


def goals_to_csv():
    return pd.DataFrame(load_goals(), columns=COLUMNS).to_csv(index=False).encode("utf-8-sig")


def goals_from_csv(file):
    """Read a CSV saved by goals_to_csv(); raise ValueError if it is not one."""
    df = pd.read_csv(file, encoding="utf-8-sig")
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(", ".join(sorted(missing)))
    df = df[COLUMNS].fillna({"details": "{}", "created_at": ""})
    df[NUMBERS] = df[NUMBERS].astype(float)
    if not df["goal_type"].isin(["retirement", "short", "long"]).all() or \
            not df["risk"].isin(["conservative", "moderate", "aggressive"]).all():
        raise ValueError("goal_type / risk")
    df["id"] = range(1, len(df) + 1)
    return df.to_dict("records")


def example_goals():
    """A few goals so a class demo does not start from an empty screen."""
    st.session_state["goals"] = []
    add_goal(goal_type="short", name="Emergency fund / เงินสำรองฉุกเฉิน", target_amount=90_000, years=1.5,
             current_saving=30_000, monthly_saving=3_500, risk="conservative", expected_return=1.6, inflation=2.0)
    add_goal(goal_type="long", name="House down payment / เงินดาวน์บ้าน", target_amount=600_000, years=7,
             current_saving=50_000, monthly_saving=5_000, risk="moderate", expected_return=3.9, inflation=2.0)
    corpus, _ = retirement_corpus(25_000, 30, 25, 2.0, 3.0)
    add_goal(goal_type="retirement", name="Retirement at 60 / เกษียณอายุ 60 ปี", target_amount=corpus, years=30,
             current_saving=100_000, monthly_saving=5_000, risk="moderate", expected_return=5.1, inflation=0.0)


# ---------------------------------------------------------------- sidebar: language
lang = st.sidebar.radio("ภาษา / Language", ["TH", "EN"], horizontal=True)
T = TEXT[lang]

st.title(T["title"])
st.caption(T["subtitle"])

with st.sidebar:
    st.info(T["session_info"])
    st.download_button(T["csv"], goals_to_csv(), "my_goals.csv", "text/csv", disabled=not load_goals())
    st.caption(T["note"])

money = lambda v: f"฿{v:,.0f}"  # noqa: E731
goals = [goal_summary(g) for g in load_goals()]
tab_dash, tab_add, tab_ret, tab_data = st.tabs([T["tab_dash"], T["tab_add"], T["tab_ret"], T["tab_data"]])

# ---------------------------------------------------------------- tab 1: dashboard
with tab_dash:
    if not goals:
        st.info(T["no_goals"])
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(T["n_goals"], len(goals))
        c2.metric(T["total_target"], money(sum(g["target_future"] for g in goals)))
        c3.metric(T["monthly_plan"], money(sum(g["monthly_saving"] for g in goals)))
        c4.metric(T["monthly_need"], money(sum(g["need"] for g in goals)))

        table = pd.DataFrame([{
            T["col_name"]: g["name"], T["col_type"]: T["types"][g["goal_type"]], T["col_years"]: g["years"],
            T["col_target"]: g["target_future"], T["col_proj"]: g["projected"],
            T["col_need"]: g["need"], T["col_plan"]: g["monthly_saving"], T["col_prog"]: g["progress"] * 100,
            T["col_status"]: T["on_track"] if g["on_track"] else T["behind"]} for g in goals])
        money_cols = [T["col_target"], T["col_proj"], T["col_need"], T["col_plan"]]
        st.dataframe(table, hide_index=True, width="stretch", column_config={
            **{c: st.column_config.NumberColumn(format="฿%,.0f") for c in money_cols},
            T["col_prog"]: st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100)})

        for g in goals:
            with st.expander(f"{T['types'][g['goal_type']]} · {g['name']} · {T['on_track'] if g['on_track'] else T['behind']}"):
                left, right = st.columns([3, 2])
                with left:
                    years = list(range(0, int(g["years"]) + 1))
                    if g["years"] > int(g["years"]):
                        years.append(g["years"])
                    chart_df = pd.DataFrame({
                        T["chart_x"]: years * 2,
                        T["chart_y"]: [future_value(g["current_saving"], g["monthly_saving"], g["expected_return"], y)
                                       for y in years] + [g["target_future"]] * len(years),
                        "line": [T["line_proj"]] * len(years) + [T["line_target"]] * len(years)})
                    st.altair_chart(alt.Chart(chart_df).mark_line(point=len(years) <= 15).encode(
                        x=alt.X(f"{T['chart_x']}:Q"), y=alt.Y(f"{T['chart_y']}:Q"),
                        color=alt.Color("line:N", title=None,
                                        scale=alt.Scale(range=["#00897E", "#E0652B"]))), width="stretch")
                    if g["on_track"]:
                        st.success(T["ok"].format(extra=g["projected"] - g["target_future"]))
                    else:
                        st.warning(T["gap"].format(need=g["need"], plan=g["monthly_saving"]))
                with right:
                    weights, _ = suggest_portfolio(g["years"], g["risk"])
                    st.markdown(f"**{T['alloc']}** ({T['risks'][g['risk']]}, {g['expected_return']:.1f}%)")
                    st.dataframe(pd.DataFrame({T["asset"]: [T["assets"][a] for a in weights],
                                               T["weight"]: list(weights.values())}),
                                 hide_index=True, width="stretch")
                    new_monthly = st.number_input(T["update_monthly"], min_value=0.0, step=500.0,
                                                  value=float(g["monthly_saving"]), key=f"m{g['id']}")
                    b1, b2 = st.columns(2)
                    if b1.button(T["update"], key=f"u{g['id']}"):
                        update_monthly(g["id"], new_monthly)
                        st.rerun()
                    if b2.button(T["delete"], key=f"d{g['id']}"):
                        delete_goal(g["id"])
                        st.rerun()

# ---------------------------------------------------------------- tab 2: add short / long-term goal
with tab_add:
    goal_type = st.radio(T["goal_type"], ["short", "long"], format_func=lambda k: T["types"][k],
                         horizontal=True, help=T["type_help"])
    c1, c2 = st.columns(2)
    name = c1.text_input(T["goal_name"], placeholder="Emergency fund / เงินสำรองฉุกเฉิน")
    target = c1.number_input(T["target"], min_value=0.0, value=100_000.0 if goal_type == "short" else 2_000_000.0,
                             step=10_000.0)
    years = c1.number_input(T["years"], min_value=0.5, max_value=3.0 if goal_type == "short" else 50.0,
                            value=2.0 if goal_type == "short" else 10.0, step=0.5)
    current = c2.number_input(T["current"], min_value=0.0, value=0.0, step=1_000.0)
    monthly = c2.number_input(T["monthly"], min_value=0.0, value=3_000.0, step=500.0)
    risk = c2.select_slider(T["risk"], options=list(T["risks"]), value="moderate", format_func=lambda k: T["risks"][k])
    weights, expected = suggest_portfolio(years, risk)
    st.caption(T["suggested"].format(y=years, r=T["risks"][risk], p=expected))
    c3, c4 = st.columns(2)
    exp_return = c3.number_input(T["ret"], min_value=0.0, max_value=15.0, value=round(expected, 1), step=0.1,
                                 key=f"ret_{years}_{risk}")
    inflation = c4.number_input(T["inflation"], min_value=0.0, max_value=10.0, value=2.0, step=0.1)

    preview = goal_summary({"target_amount": target, "years": years, "current_saving": current,
                            "monthly_saving": monthly, "expected_return": exp_return, "inflation": inflation})
    p1, p2, p3 = st.columns(3)
    p1.metric(T["col_target"], money(preview["target_future"]))
    p2.metric(T["col_proj"], money(preview["projected"]))
    p3.metric(T["col_need"], money(preview["need"]))

    if st.button(T["save"], type="primary"):
        if not name.strip():
            st.error(T["need_name"])
        else:
            add_goal(goal_type=goal_type, name=name.strip(), target_amount=target, years=years,
                     current_saving=current, monthly_saving=monthly, risk=risk,
                     expected_return=exp_return, inflation=inflation)
            st.success(T["saved"].format(n=name.strip()))
            st.rerun()

# ---------------------------------------------------------------- tab 3: retirement planner
with tab_ret:
    c1, c2, c3 = st.columns(3)
    age = c1.number_input(T["r_age"], min_value=18, max_value=80, value=30)
    retire_age = c2.number_input(T["r_retire"], min_value=40, max_value=85, value=60)
    life_age = c3.number_input(T["r_life"], min_value=60, max_value=110, value=85)
    c1, c2 = st.columns(2)
    expense = c1.number_input(T["r_exp"], min_value=0.0, value=25_000.0, step=1_000.0)
    other = c1.number_input(T["r_other"], min_value=0.0, value=0.0, step=50_000.0)
    r_current = c1.number_input(T["current"], min_value=0.0, value=100_000.0, step=10_000.0, key="r_cur")
    r_monthly = c2.number_input(T["monthly"], min_value=0.0, value=5_000.0, step=500.0, key="r_mon")
    r_infl = c2.number_input(T["inflation"], min_value=0.0, max_value=10.0, value=2.0, step=0.1, key="r_inf")
    r_after = c2.number_input(T["r_after"], min_value=0.0, max_value=10.0, value=3.0, step=0.1)

    if not age < retire_age < life_age:
        st.error(T["r_bad_age"])
    else:
        years_to = retire_age - age
        r_risk = st.select_slider(T["risk"], options=list(T["risks"]), value="moderate",
                                  format_func=lambda k: T["risks"][k], key="r_risk")
        _, r_expected = suggest_portfolio(years_to, r_risk)
        st.caption(T["suggested"].format(y=years_to, r=T["risks"][r_risk], p=r_expected))
        corpus, monthly_at_ret = retirement_corpus(expense, years_to, life_age - retire_age, r_infl, r_after)
        corpus = max(corpus - other, 0)
        st.markdown(T["r_result"].format(c=corpus, a=retire_age, m=monthly_at_ret))
        # Saved as a goal whose target is already in future money, so its inflation is 0.
        r_goal = goal_summary({"target_amount": corpus, "years": years_to, "current_saving": r_current,
                               "monthly_saving": r_monthly, "expected_return": r_expected, "inflation": 0.0})
        p1, p2, p3 = st.columns(3)
        p1.metric(T["col_proj"], money(r_goal["projected"]))
        p2.metric(T["col_need"], money(r_goal["need"]))
        p3.metric(T["col_status"], T["on_track"] if r_goal["on_track"] else T["behind"])
        st.info(T["r_tips"])
        if st.button(T["save"], type="primary", key="r_save"):
            add_goal(goal_type="retirement", name=T["r_name"].format(a=retire_age), target_amount=corpus,
                     years=years_to, current_saving=r_current, monthly_saving=r_monthly, risk=r_risk,
                     expected_return=r_expected, inflation=0.0,
                     details={"age": age, "retire_age": retire_age, "life_age": life_age,
                              "monthly_expense_today": expense, "inflation": r_infl, "return_after": r_after,
                              "other_money": other})
            st.success(T["saved"].format(n=T["r_name"].format(a=retire_age)))
            st.rerun()

# ---------------------------------------------------------------- tab 4: save / load the plan as CSV
with tab_data:
    st.markdown(T["data_info"])
    st.dataframe(pd.DataFrame(load_goals(), columns=COLUMNS), hide_index=True, width="stretch")
    c1, c2 = st.columns(2)
    c1.download_button(T["csv"], goals_to_csv(), "my_goals.csv", "text/csv", disabled=not load_goals(), key="csv2")
    if c2.button(T["example"]):
        example_goals()
        st.rerun()
    uploaded = st.file_uploader(T["upload"], type="csv")
    if uploaded is not None and st.button(T["load"], type="primary"):
        try:
            st.session_state["goals"] = goals_from_csv(uploaded)
            st.rerun()
        except Exception as err:  # wrong file, missing columns, bad values
            st.error(T["bad_csv"].format(e=err))
