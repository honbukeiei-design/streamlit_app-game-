import streamlit as st
import pandas as pd
import random
import plotly.express as px
from datetime import date
from dateutil.relativedelta import relativedelta

# =====================================================
# 病院経営戦略ゲーム
# Streamlit app.py
# 単独プレイ / 仮想近隣病院対戦モード対応
# =====================================================

st.set_page_config(page_title="病院経営戦略ゲーム", layout="wide")

INITIAL_DATE = date(2026, 4, 1)

BASE_PARAMS = {
    "money": 50000,
    "staff": 120,
    "outpatients": 420,
    "inpatients": 160,
    "quality": 75,
    "reputation": 60,
    "dx": 25,
    "burnout": 10,
}

ENTITY_MODIFIERS = {
    "公立": {
        "money": 3000,
        "staff": 5,
        "reputation": 8,
        "dx": -2,
        "burnout": 2,
        "description": "地域医療・政策医療への期待が大きく、地域評価は高め。ただし意思決定や投資は慎重になりやすい。",
    },
    "公的": {
        "money": 1000,
        "staff": 3,
        "reputation": 5,
        "quality": 2,
        "description": "公共性と経営性のバランスが求められる。地域連携や医療の質で評価されやすい。",
    },
    "私立": {
        "money": -1000,
        "dx": 5,
        "reputation": -2,
        "burnout": 1,
        "description": "意思決定が比較的速く、DX投資に踏み切りやすい。一方で収益性への圧力が高い。",
    },
}

LOCATION_MODIFIERS = {
    "都市部": {
        "outpatients": 90,
        "inpatients": 20,
        "staff": 10,
        "money": 3500,
        "reputation": -2,
        "burnout": 5,
        "description": "患者数・職員数は多いが、競合病院も多く、待ち時間や職員負担が課題になりやすい。",
    },
    "都市近郊": {
        "outpatients": 40,
        "inpatients": 10,
        "money": 1500,
        "reputation": 2,
        "description": "都市部と地域医療の中間。紹介・逆紹介や救急受入のバランスが重要。",
    },
    "へき地": {
        "outpatients": -80,
        "inpatients": -25,
        "staff": -20,
        "money": -2500,
        "reputation": 10,
        "burnout": 8,
        "description": "地域唯一の医療資源として期待が大きい。人材確保・救急維持・広域連携が大きな課題。",
    },
}

CARE_MODIFIERS = {
    "急性期": {
        "outpatients": 40,
        "inpatients": 35,
        "staff": 12,
        "money": 2500,
        "quality": 2,
        "burnout": 8,
        "description": "救急・手術・DPC管理が重要。収益機会は大きいが、職員疲弊も起こりやすい。",
    },
    "亜急性期": {
        "inpatients": 15,
        "quality": 3,
        "reputation": 3,
        "burnout": 3,
        "description": "急性期後の受け皿として、地域連携と退院支援が重要。",
    },
    "回復期": {
        "outpatients": -20,
        "inpatients": 25,
        "quality": 4,
        "reputation": 4,
        "money": 500,
        "burnout": 1,
        "description": "リハビリ・在宅復帰・地域連携が中心。急性期病院との連携が鍵。",
    },
    "慢性期": {
        "outpatients": -40,
        "inpatients": 30,
        "staff": -5,
        "money": -500,
        "quality": 2,
        "burnout": -1,
        "description": "長期療養・生活支援が中心。医療・介護連携と人員配置が重要。",
    },
}

