### 서브 콘텐츠 2: 커뮤니티 페이지

import streamlit as st
from datetime import date
import uuid

def community_page():
    st.title("📢 커뮤니티")

    # 로그인 상태 확인
    if 'user_id' not in st.session_state:
        st.warning("커뮤니티 기능은 로그인 후 이용할 수 있습니다.")
        return

    # 게시글 저장소 초기화
    if 'posts' not in st.session_state:
        st.session_state.posts = [] 

    # 작성 상태 변수 초기화
    if 'editing_post_id' not in st.session_state:
        st.session_state.editing_post_id = None

    # 게시글 검색
    search_query = st.text_input("🔍 게시글 검색", key="search_query")
    filtered_posts = [
        post for post in st.session_state.posts
        if search_query.lower() in post['title'].lower() or search_query.lower() in post['content'].lower()
    ] if search_query else st.session_state.posts

    # 최신 글이 위로 가도록
    filtered_posts = sorted(filtered_posts, key=lambda x: x['date'], reverse=True)

    st.subheader("📄 게시글 목록")
    if filtered_posts:
        for post in filtered_posts:
            with st.expander(post["title"]):
                st.markdown(f"✏️ **작성자:** {post['author']} | 🗓️ {post['date'].strftime('%Y-%m-%d')}")

                st.write(post["content"])

                # 신고 기능
                if st.button(f"🚨 신고하기 (현재 신고 수: {post['report_count']})", key=f"report_{post['id']}"):
                    post['report_count'] += 1
                    st.success("신고가 접수되었습니다.")

                # 수정/삭제는 작성자 본인만
                if st.session_state.user_id == post["author"]:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✏️ 수정", key=f"edit_{post['id']}"):
                            st.session_state.editing_post_id = post["id"]
                            st.rerun()
                    with col2:
                        if st.button("🗑️ 삭제", key=f"delete_{post['id']}"):
                            st.session_state.posts = [p for p in st.session_state.posts if p["id"] != post["id"]]
                            st.success("삭제되었습니다.")
                            st.rerun()
    else:
        st.info("표시할 게시글이 없습니다.")

    st.markdown("---")
    st.subheader("📝 게시글 작성")

    # 수정 중인지 확인
    editing_post = None
    if st.session_state.editing_post_id is not None:
        for post in st.session_state.posts:
            if post["id"] == st.session_state.editing_post_id:
                editing_post = post
                break

    if editing_post:
        title = st.text_input("제목", value=editing_post["title"], key="edit_title")
        content = st.text_area("내용", value=editing_post["content"], key="edit_content")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("수정 완료"):
                if title and content and len(content) <= 500:
                    editing_post["title"] = title
                    editing_post["content"] = content
                    editing_post["date"] = date.today()
                    st.session_state.editing_post_id = None
                    st.success("게시글이 수정되었습니다.")
                    st.rerun()
                elif len(content) > 500:
                    st.error("게시글 내용은 500자 이내로 작성해주세요")
                else:
                    st.error("제목과 내용을 모두 입력해주세요.")
        with col2:
            if st.button("수정 취소"):
                st.session_state.editing_post_id = None
                st.info("게시글 수정이 취소되었습니다.")
                st.rerun()
    else:
        title = st.text_input("제목", key="new_title")
        content = st.text_area("내용", key="new_content", max_chars=500)

        if st.button("등록"):
            if title and content and len(500) <= 500:
                st.session_state.posts.append({
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "content": content,
                    "author": st.session_state.user_id,
                    "date": date.today(),
                    "report_count": 0
                })
                st.success("게시글이 등록되었습니다.")
                st.rerun()
            elif len(content) > 500:
                st.error("게시글 내용은 500자 이내로 작성해주세요.")
            else:
                st.error("제목과 내용을 모두 입력해주세요.")