"""Goal-based financial planning website (ICT336 sample project).

Each user logs in and sees only their own goals (retirement, short-term, long-term).

Run locally:   streamlit run app.py            (SQLite file + demo login, no setup needed)
Deploy:        push this folder to GitHub, create an app on Streamlit Community Cloud,
               then paste the [auth] and [database] settings into the app's Secrets.
"""
import json
from datetime import datetime, timezone

import altair as alt
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Goal Planner", page_icon="💰", layout="wide")

# ---------------------------------------------------------------- text (EN / TH)
TEXT = {
    "EN": {
        "title": "💰 Goal-Based Financial Planner",
        "subtitle": "Plan your savings and investments for retirement, short-term and long-term goals.",
        "note": "Sample project for ICT336. Returns are assumptions for teaching, not investment advice.",
        "login_title": "Please log in", "login_google": "Log in with Google", "logout": "Log out",
        "login_info": "Your goals are stored under your email, so you only see your own plan.",
        "demo_title": "Demo login (no password)", "demo_email": "Email",
        "demo_btn": "Enter", "demo_warn": "Demo mode: Google login is not set up, so anyone can type any email. "
                                          "Use it only on your own computer.",
        "signed_in": "Signed in as", "db": "Database",
        "tab_dash": "My goals", "tab_add": "Add a goal", "tab_ret": "Retirement planner",
        "tab_data": "My data (database)",
        "types": {"retirement": "Retirement", "short": "Short-term", "long": "Long-term"},
        "type_help": "Short-term: within 3 years (trip, emergency fund). Long-term: more than 3 years (house, child's education).",
        "risks": {"conservative": "Conservative", "moderate": "Moderate", "aggressive": "Aggressive"},
        "goal_type": "Goal type", "goal_name": "Goal name", "target": "Target amount in today's money (฿)",
        "years": "Years until the goal", "current": "Money already saved for this goal (฿)",
        "monthly": "Monthly saving you plan to put in (฿)", "risk": "Risk you can accept",
        "inflation": "Inflation per year (%)", "ret": "Expected return per year (%)",
        "suggested": "Suggested portfolio for {y} years, {r} risk: expected return about {p:.1f}% per year",
        "save": "Save goal", "saved": "Saved “{n}”.", "need_name": "Please give the goal a name.",
        "no_goals": "You have no goals yet. Add one in the “Add a goal” tab or the Retirement planner.",
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
        "data_info": "These rows come from the database with `WHERE user_email = '{e}'`. "
                     "Another user running the same app sees only their own rows.",
        "csv": "Download my goals (CSV)",
    },
    "TH": {
        "title": "💰 วางแผนการเงินตามเป้าหมาย",
        "subtitle": "วางแผนการออมและการลงทุนสำหรับเกษียณ เป้าหมายระยะสั้น และเป้าหมายระยะยาว",
        "note": "โปรเจกต์ตัวอย่างวิชา ICT336 ผลตอบแทนเป็นสมมติฐานเพื่อการสอน ไม่ใช่คำแนะนำการลงทุน",
        "login_title": "กรุณาเข้าสู่ระบบ", "login_google": "เข้าสู่ระบบด้วย Google", "logout": "ออกจากระบบ",
        "login_info": "เป้าหมายจะเก็บแยกตามอีเมล แต่ละคนจึงเห็นเฉพาะแผนของตัวเอง",
        "demo_title": "เข้าสู่ระบบแบบทดลอง (ไม่มีรหัสผ่าน)", "demo_email": "อีเมล",
        "demo_btn": "เข้าใช้งาน", "demo_warn": "โหมดทดลอง: ยังไม่ได้ตั้งค่า Google login ใครก็พิมพ์อีเมลอะไรก็ได้ "
                                                "ใช้บนเครื่องตัวเองเท่านั้น",
        "signed_in": "เข้าสู่ระบบเป็น", "db": "ฐานข้อมูล",
        "tab_dash": "เป้าหมายของฉัน", "tab_add": "เพิ่มเป้าหมาย", "tab_ret": "วางแผนเกษียณ",
        "tab_data": "ข้อมูลของฉัน (ฐานข้อมูล)",
        "types": {"retirement": "เกษียณ", "short": "ระยะสั้น", "long": "ระยะยาว"},
        "type_help": "ระยะสั้น: ภายใน 3 ปี (ท่องเที่ยว เงินสำรองฉุกเฉิน) ระยะยาว: มากกว่า 3 ปี (ซื้อบ้าน การศึกษาลูก)",
        "risks": {"conservative": "รับความเสี่ยงได้ต่ำ", "moderate": "ปานกลาง", "aggressive": "รับความเสี่ยงได้สูง"},
        "goal_type": "ประเภทเป้าหมาย", "goal_name": "ชื่อเป้าหมาย", "target": "เงินที่ต้องการ คิดเป็นมูลค่าวันนี้ (฿)",
        "years": "อีกกี่ปีถึงเป้าหมาย", "current": "เงินที่เก็บไว้แล้วสำหรับเป้าหมายนี้ (฿)",
        "monthly": "เงินที่ตั้งใจออมต่อเดือน (฿)", "risk": "ระดับความเสี่ยงที่รับได้",
        "inflation": "เงินเฟ้อต่อปี (%)", "ret": "ผลตอบแทนที่คาดต่อปี (%)",
        "suggested": "พอร์ตแนะนำสำหรับ {y} ปี ความเสี่ยง{r}: ผลตอบแทนคาดประมาณ {p:.1f}% ต่อปี",
        "save": "บันทึกเป้าหมาย", "saved": "บันทึก “{n}” แล้ว", "need_name": "กรุณาตั้งชื่อเป้าหมาย",
        "no_goals": "ยังไม่มีเป้าหมาย เพิ่มได้ที่แท็บ “เพิ่มเป้าหมาย” หรือ “วางแผนเกษียณ”",
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
        "data_info": "แถวเหล่านี้ดึงจากฐานข้อมูลด้วย `WHERE user_email = '{e}'` "
                     "ผู้ใช้คนอื่นที่เปิดแอปเดียวกันจะเห็นเฉพาะแถวของตัวเอง",
        "csv": "ดาวน์โหลดเป้าหมายของฉัน (CSV)",
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


# ---------------------------------------------------------------- database
def get_secret(section):
    """Read one section of .streamlit/secrets.toml, or {} if there are no secrets."""
    try:
        return dict(st.secrets[section]) if section in st.secrets else {}
    except Exception:  # no secrets file at all
        return {}


@st.cache_resource
def get_engine():
    """SQLite file on this computer by default; Supabase/PostgreSQL when [database] url is in Secrets."""
    url = get_secret("database").get("url", "sqlite:///finance_goals.db")
    if url.startswith(("postgres://", "postgresql://")):  # Supabase gives this form; use the psycopg driver
        url = "postgresql+psycopg://" + url.split("://", 1)[1]
    engine = create_engine(url, pool_pre_ping=True)
    with engine.begin() as conn:
        id_col = "INTEGER PRIMARY KEY AUTOINCREMENT" if engine.dialect.name == "sqlite" else "SERIAL PRIMARY KEY"
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS goals (
                id {id_col},
                user_email TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                name TEXT NOT NULL,
                target_amount DOUBLE PRECISION NOT NULL,
                years DOUBLE PRECISION NOT NULL,
                current_saving DOUBLE PRECISION NOT NULL,
                monthly_saving DOUBLE PRECISION NOT NULL,
                risk TEXT NOT NULL,
                expected_return DOUBLE PRECISION NOT NULL,
                inflation DOUBLE PRECISION NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL
            )"""))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_goals_user ON goals (user_email)"))
    return engine


# Every query below includes user_email, so a user can never read or change someone else's goals.
def load_goals(email):
    with get_engine().connect() as conn:
        rows = conn.execute(text("SELECT * FROM goals WHERE user_email = :e ORDER BY id"), {"e": email})
        return [dict(r._mapping) for r in rows]


def add_goal(email, **goal):
    goal["details"] = json.dumps(goal.get("details") or {})
    with get_engine().begin() as conn:
        conn.execute(text("""
            INSERT INTO goals (user_email, goal_type, name, target_amount, years, current_saving,
                               monthly_saving, risk, expected_return, inflation, details, created_at)
            VALUES (:user_email, :goal_type, :name, :target_amount, :years, :current_saving,
                    :monthly_saving, :risk, :expected_return, :inflation, :details, :created_at)"""),
            {**goal, "user_email": email, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})


def update_monthly(email, goal_id, monthly):
    with get_engine().begin() as conn:
        conn.execute(text("UPDATE goals SET monthly_saving = :m WHERE id = :i AND user_email = :e"),
                     {"m": monthly, "i": goal_id, "e": email})


def delete_goal(email, goal_id):
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM goals WHERE id = :i AND user_email = :e"), {"i": goal_id, "e": email})


# ---------------------------------------------------------------- sidebar: language and login
lang = st.sidebar.radio("ภาษา / Language", ["TH", "EN"], horizontal=True)
T = TEXT[lang]
google_login = bool(get_secret("auth"))  # st.login() needs an [auth] section in Secrets


def current_user():
    """Return the logged-in user's email, or None."""
    if google_login:
        return st.user.get("email") if st.user.get("is_logged_in") else None
    return st.session_state.get("demo_email")


st.title(T["title"])
st.caption(T["subtitle"])

email = current_user()
if email is None:
    st.subheader(T["login_title"])
    st.write(T["login_info"])
    if google_login:
        st.button(T["login_google"], on_click=st.login, type="primary")
    else:
        st.warning(T["demo_warn"])
        with st.form("demo_login"):
            typed = st.text_input(T["demo_email"], placeholder="student@example.com")
            if st.form_submit_button(T["demo_btn"], type="primary") and "@" in typed:
                st.session_state["demo_email"] = typed.strip().lower()
                st.rerun()
    st.info(T["note"])
    st.stop()

with st.sidebar:
    st.write(f"{T['signed_in']} **{email}**")
    if google_login:
        st.button(T["logout"], on_click=st.logout)
    elif st.button(T["logout"]):
        del st.session_state["demo_email"]
        st.rerun()
    st.caption(f"{T['db']}: {get_engine().dialect.name}")
    st.caption(T["note"])

money = lambda v: f"฿{v:,.0f}"  # noqa: E731
goals = [goal_summary(g) for g in load_goals(email)]
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
                        update_monthly(email, g["id"], new_monthly)
                        st.rerun()
                    if b2.button(T["delete"], key=f"d{g['id']}"):
                        delete_goal(email, g["id"])
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
            add_goal(email, goal_type=goal_type, name=name.strip(), target_amount=target, years=years,
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
            add_goal(email, goal_type="retirement", name=T["r_name"].format(a=retire_age), target_amount=corpus,
                     years=years_to, current_saving=r_current, monthly_saving=r_monthly, risk=r_risk,
                     expected_return=r_expected, inflation=0.0,
                     details={"age": age, "retire_age": retire_age, "life_age": life_age,
                              "monthly_expense_today": expense, "inflation": r_infl, "return_after": r_after,
                              "other_money": other})
            st.success(T["saved"].format(n=T["r_name"].format(a=retire_age)))
            st.rerun()

# ---------------------------------------------------------------- tab 4: raw data (shows per-user filtering)
with tab_data:
    st.markdown(T["data_info"].format(e=email))
    raw = pd.DataFrame(load_goals(email))
    st.dataframe(raw, hide_index=True, width="stretch")
    if not raw.empty:
        st.download_button(T["csv"], raw.to_csv(index=False).encode("utf-8-sig"), "my_goals.csv", "text/csv")