EVENTS = [
    {
        "id": "emergency_surge",
        "title": "救急搬送の急増",
        "description": "近隣医療機関の受入制限により、救急搬送が急増しました。地域からの期待は高まりますが、現場負担も増えています。",
        "effects": {"outpatients": 60, "inpatients": 12, "money": 1800, "quality": -3, "reputation": 5, "burnout": 12},
        "discussion": "救急受入を維持しながら、職員負担をどう抑えるかが論点です。",
    },
    {
        "id": "nurse_turnover",
        "title": "看護師の退職増加",
        "description": "夜勤負担と残業増加を背景に、看護師の退職が相次ぎました。病棟運営に影響が出始めています。",
        "effects": {"staff": -10, "quality": -5, "reputation": -3, "burnout": 10, "money": -800},
        "discussion": "採用だけでなく、業務負担の軽減や勤務環境改善が必要です。",
    },
    {
        "id": "fee_revision",
        "title": "診療報酬改定への対応",
        "description": "診療報酬改定により、一部の入院料・加算の要件が見直されました。収益構造の再点検が必要です。",
        "effects": {"money": -2200, "burnout": 3},
        "discussion": "加算取得、DPC分析、在院日数管理をどう進めるかが論点です。",
    },
    {
        "id": "infection_wave",
        "title": "感染症流行",
        "description": "地域で感染症が流行し、発熱外来と入院受入が増加しました。院内感染対策と通常診療の両立が求められます。",
        "effects": {"outpatients": 90, "inpatients": 18, "money": 2300, "quality": -4, "reputation": 4, "burnout": 16},
        "discussion": "短期的な患者増に対し、現場の持続可能性をどう守るかがポイントです。",
    },
    {
        "id": "regional_path",
        "title": "地域連携パスの改善機会",
        "description": "地域の診療所や介護施設から、退院調整や紹介受入のスピード改善を求める声が届いています。",
        "effects": {"outpatients": 10, "inpatients": 4, "money": 500, "quality": 2, "reputation": -2, "burnout": 2},
        "discussion": "地域連携を強化すれば、紹介率・逆紹介率・地域評価の向上が期待できます。",
    },
    {
        "id": "patient_waiting",
        "title": "患者満足度調査で待ち時間への不満",
        "description": "外来待ち時間、会計待ち、案内表示に関する不満が多く寄せられました。",
        "effects": {"outpatients": -15, "money": -700, "quality": -2, "reputation": -8, "burnout": 2},
        "discussion": "外来導線、予約枠、会計処理、案内表示の見直しが必要です。",
    },
    {
        "id": "dx_subsidy",
        "title": "医療DX補助金の公募開始",
        "description": "医療DX推進のための補助金公募が始まりました。申請できれば、システム投資の負担を抑えられます。",
        "effects": {"money": 1500, "dx": 3, "burnout": 1},
        "discussion": "短期的な申請負担と、中長期のDX効果をどう見極めるかが論点です。",
    },
    {
        "id": "dpc_overstay",
        "title": "DPC期間II超えが増加",
        "description": "一部疾患で平均在院日数が伸び、DPC上の収益性が悪化しています。退院支援・地域連携の強化が必要です。",
        "effects": {"inpatients": 6, "money": -1800, "quality": -1, "reputation": -2, "burnout": 5},
        "discussion": "医療の質を落とさず、在院日数と退院支援をどう最適化するかがポイントです。",
    },
    {
        "id": "doctor_recruitment",
        "title": "医師確保に成功",
        "description": "新たに医師を確保できました。診療体制は強化されますが、人件費負担も増加します。",
        "effects": {"staff": 8, "outpatients": 25, "inpatients": 5, "money": -1200, "quality": 7, "reputation": 5, "burnout": -3},
        "discussion": "診療体制強化をどう収益・地域貢献につなげるかが論点です。",
    },
    {
        "id": "disaster_training",
        "title": "災害対応訓練の必要性",
        "description": "県内で大規模災害を想定した医療提供体制の再確認が求められています。",
        "effects": {"money": -600, "quality": 2, "reputation": 4, "burnout": 2},
        "discussion": "短期的には負担ですが、地域医療を守る公的病院として重要なテーマです。",
    },
    {
        "id": "cyber_incident",
        "title": "サイバー攻撃訓練で脆弱性が判明",
        "description": "情報セキュリティ訓練で、端末管理やバックアップ体制に課題が見つかりました。",
        "effects": {"money": -900, "dx": -2, "quality": -1, "burnout": 3},
        "discussion": "医療DXを進めるほど、セキュリティと運用設計が重要になります。",
    },
    {
        "id": "ambulance_decline_news",
        "title": "救急受入困難事例が報道",
        "description": "救急受入困難事例が地域ニュースで取り上げられ、住民から不安の声が出ています。",
        "effects": {"reputation": -10, "outpatients": -10, "burnout": 4},
        "discussion": "救急体制、広報、地域連携を一体で考える必要があります。",
    },
    {
        "id": "aging_population",
        "title": "高齢患者の増加",
        "description": "地域の高齢化により、複数疾患を抱える患者や退院調整が難しい患者が増えています。",
        "effects": {"outpatients": 20, "inpatients": 15, "money": 1000, "quality": -2, "burnout": 8},
        "discussion": "急性期医療だけでなく、在宅・介護との連携が問われます。",
    },
    {
        "id": "student_pr",
        "title": "インターン体験がSNSで好評",
        "description": "病院経営DXインターンの内容が学生の間で話題になり、採用広報に追い風が生まれました。",
        "effects": {"reputation": 8, "staff": 3, "dx": 2, "money": 300},
        "discussion": "採用ブランディングは、将来の人材確保に直結します。",
    },
]

STRATEGIES = {
    "AI問診・カルテ要約の試行導入": {
        "category": "DX",
        "description": "外来前問診、紹介状要約、退院サマリ下書きなどを試行し、事務・医師の作業負担を軽減する。",
        "cost": 1800,
        "effects": {"money": -1800, "dx": 12, "quality": 3, "burnout": -5, "reputation": 2},
    },
    "RPAで月次集計・報告業務を自動化": {
        "category": "DX",
        "description": "経営指標、医事統計、会議資料作成の一部を自動化し、管理部門の作業時間を削減する。",
        "cost": 1200,
        "effects": {"money": -1200, "dx": 10, "burnout": -4, "quality": 1},
    },
    "外来待ち時間改善プロジェクト": {
        "category": "患者サービス",
        "description": "受付、診察、会計、薬局案内の流れを見直し、待ち時間と迷いやすさを減らす。",
        "cost": 900,
        "effects": {"money": -900, "outpatients": 15, "reputation": 10, "quality": 2, "burnout": -2},
    },
    "地域連携・紹介受入強化": {
        "category": "地域医療",
        "description": "診療所訪問、紹介窓口改善、返書管理により、紹介患者と地域評価を増やす。",
        "cost": 1000,
        "effects": {"money": -1000, "outpatients": 25, "inpatients": 6, "reputation": 12, "quality": 2},
    },
    "退院支援・在院日数適正化チーム": {
        "category": "DPC・病床運営",
        "description": "入退院支援、地域包括ケア、転院調整を強化し、DPC期間管理と病床回転を改善する。",
        "cost": 1300,
        "effects": {"money": 1600, "inpatients": -4, "quality": 3, "reputation": 4, "burnout": -3},
    },
    "看護補助者・事務補助の重点配置": {
        "category": "人材",
        "description": "看護師・医師が専門業務に集中できるよう、補助職種を重点配置する。",
        "cost": 2200,
        "effects": {"money": -2200, "staff": 8, "quality": 5, "burnout": -12, "reputation": 2},
    },
    "職員満足度向上・離職防止策": {
        "category": "人材",
        "description": "勤務表改善、面談、研修、心理的安全性の向上により、疲弊と離職を抑える。",
        "cost": 1500,
        "effects": {"money": -1500, "staff": 4, "quality": 3, "burnout": -15, "reputation": 1},
    },
    "救急受入体制の強化": {
        "category": "救急",
        "description": "救急導線、当直体制、病床確保ルールを整備し、救急受入件数を増やす。",
        "cost": 2000,
        "effects": {"money": 900, "outpatients": 35, "inpatients": 10, "reputation": 10, "burnout": 8, "quality": -1},
    },
    "病床再編・稼働率改善": {
        "category": "経営",
        "description": "病棟機能を見直し、急性期・回復期・地域包括ケアの役割分担を最適化する。",
        "cost": 1600,
        "effects": {"money": 2600, "inpatients": 8, "quality": 1, "reputation": -1, "burnout": 2},
    },
    "加算取得・施設基準点検": {
        "category": "医事・収益",
        "description": "算定可能な加算、施設基準、記録要件を点検し、取り漏れを減らす。",
        "cost": 800,
        "effects": {"money": 2800, "quality": 1, "burnout": 3, "dx": 2},
    },
    "診療材料・委託費の見直し": {
        "category": "経費",
        "description": "診療材料、委託費、保守契約を見直し、医療の質を維持しながらコストを抑える。",
        "cost": 0,
        "effects": {"money": 2200, "quality": -2, "reputation": -1, "burnout": 2},
    },
    "住民説明会・広報強化": {
        "category": "広報",
        "description": "地域住民へ病院の役割、医療体制、課題を説明し、信頼を高める。",
        "cost": 700,
        "effects": {"money": -700, "reputation": 13, "outpatients": 8, "quality": 1},
    },
    "災害・感染症対応訓練": {
        "category": "危機管理",
        "description": "BCP、感染対策、災害時受入、情報連絡体制を確認する。",
        "cost": 900,
        "effects": {"money": -900, "quality": 5, "reputation": 6, "burnout": 3},
    },
    "現状維持": {
        "category": "なし",
        "description": "大きな投資や改革は行わず、通常運営を継続する。",
        "cost": 0,
        "effects": {},
    },
}

