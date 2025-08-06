import streamlit as st

def analyst_page():

    st.title("📊 애널리스트 분석 의뢰")
    st.write("전문 애널리스트에게 원하는 종목의 심층 분석을 요청해 보세요.")

    if "analysis_requests" not in st.session_state:
        st.session_state.analysis_requests = {}
    
    # --- 관리자 전용 페이지 ---
    with st.expander("🛠️ 관리자 패널"):
        st.write("사용자의 분석 요청을 승인하고 분석 결과를 생성합니다.")
        
        # 현재 대기 중인(pending) 분석 요청만 필터링 해서 가져옴
        pending_requests = {
            uid: req for uid, req in st.session_state.analysis_requests.items()
            if req["status"] == "pending"
        }
        
        if not pending_requests:
            st.info("현재 대기 중인 분석 요청이 없습니다.")
        else:
            pending_user_ids = list(pending_requests.keys())
            selected_user_id = st.selectbox("승인할 사용자 선택", pending_user_ids)
            
            # 선택된 사용자의 요청 정보(종목, 투자 성향)
            request_info = pending_requests[selected_user_id]
            st.markdown(f"**사용자 ID:** {selected_user_id}")
            st.markdown(f"**요청 종목:** {request_info['request_data']['stock']}")
            st.markdown(f"**투자 성향:** {request_info['request_data']['style']}")
            st.markdown("---")

            if st.button(f"✅ {selected_user_id}의 요청 승인 및 분석 생성"):
                # 가상 분석 결과 생성
                stock_name = request_info['request_data']['stock']
                analysis_content = f"""
                ### **'{stock_name}' 심층 분석 보고서**

                **작성자:** 애널리스트A
                
                **분석 요약:**
                '{stock_name}'에 대한 요약
                
                **주요 투자 포인트:**
                - **기술력:** 
                - **시장 성장:** 
                
                **리스크 요인:**
                - **경쟁 심화:** 
                - **외부 환경:** 

                **결론:**
                '{stock_name}'에 대한 결론
                """
                
                # 해당 사용자의 요청 상태 "승인됨"으로 변경, 분석 결과 저장
                st.session_state.analysis_requests[selected_user_id]["status"] = "approved"
                st.session_state.analysis_requests[selected_user_id]["result"] = {
                    "content": analysis_content,
                    "cost": 50, # 예시 비용
                    "is_purchased": False
                }
                st.success(f"{selected_user_id}의 요청이 승인되고 분석이 생성되었습니다!")
                st.rerun()

    st.markdown("---")

    # --- 사용자 상태에 따른 페이지 분기 ---
    user_id = st.session_state.get("user_id")
    current_points = st.session_state.get("points", 0)
    user_request = st.session_state.analysis_requests.get(user_id)

    # 1. 분석 요청이 승인된 경우
    if user_request and user_request["status"] == "approved":
        st.subheader("✅ 분석 요청이 승인되었습니다!")
        st.write(f"요청하신 종목의 분석 결과가 도착했습니다. 포인트를 소모하여 열람해 보세요.")
        
        report = user_request["result"]
        
        st.info(f"💰 현재 보유 포인트: **{current_points}**점")
        
        # 이미 구매한 분석 결과인 경우
        if report["is_purchased"]:
            st.success("✅ 이미 열람한 분석 결과입니다.")
            if st.button("분석 결과 보기", key="view_approved_analysis"):
                st.markdown("---")
                st.markdown(report["content"])
        else:
            st.markdown(f"**열람 비용:** {report['cost']} 포인트")
            if st.button("결과 열람하기", key="buy_approved_analysis"):
                if current_points >= report["cost"]:
                    st.session_state.points -= report["cost"]
                    user_request["result"]["is_purchased"] = True
                    
                    st.success(f"🎉 **{report['cost']}** 포인트를 사용하고 분석 결과를 열람합니다!")
                    st.rerun()
                else:
                    st.error(f"포인트가 부족합니다! 분석 결과를 열람하려면 **{report['cost'] - current_points}** 포인트가 더 필요해요.")
    
    # 2. 분석 요청 후 승인 대기 중인 경우
    elif user_request and user_request["status"] == "pending":
        st.subheader("⏳ 분석 요청이 접수되었습니다.")
        st.info("애널리스트가 요청을 검토 중입니다. 잠시만 기다려 주세요.")
        
        request_info = user_request["request_data"]
        st.markdown("---")
        st.markdown(f"**요청 종목:** {request_info['stock']}")
        st.markdown(f"**투자 성향:** {request_info['style']}")
        st.markdown("---")

    # 3. 아직 분석 요청을 하지 않은 경우    
    else:
        st.subheader("📝 분석 요청하기")
        st.write("애널리스트에게 분석을 요청할 종목과 투자 성향을 알려주세요.")

        with st.form(key="analyst_request_form"):
            stock = st.text_input("분석을 요청할 종목 (예: 삼성전자, Apple)", help="종목명 또는 티커를 입력해 주세요.")
            style = st.selectbox(
                "선호하는 투자 성향",
                ["장기 투자 (가치주)", "단기 투자 (테마주)", "성장주 위주", "배당주 위주"],
                help="어떤 관점으로 분석하길 원하시나요?"
            )
            submit_button = st.form_submit_button("분석 요청하기")

            if submit_button:
                if not stock:
                    st.error("분석을 요청할 종목을 입력해 주세요.")
                else:
                    st.session_state.analysis_requests[user_id] = {
                        "status": "pending",
                        "request_data": {
                            "stock": stock,
                            "style": style
                        },
                        "result": None # 분석 결과는 나중에 생성
                    }
                    st.success(f"'{stock}' 종목에 대한 분석 요청이 완료되었습니다! 관리자의 검토를 기다려주세요.")
                    st.rerun()

