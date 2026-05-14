import streamlit as st
import pandas as pd
import random
import plotly.express as px
from datetime import date
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="病院経営戦略ゲーム", layout="wide")

INITIAL_DATE = date(2026, 4, 1)

EVENTS = [
    {
        "title": "救急搬送の急増",
        "description": "近隣医療機関の受入制限により、救急搬送が急増しました。地域からの期待は高まりますが、現場負担も増えています。",
        "effects": {"outpatients": 60, "inpatients": 12, "money": 1800, "quality": -3, "reputation": 5, "burnout": 12},
        "discussion": "救急受入を維持しながら、職員負担をどう抑えるかが論点です。",
    },
    {
        "title": "看護師の退職増加",
        "description": "夜勤負担と残業増加を背景に、看護師の退職が相次ぎました。病棟運営に影響が出始めています。",
        "effects": {"staff": -10, "quality": -5, "reputation": -3, "burnout": 10, "money": -800},
        "discussion": "採用だけでなく、業務負担の軽減や勤務環境改善が必要です。",
    },
    {
        "title": "診療報酬改定への対応",
        "description": "診療報酬改定により、一部の入院料・加算の要件が見直されました。収益構造の再点検が必要です。",
        "effects": {"money": -2200, "burnout": 3},
        "discussion": "加算取得、DPC分析、在院日数管理をどう進めるかが論点です。",
    },
    {
        "title": "感染症流行",
        "description": "地域で感染症が流行し、発熱外来と入院受入が増加しました。院内感染対策と通常診療の両立が求められます。",
        "effects": {"outpatients": 90, "inpatients": 18, "money": 2300, "quality": -4, "reputation": 4, "burnout": 16},
        "discussion": "短期的な患者増に対し、現場の持続可能性をどう守るかがポイントです。",
    },
    {
        "title": "地域連携パスの改善機会",
        "description": "地域の診療所や介護施設から、退院調整や紹介受入のスピード改善を求める声が届いています。",
        "effects": {"outpatients": 10, "inpatients": 4, "money": 500, "quality": 2, "reputation": -2, "burnout": 2},
        "discussion": "地域連携を強化すれば、紹介率・逆紹介率・地域評価の向上が期待できます。",
    },
    {
        "title": "患者満足度調査で待ち時間への不満",
        "description": "外来待ち時間、会計待ち、案内表示に関する不満が多く寄せられました。",
        "effects": {"outpatients": -15, "money": -700, "quality": -2, "reputation": -8, "burnout": 2},
        "discussion": "外来導線、予約枠、会計処理、案内表示の見直しが必要です。",
    },
    {
        "title": "医療DX補助金の公募開始",
        "description": "医療DX推進のための補助金公募が始まりました。申請できれば、システム投資の負担を抑えられます。",
        "effects": {"money": 1500, "dx": 3, "burnout": 1},
        "discussion": "短期的な申請負担と、中長期のDX効果をどう見極めるかが論点です。",
    },
    {
        "title": "DPC期間II超えが増加",
        "description": "一部疾患で平均在院日数が伸び、DPC上の収益性が悪化しています。退院支援・地域連携の強化が必要です。",
        "effects": {"inpatients": 6, "money": -1800, "quality": -1, "reputation": -2, "burnout": 5},
        "discussion": "医療の質を落とさず、在院日数と退院支援をどう最適化するかがポイントです。",
    },
    {
        "title": "医師確保に成功",
        "description": "新たに医師を確保できました。診療体制は強化されますが、人件費負担も増加します。",
        "effects": {"staff": 8, "outpatients": 25, "inpatients": 5, "money": -1200, "quality": 7, "reputation": 5, "burnout": -3},
        "discussion": "診療体制強化をどう収益・地域貢献につなげるかが論点です。",
    },
    {
        "title": "災害対応訓練の必要性",
        "description": "県内で大規模災害を想定した医療提供体制の再確認が求められています。",
        "effects": {"money": -600, "quality": 2, "reputation": 4, "burnout": 2},
        "discussion": "短期的には負担ですが、地域医療を守る公的病院として重要なテーマです。",
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

def init_game():
    defaults = {
        "turn": 1,
        "current_date": INITIAL_DATE,
        "money": 50000,
        "staff": 120,
        "outpatients": 420,
        "inpatients": 160,
        "quality": 75,
        "reputation": 60,
        "dx": 25,
        "burnout": 10,
        "history": [],
        "game_log": [],
        "current_event": random.choice(EVENTS),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_game()

def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, int(value)))

def add_month(d):
    return d + relativedelta(months=1)

def apply_effects(effects):
    for key, value in effects.items():
        st.session_state[key] += value
    for key in ["quality", "reputation", "dx", "burnout"]:
        st.session_state[key] = clamp(st.session_state[key])

def natural_monthly_change():
    revenue = int(st.session_state.outpatients * 2.0 + st.session_state.inpatients * 9.0)
    staff_cost = int(st.session_state.staff * 4.2)
    burnout_loss = int(st.session_state.burnout * 8)
    quality_bonus = int((st.session_state.quality - 50) * 12)
    reputation_bonus = int((st.session_state.reputation - 50) * 8)
    monthly_profit = revenue - staff_cost - burnout_loss + quality_bonus + reputation_bonus
    st.session_state.money += monthly_profit
    return monthly_profit

def status_dataframe():
    return pd.DataFrame([
        {"項目": "年月日", "現在値": st.session_state.current_date.strftime("%Y年%m月%d日"), "補足": "1ターンごとに1か月経過"},
        {"項目": "外来患者数", "現在値": f"{st.session_state.outpatients:,} 名/月", "補足": "地域評価・救急・外来改善で変動"},
        {"項目": "入院患者数", "現在値": f"{st.session_state.inpatients:,} 名/月", "補足": "救急・地域連携・病床運営で変動"},
        {"項目": "資金", "現在値": f"{st.session_state.money:,} 万円", "補足": "月次収支・投資・イベントで変動"},
        {"項目": "職員数", "現在値": f"{st.session_state.staff:,} 名", "補足": "採用・退職・配置転換で変動"},
        {"項目": "DX指数", "現在値": f"{st.session_state.dx}/100", "補足": "デジタル活用の進み具合"},
        {"項目": "医療の質", "現在値": f"{st.session_state.quality}/100", "補足": "安全・質・継続性の総合指標"},
        {"項目": "地域評価", "現在値": f"{st.session_state.reputation}/100", "補足": "住民・診療所・行政からの信頼"},
        {"項目": "職員の疲弊度", "現在値": f"{st.session_state.burnout}/100", "補足": "高いほど離職・質低下リスク"},
    ])

def make_score():
    return int(
        st.session_state.money * 0.25
        + st.session_state.quality * 120
        + st.session_state.reputation * 100
        + st.session_state.dx * 70
        - st.session_state.burnout * 110
        + st.session_state.staff * 20
    )

def selected_strategy_effects(selected):
    combined = {}
    for strategy_name in selected:
        for key, value in STRATEGIES[strategy_name]["effects"].items():
            combined[key] = combined.get(key, 0) + value
    return combined

init_game()

st.title("病院経営戦略ゲーム")
st.caption("未来の病院経営を体験するインターンシップ教材｜1ターン＝1か月")

with st.sidebar:
    st.header("ゲーム設定")
    max_turn = st.slider("総ターン数", 6, 24, 12)
    st.divider()
    st.write("### 進め方")
    st.markdown("1. 毎ターン、1つの経営イベントが発生\n2. チームで戦略を最大2つ選択\n3. 「ターン終了」で1か月進行\n4. 経営指標の変化を確認")
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
    fig = px.bar(gauge_df, x="指標", y="値", range_y=[0, 100], text="値", title="主要スコア（100点満点）")
    fig.update_traces(texttemplate="%{text}/100", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

metric_cols = st.columns(4)
metric_cols[0].metric("外来患者数", f"{st.session_state.outpatients:,} 名/月")
metric_cols[1].metric("入院患者数", f"{st.session_state.inpatients:,} 名/月")
metric_cols[2].metric("資金", f"{st.session_state.money:,} 万円")
metric_cols[3].metric("総合スコア", f"{make_score():,}")

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

selected_strategies = st.multiselect("戦略を選択", list(STRATEGIES.keys()), default=[], max_selections=2)

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

discussion = st.text_area("チームの議論メモ", placeholder="例：救急受入は維持したいが、職員疲弊が高いため、救急強化と職員満足度向上を組み合わせる。", height=120)

can_end_turn = bool(selected_strategies) and not ("現状維持" in selected_strategies and len(selected_strategies) > 1)

if st.button("ターン終了：1か月進める", type="primary", disabled=not can_end_turn):
    event_before = current_event
    selected_before = selected_strategies.copy()

    apply_effects(event_before["effects"])
    for strategy_name in selected_before:
        apply_effects(STRATEGIES[strategy_name]["effects"])

    monthly_profit = natural_monthly_change()

    st.session_state.money = int(st.session_state.money)
    st.session_state.staff = max(0, int(st.session_state.staff))
    st.session_state.outpatients = max(0, int(st.session_state.outpatients))
    st.session_state.inpatients = max(0, int(st.session_state.inpatients))

    st.session_state.history.append({
        "turn": st.session_state.turn,
        "date": current_date_text,
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
        "monthly_profit": monthly_profit,
        "score": make_score(),
    })

    st.session_state.game_log.append({
        "turn": st.session_state.turn,
        "date": current_date_text,
        "event": event_before["title"],
        "strategies": " / ".join(selected_before),
        "discussion": discussion,
        "monthly_profit": monthly_profit,
    })

    st.session_state.turn += 1
    st.session_state.current_date = add_month(st.session_state.current_date)
    st.session_state.current_event = random.choice(EVENTS)
    st.rerun()

if st.session_state.history:
    st.divider()
    st.header("経営ダッシュボード")

    df = pd.DataFrame(st.session_state.history)
    tabs = st.tabs(["資金", "患者数", "主要スコア", "疲弊度", "履歴一覧", "経営コメント"])

    with tabs[0]:
        fig = px.line(df, x="date", y="money", markers=True, title="資金推移（万円）")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        long_df = df.melt(id_vars=["date"], value_vars=["outpatients", "inpatients"], var_name="区分", value_name="患者数")
        long_df["区分"] = long_df["区分"].replace({"outpatients": "外来患者数", "inpatients": "入院患者数"})
        fig = px.line(long_df, x="date", y="患者数", color="区分", markers=True, title="外来・入院患者数推移")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        score_long = df.melt(id_vars=["date"], value_vars=["quality", "reputation", "dx"], var_name="指標", value_name="値")
        score_long["指標"] = score_long["指標"].replace({"quality": "医療の質", "reputation": "地域評価", "dx": "DX指数"})
        fig = px.line(score_long, x="date", y="値", color="指標", markers=True, title="主要スコア推移")
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        fig = px.line(df, x="date", y="burnout", markers=True, title="職員の疲弊度推移")
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

    with tabs[4]:
        st.dataframe(df, hide_index=True, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("履歴CSVをダウンロード", data=csv, file_name="hospital_management_game_history.csv", mime="text/csv")

    with tabs[5]:
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

        if st.session_state.quality < 50:
            st.error("医療の質が低下しています。安全・教育・現場支援の施策が必要です。")
        elif st.session_state.quality >= 80:
            st.success("医療の質は高い状態です。地域への発信や紹介受入強化につなげられます。")

        if st.session_state.dx >= 75:
            st.success("DX先進病院として評価される水準です。採用広報にも活用できます。")
        elif st.session_state.dx < 35:
            st.warning("DX指数が低めです。小さな自動化やAI活用から始める余地があります。")

if st.session_state.turn > max_turn:
    st.divider()
    st.header("ゲーム終了")
    final_score = make_score()
    st.metric("最終総合スコア", f"{final_score:,}")

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
            st.write(f"**月次自然収支：** {log['monthly_profit']:,} 万円")
            if log["discussion"]:
                st.write(f"**議論メモ：** {log['discussion']}")
            st.divider()
    else:
        st.caption("まだログはありません。")