NEIGHBOR_STRATEGY_NAMES = [
    "地域連携・紹介受入強化",
    "加算取得・施設基準点検",
    "外来待ち時間改善プロジェクト",
    "退院支援・在院日数適正化チーム",
    "職員満足度向上・離職防止策",
    "病床再編・稼働率改善",
    "現状維持",
]


def build_initial_params(entity, location, care):
    params = BASE_PARAMS.copy()
    for modifier in [ENTITY_MODIFIERS[entity], LOCATION_MODIFIERS[location], CARE_MODIFIERS[care]]:
        for key, value in modifier.items():
            if key != "description":
                params[key] = params.get(key, 0) + value

    for key in ["quality", "reputation", "dx", "burnout"]:
        params[key] = max(0, min(100, int(params[key])))

    params["staff"] = max(20, int(params["staff"]))
    params["outpatients"] = max(20, int(params["outpatients"]))
    params["inpatients"] = max(5, int(params["inpatients"]))
    params["money"] = max(5000, int(params["money"]))
    return params


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, int(value)))


def add_month(d):
    return d + relativedelta(months=1)


def calc_score_from_values(values):
    return int(
        values["money"] * 0.25
        + values["quality"] * 120
        + values["reputation"] * 100
        + values["dx"] * 70
        - values["burnout"] * 110
        + values["staff"] * 20
    )


def player_values():
    return {
        "money": st.session_state.money,
        "staff": st.session_state.staff,
        "outpatients": st.session_state.outpatients,
        "inpatients": st.session_state.inpatients,
        "quality": st.session_state.quality,
        "reputation": st.session_state.reputation,
        "dx": st.session_state.dx,
        "burnout": st.session_state.burnout,
    }


def make_score():
    return calc_score_from_values(player_values())


def pick_next_event():
    used_ids = set(st.session_state.get("used_event_ids", []))
    candidates = [event for event in EVENTS if event["id"] not in used_ids]
    if not candidates:
        st.session_state.used_event_ids = []
        candidates = EVENTS.copy()
    return random.choice(candidates)


def apply_effects_to_values(values, effects, multiplier=1.0):
    new_values = values.copy()
    for key, value in effects.items():
        new_values[key] = new_values.get(key, 0) + int(value * multiplier)
    for key in ["quality", "reputation", "dx", "burnout"]:
        new_values[key] = clamp(new_values[key])
    new_values["money"] = int(new_values["money"])
    new_values["staff"] = max(0, int(new_values["staff"]))
    new_values["outpatients"] = max(0, int(new_values["outpatients"]))
    new_values["inpatients"] = max(0, int(new_values["inpatients"]))
    return new_values


def natural_monthly_change_values(values):
    revenue = int(values["outpatients"] * 2.0 + values["inpatients"] * 9.0)
    staff_cost = int(values["staff"] * 4.2)
    burnout_loss = int(values["burnout"] * 8)
    quality_bonus = int((values["quality"] - 50) * 12)
    reputation_bonus = int((values["reputation"] - 50) * 8)
    monthly_profit = revenue - staff_cost - burnout_loss + quality_bonus + reputation_bonus
    values["money"] += monthly_profit
    values["money"] = int(values["money"])
    return values, monthly_profit


def apply_effects(effects):
    for key, value in effects.items():
        st.session_state[key] += value
    for key in ["quality", "reputation", "dx", "burnout"]:
        st.session_state[key] = clamp(st.session_state[key])


def natural_monthly_change():
    values, monthly_profit = natural_monthly_change_values(player_values())
    for key, value in values.items():
        setattr(st.session_state, key, value)
    return monthly_profit


