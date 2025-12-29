import streamlit as st
import datetime
import requests
import pandas as pd


GEMINI_API_KEY = "AIzaSyCLx1hnWhRB-G40-M8vUwMADJQ9mNb50O4" 


st.set_page_config(page_title="SMART KITCHEN", page_icon="🥗", layout="wide")


st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; }
    .stApp { background-color: #f8fafc; }
    h1 { color: #059669 !important; font-family: 'Inter', sans-serif; font-weight: 900 !important; }
    </style>
""", unsafe_allow_html=True)


def call_gemini(prompt, use_search=False):
    if not GEMINI_API_KEY or GEMINI_API_KEY == "你的_GEMINI_API_KEY_寫在這裡":
        st.error("❌ 尚未在程式碼中填入有效的 GEMINI_API_KEY")
        return None, []
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}] if use_search else []
    }
    
    try:
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        text = data['candidates'][0]['content']['parts'][0]['text']
        
        sources = []
        if use_search:
            grounding = data['candidates'][0].get('groundingMetadata', {}).get('groundingAttributions', [])
            for g in grounding:
                if 'web' in g:
                    sources.append({"title": g['web'].get('title', '參考連結'), "uri": g['web'].get('uri')})
        
        return text, sources
    except Exception as e:
        return f"AI 暫時無法回應: {str(e)}", []

# --- 資料初始化 ---
if 'ingredients' not in st.session_state:
    st.session_state.ingredients = []

# --- 主介面 ---
st.title("🥗 SMART KITCHEN")
st.markdown("##### 零浪費智慧廚房管理系統 (雲端同步版)")

# 第一區：新增食材表單
with st.container():
    st.markdown("### ➕ 新增至雲端庫存")
    c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 1])
    with c1: name = st.text_input("食材名稱", placeholder="雞蛋", key="in_name")
    with c2: p_date = st.date_input("購買日期", datetime.date.today())
    with c3: qty = st.number_input("數量", min_value=1, value=1)
    with c4: unit = st.text_input("單位", "顆")
    with c5: status = st.selectbox("狀態", ["冷藏", "冷凍", "常溫"])
    
    if st.button("確認新增", use_container_width=True):
        if name:
            with st.spinner("AI 生成保存建議中..."):
                prompt = f"食材：{name}，數量：{qty}{unit}，狀態：{status}。請提供一句話的專業保存建議。"
                advice, _ = call_gemini(prompt)
                
                if advice:
                    new_item = {
                        "id": str(datetime.datetime.now().timestamp()),
                        "name": name,
                        "date": p_date,
                        "qty": qty,
                        "unit": unit,
                        "status": status,
                        "advice": advice,
                        "selected": False
                    }
                    st.session_state.ingredients.append(new_item)
                    st.success(f"已新增 {name}！")
                    st.rerun()

st.divider()

# 第二區：清單顯示
st.subheader("🧊 目前庫存清單")

if not st.session_state.ingredients:
    st.info("目前冰箱是空的，快去買點東西吧！")
else:
    search = st.text_input("🔍 搜尋庫存...")
    
    for i, item in enumerate(st.session_state.ingredients):
        if search.lower() in item['name'].lower():
            with st.container():
                col_sel, col_main, col_ctrl, col_del = st.columns([0.5, 6, 2, 0.5])
                
                with col_sel:
                    item['selected'] = st.checkbox("", value=item['selected'], key=f"sel_{item['id']}")
                
                with col_main:
                    st.markdown(f"**{item['name']}** <span style='font-size:10px; background:#e2e8f0; padding:2px 8px; border-radius:10px;'>{item['status']}</span>", unsafe_allow_html=True)
                    days = (datetime.date.today() - item['date']).days
                    st.caption(f"📅 購買日期：{item['date']} (已存放 {days} 天)")
                    st.info(f"💡 AI 建議：{item['advice']}")
                
                with col_ctrl:
                    c_minus, c_val, c_plus = st.columns([1, 2, 1])
                    with c_minus:
                        if st.button("➖", key=f"minus_{item['id']}"):
                            item['qty'] = max(0, item['qty'] - 1)
                            st.rerun()
                    with c_val:
                        st.markdown(f"<p style='text-align:center; font-weight:bold; margin-top:5px;'>{item['qty']} {item['unit']}</p>", unsafe_allow_html=True)
                    with c_plus:
                        if st.button("➕", key=f"plus_{item['id']}"):
                            item['qty'] += 1
                            st.rerun()
                            
                with col_del:
                    if st.button("🗑️", key=f"del_{item['id']}"):
                        st.session_state.ingredients.pop(i)
                        st.rerun()
                st.divider()

# 第三區：食譜推薦
selected_names = [item['name'] for item in st.session_state.ingredients if item['selected']]

if selected_names:
    if st.button(f"👨‍🍳 根據這 {len(selected_names)} 樣食材生成食譜", use_container_width=True):
        with st.spinner("AI 正在搜尋網路食譜..."):
            prompt = f"我有以下食材：{'、'.join(selected_names)}。請搜尋網路提供三個真實食譜、做法與連結。"
            recipe_text, sources = call_gemini(prompt, use_search=True)
            
            if recipe_text:
                st.success("### 👨‍🍳 Gemini 嚴選食譜")
                st.markdown(recipe_text)
                
                if sources:
                    st.markdown("---")
                    st.caption("📖 參考來源")
                    for s in sources:
                        st.markdown(f"🔗 [{s['title']}]({s['uri']})")