def init_game_values(entity, location, care, game_mode):
    params = build_initial_params(entity, location, care)
    st.session_state.turn = 1
    st.session_state.current_date = INITIAL_DATE
    for key, value in params.items():
        st.session_state[key] = value

    st.session_state.history = []
    st.session_state.game_log = []
    st.session_state.used_event_ids = []
    st.session_state.current_event = pick_next_event()
    st.session_state.game_started = True
    st.session_state.entity = entity
    st.session_state.location = location
    st.session_state.care = care
    st.session_state.game_mode = game_mode
    st.session_state.strategy_picker = 0

    if game_mode == "仮想近隣病院と対戦":
        neighbor_params = build_initial_params("私立", location, care)
        neighbor_params["money"] += 1500
        neighbor_params["dx"] = clamp(neighbor_params["dx"] + 5)
        neighbor_params["reputation"] = clamp(neighbor_params["reputation"] + 2)
        neighbor_params["burnout"] = clamp(neighbor_params["burnout"] + 3)
        st.session_state.neighbor = neighbor_params
        st.session_state.neighbor_name = "近隣ライバル病院"
    else:
        st.session_state.neighbor = None
        st.session_state.neighbor_name = ""


def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def status_dataframe():
    rows = [
        {"項目": "年月日", "現在値": st.session_state.current_date.strftime("%Y年%m月%d日"), "補足": "1ターンごとに1か月経過"},
        {"項目": "モード", "現在値": st.session_state.game_mode, "補足": "単独運営または仮想近隣病院との対戦"},
        {"項目": "設立主体", "現在値": st.session_state.entity, "補足": ENTITY_MODIFIERS[st.session_state.entity]["description"]},
        {"項目": "設立場所", "現在値": st.session_state.location, "補足": LOCATION_MODIFIERS[st.session_state.location]["description"]},
        {"項目": "診療内容", "現在値": st.session_state.care, "補足": CARE_MODIFIERS[st.session_state.care]["description"]},
        {"項目": "外来患者数", "現在値": f"{st.session_state.outpatients:,} 名/月", "補足": "地域評価・救急・外来改善で変動"},
        {"項目": "入院患者数", "現在値": f"{st.session_state.inpatients:,} 名/月", "補足": "救急・地域連携・病床運営で変動"},
        {"項目": "資金", "現在値": f"{st.session_state.money:,} 万円", "補足": "月次収支・投資・イベントで変動"},
        {"項目": "職員数", "現在値": f"{st.session_state.staff:,} 名", "補足": "採用・退職・配置転換で変動"},
        {"項目": "DX指数", "現在値": f"{st.session_state.dx}/100", "補足": "デジタル活用の進み具合"},
        {"項目": "医療の質", "現在値": f"{st.session_state.quality}/100", "補足": "安全・質・継続性の総合指標"},
        {"項目": "地域評価", "現在値": f"{st.session_state.reputation}/100", "補足": "住民・診療所・行政からの信頼"},
        {"項目": "職員の疲弊度", "現在値": f"{st.session_state.burnout}/100", "補足": "高いほど離職・質低下リスク"},
    ]
    return pd.DataFrame(rows)


def selected_strategy_effects(selected):
    combined = {}
    for strategy_name in selected:
        for key, value in STRATEGIES[strategy_name]["effects"].items():
            combined[key] = combined.get(key, 0) + value
    return combined


def run_neighbor_turn(event):
    if st.session_state.neighbor is None:
        return None

    neighbor = st.session_state.neighbor.copy()

    # 近隣病院は状況に応じて1つ、まれに2つ戦略を選択
    choices = NEIGHBOR_STRATEGY_NAMES.copy()
    if neighbor["burnout"] > 55 and "職員満足度向上・離職防止策" in choices:
        selected = ["職員満足度向上・離職防止策"]
    elif neighbor["money"] < 25000:
        selected = ["加算取得・施設基準点検"]
    elif neighbor["reputation"] < 55:
        selected = ["外来待ち時間改善プロジェクト"]
    elif neighbor["dx"] < 45:
        selected = ["RPAで月次集計・報告業務を自動化"] if "RPAで月次集計・報告業務を自動化" in STRATEGIES else ["現状維持"]
    else:
        selected = [random.choice(choices)]

    if selected[0] != "現状維持" and random.random() < 0.35:
        second_candidates = [s for s in choices if s not in selected and s != "現状維持"]
        if second_candidates:
            selected.append(random.choice(second_candidates))

    neighbor = apply_effects_to_values(neighbor, event["effects"], multiplier=0.9)
    for s in selected:
        neighbor = apply_effects_to_values(neighbor, STRATEGIES[s]["effects"], multiplier=1.0)

    neighbor, profit = natural_monthly_change_values(neighbor)
    st.session_state.neighbor = neighbor

    return {
        "strategies": " / ".join(selected),
        "monthly_profit": profit,
        "score": calc_score_from_values(neighbor),
        **neighbor,
    }


def metric_card_cols(prefix, values, score):
    cols = st.columns(4)
    cols[0].metric(f"{prefix}外来患者数", f"{values['outpatients']:,} 名/月")
    cols[1].metric(f"{prefix}入院患者数", f"{values['inpatients']:,} 名/月")
    cols[2].metric(f"{prefix}資金", f"{values['money']:,} 万円")
    cols[3].metric(f"{prefix}総合スコア", f"{score:,}")


if "game_started" not in st.session_state:
    st.session_state.game_started = False

st.title("病院経営戦略ゲーム")
st.caption("未来の病院経営を体験するインターンシップ教材｜1ターン＝1か月")

if not st.session_state.game_started:
    st.header("初期設定")
    st.write("病院プロファイルとゲームモードを選択してください。選択内容に応じて初期パラメータが変わります。")

    mode = st.radio(
        "ゲームモード",
        ["単独で病院を経営", "仮想近隣病院と対戦"],
        horizontal=True,
    )

    if mode == "仮想近隣病院と対戦":
        st.info("目的：同じ地域にある仮想近隣病院よりも、最終的な経営状況を良くすることです。総合スコア、地域評価、医療の質、DX、職員疲弊度などで比較します。")
    else:
        st.info("目的：限られた資源の中で、地域医療・経営・職員負担・DXのバランスを取ることです。")

    c1, c2, c3 = st.columns(3)
    with c1:
        entity = st.selectbox("設立主体", ["公立", "公的", "私立"])
        st.info(ENTITY_MODIFIERS[entity]["description"])
    with c2:
        location = st.selectbox("設立場所", ["都市部", "都市近郊", "へき地"])
        st.info(LOCATION_MODIFIERS[location]["description"])
    with c3:
        care = st.selectbox("診療内容", ["急性期", "亜急性期", "回復期", "慢性期"])
        st.info(CARE_MODIFIERS[care]["description"])

    preview = build_initial_params(entity, location, care)
    preview_df = pd.DataFrame([
        {"項目": "資金", "初期値": f"{preview['money']:,} 万円"},
        {"項目": "職員数", "初期値": f"{preview['staff']:,} 名"},
        {"項目": "外来患者数", "初期値": f"{preview['outpatients']:,} 名/月"},
        {"項目": "入院患者数", "初期値": f"{preview['inpatients']:,} 名/月"},
        {"項目": "DX指数", "初期値": f"{preview['dx']}/100"},
        {"項目": "医療の質", "初期値": f"{preview['quality']}/100"},
        {"項目": "地域評価", "初期値": f"{preview['reputation']}/100"},
        {"項目": "職員の疲弊度", "初期値": f"{preview['burnout']}/100"},
    ])

    st.subheader("自院の初期ステータス")
    st.dataframe(preview_df, hide_index=True, use_container_width=True)

    if mode == "仮想近隣病院と対戦":
        neighbor_preview = build_initial_params("私立", location, care)
        neighbor_preview["money"] += 1500
        neighbor_preview["dx"] = clamp(neighbor_preview["dx"] + 5)
        neighbor_preview["reputation"] = clamp(neighbor_preview["reputation"] + 2)
        neighbor_preview["burnout"] = clamp(neighbor_preview["burnout"] + 3)
        neighbor_df = pd.DataFrame([
            {"項目": "資金", "初期値": f"{neighbor_preview['money']:,} 万円"},
            {"項目": "職員数", "初期値": f"{neighbor_preview['staff']:,} 名"},
            {"項目": "外来患者数", "初期値": f"{neighbor_preview['outpatients']:,} 名/月"},
            {"項目": "入院患者数", "初期値": f"{neighbor_preview['inpatients']:,} 名/月"},
            {"項目": "DX指数", "初期値": f"{neighbor_preview['dx']}/100"},
            {"項目": "医療の質", "初期値": f"{neighbor_preview['quality']}/100"},
            {"項目": "地域評価", "初期値": f"{neighbor_preview['reputation']}/100"},
            {"項目": "職員の疲弊度", "初期値": f"{neighbor_preview['burnout']}/100"},
        ])
        st.subheader("仮想近隣病院の初期ステータス")
        st.dataframe(neighbor_df, hide_index=True, use_container_width=True)

    if st.button("この設定でゲーム開始", type="primary"):
        init_game_values(entity, location, care, mode)
        st.rerun()

    st.stop()


with st.sidebar:
    st.header("ゲーム設定")
    max_turn = st.slider("総ターン数", 6, min(24, len(EVENTS)), min(12, len(EVENTS)))
    st.divider()
    st.write("### ゲームモード")
    st.write(f"**{st.session_state.game_mode}**")
    st.write("### 病院プロファイル")
    st.write(f"設立主体：**{st.session_state.entity}**")
    st.write(f"設立場所：**{st.session_state.location}**")
    st.write(f"診療内容：**{st.session_state.care}**")
    st.divider()
    st.write("### 進め方")
    st.markdown("1. 毎ターン、未発生の経営イベントが1つ発生\n2. チームで戦略を最大2つ選択\n3. 「ターン終了」で1か月進行\n4. 経営指標の変化を確認")
    st.divider()
    if st.button("ゲームを最初からやり直す"):
        reset_game()
        st.rerun()


current_date_text = st.session_state.current_date.strftime("%Y年%m月%d日")
st.subheader(f"現在の病院状況：{current_date_text}")

top1, top2 = st.columns([1.1, 1])

with top1:
    st.dataframe(status_dataframe(), hide_index=True, use_container_width=True)

with top2:
    gauge_df = pd.DataFrame({
        "指標": ["DX指数", "医療の質", "地域評価", "職員の疲弊度"],
        "値": [st.session_state.dx, st.session_state.quality, st.session_state.reputation, st.session_state.burnout],
    })
    fig = px.bar(gauge_df, x="指標", y="値", range_y=[0, 100], text="値", title="自院：主要スコア（100点満点）")
    fig.update_traces(texttemplate="%{text}/100", textposition="outside")
    st.plotly_chart(fig, use_container_width=True, key="top_player_scores")

metric_card_cols("", player_values(), make_score())

if st.session_state.game_mode == "仮想近隣病院と対戦":
    st.write("### 仮想近隣病院との比較")
    neighbor = st.session_state.neighbor
    metric_card_cols("近隣病院：", neighbor, calc_score_from_values(neighbor))

    compare_df = pd.DataFrame([
        {"指標": "資金", "自院": st.session_state.money, "近隣病院": neighbor["money"]},
        {"指標": "外来患者数", "自院": st.session_state.outpatients, "近隣病院": neighbor["outpatients"]},
        {"指標": "入院患者数", "自院": st.session_state.inpatients, "近隣病院": neighbor["inpatients"]},
        {"指標": "DX指数", "自院": st.session_state.dx, "近隣病院": neighbor["dx"]},
        {"指標": "医療の質", "自院": st.session_state.quality, "近隣病院": neighbor["quality"]},
        {"指標": "地域評価", "自院": st.session_state.reputation, "近隣病院": neighbor["reputation"]},
        {"指標": "職員疲弊度", "自院": st.session_state.burnout, "近隣病院": neighbor["burnout"]},
        {"指標": "総合スコア", "自院": make_score(), "近隣病院": calc_score_from_values(neighbor)},
    ])
    st.dataframe(compare_df, hide_index=True, use_container_width=True)

st.divider()

st.header(f"TURN {st.session_state.turn}：{current_date_text} の経営会議")
current_event = st.session_state.current_event

st.subheader("今月のイベント")

with st.container(border=True):
    st.write(f"### {current_event['title']}")
    st.write(current_event["description"])
    st.caption(current_event["discussion"])
    event_effect_df = pd.DataFrame([{"影響項目": key, "変化": value} for key, value in current_event["effects"].items()])
    st.write("#### イベントによる想定影響")
    st.dataframe(event_effect_df, hide_index=True, use_container_width=True)

st.subheader("戦略会議：今月実行する戦略を選択")
st.caption("最大2つまで選択できます。現状維持を選ぶ場合は、現状維持のみ選択してください。")

strategy_key = f"strategy_select_{st.session_state.strategy_picker}"
discussion_key = f"discussion_{st.session_state.strategy_picker}"

selected_strategies = st.multiselect(
    "戦略を選択",
    list(STRATEGIES.keys()),
    default=[],
    max_selections=2,
    key=strategy_key,
)

if "現状維持" in selected_strategies and len(selected_strategies) > 1:
    st.error("現状維持は単独で選択してください。他の戦略と同時には選べません。")

if selected_strategies:
    detail_rows = []
    for name in selected_strategies:
        strategy = STRATEGIES[name]
        detail_rows.append({"戦略": name, "分類": strategy["category"], "概要": strategy["description"], "概算費用": f"{strategy['cost']:,} 万円"})
    st.write("#### 選択中の戦略")
    st.dataframe(pd.DataFrame(detail_rows), hide_index=True, use_container_width=True)

    combined = selected_strategy_effects(selected_strategies)
    if combined:
        st.write("#### 選択戦略による想定影響")
        st.dataframe(pd.DataFrame([{"影響項目": key, "変化": value} for key, value in combined.items()]), hide_index=True, use_container_width=True)
else:
    st.info("戦略を選択してください。")

discussion = st.text_area(
    "チームの議論メモ",
    placeholder="例：救急受入は維持したいが、職員疲弊が高いため、救急強化と職員満足度向上を組み合わせる。",
    height=120,
    key=discussion_key,
)

can_end_turn = bool(selected_strategies) and not ("現状維持" in selected_strategies and len(selected_strategies) > 1)

if st.button("ターン終了：1か月進める", type="primary", disabled=not can_end_turn):
    event_before = current_event
    selected_before = selected_strategies.copy()
    discussion_before = discussion

    apply_effects(event_before["effects"])
    st.session_state.used_event_ids.append(event_before["id"])

    for strategy_name in selected_before:
        apply_effects(STRATEGIES[strategy_name]["effects"])

    monthly_profit = natural_monthly_change()

    st.session_state.money = int(st.session_state.money)
    st.session_state.staff = max(0, int(st.session_state.staff))
    st.session_state.outpatients = max(0, int(st.session_state.outpatients))
    st.session_state.inpatients = max(0, int(st.session_state.inpatients))

    neighbor_result = None
    if st.session_state.game_mode == "仮想近隣病院と対戦":
        neighbor_result = run_neighbor_turn(event_before)

    history_row = {
        "turn": st.session_state.turn,
        "date": current_date_text,
        "entity": st.session_state.entity,
        "location": st.session_state.location,
        "care": st.session_state.care,
        "money": st.session_state.money,
        "staff": st.session_state.staff,
        "outpatients": st.session_state.outpatients,
        "inpatients": st.session_state.inpatients,
        "quality": st.session_state.quality,
        "reputation": st.session_state.reputation,
        "dx": st.session_state.dx,
        "burnout": st.session_state.burnout,
        "event": event_before["title"],
        "strategies": " / ".join(selected_before),
        "discussion": discussion_before,
        "monthly_profit": monthly_profit,
        "score": make_score(),
    }

    if neighbor_result:
        history_row.update({
            "neighbor_money": neighbor_result["money"],
            "neighbor_staff": neighbor_result["staff"],
            "neighbor_outpatients": neighbor_result["outpatients"],
            "neighbor_inpatients": neighbor_result["inpatients"],
            "neighbor_quality": neighbor_result["quality"],
            "neighbor_reputation": neighbor_result["reputation"],
            "neighbor_dx": neighbor_result["dx"],
            "neighbor_burnout": neighbor_result["burnout"],
            "neighbor_strategies": neighbor_result["strategies"],
            "neighbor_monthly_profit": neighbor_result["monthly_profit"],
            "neighbor_score": neighbor_result["score"],
            "score_gap": make_score() - neighbor_result["score"],
        })

    st.session_state.history.append(history_row)

    st.session_state.game_log.append({
        "turn": st.session_state.turn,
        "date": current_date_text,
        "event": event_before["title"],
        "strategies": " / ".join(selected_before),
        "discussion": discussion_before,
        "monthly_profit": monthly_profit,
        "neighbor_strategies": neighbor_result["strategies"] if neighbor_result else "",
    })

    st.session_state.turn += 1
    st.session_state.current_date = add_month(st.session_state.current_date)
    st.session_state.current_event = pick_next_event()
    st.session_state.strategy_picker += 1

    st.rerun()

if st.session_state.history:
    st.divider()
    st.header("経営ダッシュボード・履歴一覧")

    df = pd.DataFrame(st.session_state.history)

    tabs = st.tabs(["資金", "患者数", "主要スコア", "疲弊度", "対戦比較", "履歴一覧", "まとめ出力", "経営コメント"])

    with tabs[0]:
        fig = px.line(df, x="date", y="money", markers=True, title="自院：資金推移（万円）")
        st.plotly_chart(fig, use_container_width=True, key="tab_money_player")
        if "neighbor_money" in df.columns:
            money_long = df.melt(id_vars=["date"], value_vars=["money", "neighbor_money"], var_name="病院", value_name="資金")
            money_long["病院"] = money_long["病院"].replace({"money": "自院", "neighbor_money": "近隣病院"})
            fig2 = px.line(money_long, x="date", y="資金", color="病院", markers=True, title="資金推移：自院 vs 近隣病院")
            st.plotly_chart(fig2, use_container_width=True, key="tab_money_compare")

    with tabs[1]:
        long_df = df.melt(id_vars=["date"], value_vars=["outpatients", "inpatients"], var_name="区分", value_name="患者数")
        long_df["区分"] = long_df["区分"].replace({"outpatients": "外来患者数", "inpatients": "入院患者数"})
        fig = px.line(long_df, x="date", y="患者数", color="区分", markers=True, title="自院：外来・入院患者数推移")
        st.plotly_chart(fig, use_container_width=True, key="tab_patients_player")

    with tabs[2]:
        score_long = df.melt(id_vars=["date"], value_vars=["quality", "reputation", "dx"], var_name="指標", value_name="値")
        score_long["指標"] = score_long["指標"].replace({"quality": "医療の質", "reputation": "地域評価", "dx": "DX指数"})
        fig = px.line(score_long, x="date", y="値", color="指標", markers=True, title="自院：主要スコア推移")
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, use_container_width=True, key="tab_score_player")

    with tabs[3]:
        fig = px.line(df, x="date", y="burnout", markers=True, title="自院：職員疲弊度推移")
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, use_container_width=True, key="tab_burnout_player")
        if "neighbor_burnout" in df.columns:
            burnout_long = df.melt(id_vars=["date"], value_vars=["burnout", "neighbor_burnout"], var_name="病院", value_name="疲弊度")
            burnout_long["病院"] = burnout_long["病院"].replace({"burnout": "自院", "neighbor_burnout": "近隣病院"})
            fig2 = px.line(burnout_long, x="date", y="疲弊度", color="病院", markers=True, title="職員疲弊度：自院 vs 近隣病院")
            fig2.update_yaxes(range=[0, 100])
            st.plotly_chart(fig2, use_container_width=True, key="tab_burnout_compare")

    with tabs[4]:
        if "neighbor_score" in df.columns:
            score_compare = df.melt(id_vars=["date"], value_vars=["score", "neighbor_score"], var_name="病院", value_name="総合スコア")
            score_compare["病院"] = score_compare["病院"].replace({"score": "自院", "neighbor_score": "近隣病院"})
            fig = px.line(score_compare, x="date", y="総合スコア", color="病院", markers=True, title="総合スコア：自院 vs 近隣病院")
            st.plotly_chart(fig, use_container_width=True, key="tab_compare_score")

            latest = df.iloc[-1]
            gap = int(latest["score_gap"])
            if gap >= 0:
                st.success(f"現在、自院が近隣病院を {gap:,} 点上回っています。")
            else:
                st.warning(f"現在、自院は近隣病院を {abs(gap):,} 点下回っています。")
        else:
            st.info("単独モードのため、対戦比較はありません。")

    with tabs[5]:
        display_df = df.copy()
        display_df = display_df.rename(columns={
            "turn": "ターン",
            "date": "年月日",
            "entity": "設立主体",
            "location": "設立場所",
            "care": "診療内容",
            "money": "資金",
            "staff": "職員数",
            "outpatients": "外来患者数",
            "inpatients": "入院患者数",
            "quality": "医療の質",
            "reputation": "地域評価",
            "dx": "DX指数",
            "burnout": "職員疲弊度",
            "event": "イベント",
            "strategies": "選択戦略",
            "discussion": "議論コメント",
            "monthly_profit": "月次自然収支",
            "score": "総合スコア",
            "neighbor_score": "近隣病院スコア",
            "neighbor_strategies": "近隣病院戦略",
            "score_gap": "スコア差",
        })
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        csv = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("履歴一覧CSVをダウンロード", data=csv, file_name="hospital_management_game_history.csv", mime="text/csv")

    with tabs[6]:
        st.write("### 出力用：履歴一覧とグラフ")
        st.caption("このタブをブラウザ印刷またはPDF保存すると、履歴一覧と各グラフをまとめて出力できます。")
        st.write("#### 履歴一覧")
        st.dataframe(df, hide_index=True, use_container_width=True)

        st.write("#### 資金推移")
        fig_out_money = px.line(df, x="date", y="money", markers=True, title="自院：資金推移（万円）")
        st.plotly_chart(fig_out_money, use_container_width=True, key="output_money_player")

        if "neighbor_money" in df.columns:
            money_long = df.melt(id_vars=["date"], value_vars=["money", "neighbor_money"], var_name="病院", value_name="資金")
            money_long["病院"] = money_long["病院"].replace({"money": "自院", "neighbor_money": "近隣病院"})
            fig_out_money_compare = px.line(money_long, x="date", y="資金", color="病院", markers=True, title="資金推移：自院 vs 近隣病院")
            st.plotly_chart(fig_out_money_compare, use_container_width=True, key="output_money_compare")

        st.write("#### 患者数推移")
        patient_long = df.melt(id_vars=["date"], value_vars=["outpatients", "inpatients"], var_name="区分", value_name="患者数")
        patient_long["区分"] = patient_long["区分"].replace({"outpatients": "外来患者数", "inpatients": "入院患者数"})
        fig_out_patient = px.line(patient_long, x="date", y="患者数", color="区分", markers=True, title="自院：外来・入院患者数推移")
        st.plotly_chart(fig_out_patient, use_container_width=True, key="output_patient_player")

        st.write("#### 主要スコア推移")
        score_long2 = df.melt(id_vars=["date"], value_vars=["quality", "reputation", "dx"], var_name="指標", value_name="値")
        score_long2["指標"] = score_long2["指標"].replace({"quality": "医療の質", "reputation": "地域評価", "dx": "DX指数"})
        score_fig = px.line(score_long2, x="date", y="値", color="指標", markers=True, title="自院：主要スコア推移")
        score_fig.update_yaxes(range=[0, 100])
        st.plotly_chart(score_fig, use_container_width=True, key="output_score_player")

        st.write("#### 職員疲弊度推移")
        fatigue_fig = px.line(df, x="date", y="burnout", markers=True, title="自院：職員疲弊度推移")
        fatigue_fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fatigue_fig, use_container_width=True, key="output_burnout_player")

        if "neighbor_score" in df.columns:
            st.write("#### 総合スコア対戦比較")
            score_compare = df.melt(id_vars=["date"], value_vars=["score", "neighbor_score"], var_name="病院", value_name="総合スコア")
            score_compare["病院"] = score_compare["病院"].replace({"score": "自院", "neighbor_score": "近隣病院"})
            compare_fig = px.line(score_compare, x="date", y="総合スコア", color="病院", markers=True, title="総合スコア：自院 vs 近隣病院")
            st.plotly_chart(compare_fig, use_container_width=True, key="output_compare_score")

    with tabs[7]:
        st.write("### 現在の経営コメント")
        if st.session_state.money < 15000:
            st.error("資金がかなり厳しい状態です。収益改善・費用見直し・加算取得を検討してください。")
        elif st.session_state.money > 65000:
            st.success("資金には余裕があります。将来投資や人材投資を検討できます。")
        else:
            st.info("資金は一定程度維持されています。投資と収益改善のバランスが重要です。")

        if st.session_state.burnout >= 75:
            st.error("職員の疲弊度が危険水準です。離職、医療の質低下、事故リスクに注意してください。")
        elif st.session_state.burnout >= 50:
            st.warning("職員の疲弊が高まっています。業務改善や人材投資を検討してください。")
        else:
            st.success("職員疲弊は比較的抑えられています。")

        if st.session_state.game_mode == "仮想近隣病院と対戦" and st.session_state.history:
            latest = pd.DataFrame(st.session_state.history).iloc[-1]
            if latest["score_gap"] >= 0:
                st.success("近隣病院よりも良い経営状態です。この優位を維持しましょう。")
            else:
                st.warning("近隣病院よりも総合スコアが低い状態です。差が出ている指標を確認しましょう。")

if st.session_state.turn > max_turn:
    st.divider()
    st.header("ゲーム終了")
    final_score = make_score()
    st.metric("自院：最終総合スコア", f"{final_score:,}")

    if st.session_state.game_mode == "仮想近隣病院と対戦":
        neighbor_score = calc_score_from_values(st.session_state.neighbor)
        st.metric("近隣病院：最終総合スコア", f"{neighbor_score:,}")
        if final_score > neighbor_score:
            st.success("勝利：近隣病院よりも良い経営状態を実現しました。")
        elif final_score == neighbor_score:
            st.info("引き分け：近隣病院と同水準の経営状態です。")
        else:
            st.error("敗北：近隣病院の方が良い経営状態です。どの指標で差がついたか振り返りましょう。")
    else:
        if final_score >= 65000:
            st.success("非常に優秀な病院経営です。地域医療、医療の質、職員負担、DXのバランスが取れています。")
        elif final_score >= 45000:
            st.info("安定した病院経営です。一部に改善余地はありますが、持続可能性があります。")
        else:
            st.error("経営改善が必要です。資金、職員疲弊、医療の質、地域評価のどこに課題があるか振り返りましょう。")

    st.write("### 最終ステータス")
    st.dataframe(status_dataframe(), hide_index=True, use_container_width=True)

st.divider()

with st.expander("ゲームログ"):
    if st.session_state.game_log:
        for log in reversed(st.session_state.game_log):
            st.write(f"### TURN {log['turn']}：{log['date']}")
            st.write(f"**イベント：** {log['event']}")
            st.write(f"**選択戦略：** {log['strategies']}")
            if log.get("neighbor_strategies"):
                st.write(f"**近隣病院の戦略：** {log['neighbor_strategies']}")
            st.write(f"**月次自然収支：** {log['monthly_profit']:,} 万円")
            if log["discussion"]:
                st.write(f"**議論メモ：** {log['discussion']}")
            st.divider()
    else:
        st.caption("まだログはありません。")
