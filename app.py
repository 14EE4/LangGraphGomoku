"""Streamlit을 사용한 오목 게임 UI"""

import os
import time

import streamlit as st

from ai_agent import GomokuAIAgent
from board_ui import (
    BOARD_IMAGE_PATH,
    BLACK_STONE_PATH,
    WHITE_STONE_PATH,
    display_board_interactive,
    load_or_create_assets,
)
from game import GomokuGame


st.set_page_config(
    page_title="오목 게임 🎮",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session():
    """세션 상태 초기화"""
    if "game" not in st.session_state:
        st.session_state.game = GomokuGame(19)
        st.session_state.ai_agent = GomokuAIAgent()
        st.session_state.winner = None
        st.session_state.game_over = False
        st.session_state.move_history_display = []
        st.session_state.ai_thinking = False
        st.session_state.assets = load_or_create_assets()


def handle_player_move(row: int, col: int):
    """플레이어의 수 처리"""
    game = st.session_state.game
    
    # 플레이어 수 배치
    success, winner = game.make_move(row, col, 1)
    
    if not success:
        st.error(f"❌ 유효하지 않은 수입니다! ({row}, {col})")
        return
    
    st.session_state.move_history_display.append(f"플레이어: ({row}, {col})")
    
    # 게임 종료 확인
    if winner:
        st.session_state.winner = 1
        st.session_state.game_over = True
        return
    
    # AI 수 계산
    st.session_state.ai_thinking = True
    st.rerun()


def get_ai_move():
    """AI의 최적 수 계산"""
    game = st.session_state.game
    
    valid_moves = game.get_valid_moves()
    if not valid_moves:
        st.session_state.game_over = True
        return None
    
    try:
        board_state = game.get_game_info()
        move, confidence, analysis = st.session_state.ai_agent.get_best_move(
            board_state["board"],
            board_state["board_size"],
            valid_moves
        )
        
        return move, confidence, analysis
    except Exception as e:
        st.error(f"❌ AI 오류: {str(e)}")
        return None


def display_game_info():
    """게임 정보 표시"""
    game = st.session_state.game
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("게임판 크기", f"{game.board_size}×{game.board_size}")
    
    with col2:
        st.metric("총 수 개수", len(game.move_history))
    
    with col3:
        valid_moves = len(game.get_valid_moves())
        st.metric("가능한 수", valid_moves)


def display_status():
    """게임 상태 표시"""
    if st.session_state.game_over:
        if st.session_state.winner == 1:
            st.success("🎉 **플레이어 승리!**", icon="✅")
        else:
            st.warning("🤖 **AI 승리!**", icon="⚠️")
    else:
        if st.session_state.ai_thinking:
            st.info("🤖 AI가 생각 중... 잠시만 기다려주세요")
        else:
            st.info("🎯 플레이어의 차례 - 행과 열을 선택하고 돌 놓기를 클릭하세요")


# ===== 애셋 업로드 인터페이스 =====
def show_asset_upload():
    """커스텀 이미지 업로드"""
    with st.expander("🎨 커스텀 이미지 업로드"):
        st.markdown("### 이미지 파일 준비")
        st.markdown("""
        다음 파일들을 준비해주세요:
        - `board.png`: 바둑판 배경 (나무 텍스처, 권장: 600×600px)
        - `black_stone.png`: 검은 돌 (투명 배경, 권장: 100×100px)
        - `white_stone.png`: 흰 돌 (투명 배경, 권장: 100×100px)
        
        그 다음 `assets` 폴더에 넣고 새로고침하세요.
        """)
        
        # 현재 에셋 상태 확인
        st.markdown("### 현재 에셋 상태")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if os.path.exists(BOARD_IMAGE_PATH):
                st.success("✅ board.png 로드됨")
            else:
                st.warning("⚠️ board.png 기본값 사용 중")
        
        with col2:
            if os.path.exists(BLACK_STONE_PATH):
                st.success("✅ black_stone.png 로드됨")
            else:
                st.warning("⚠️ black_stone.png 기본값 사용 중")
        
        with col3:
            if os.path.exists(WHITE_STONE_PATH):
                st.success("✅ white_stone.png 로드됨")
            else:
                st.warning("⚠️ white_stone.png 기본값 사용 중")
        
        # 재로드 버튼
        if st.button("🔄 에셋 다시 로드"):
            st.session_state.assets = load_or_create_assets()
            st.rerun()


def main():
    """메인 함수"""
    initialize_session()
    
    # 헤더
    st.title("🎮 오목 게임 vs AI")
    st.markdown("**LangGraph로 구현한 AI와 대전하는 오목 게임입니다.**")
    
    # 좌측 사이드바
    with st.sidebar:
        st.header("⚙️ 게임 설정")
        
        if st.button("🔄 새 게임 시작", use_container_width=True):
            st.session_state.game = GomokuGame(19)
            st.session_state.winner = None
            st.session_state.game_over = False
            st.session_state.move_history_display = []
            st.session_state.ai_thinking = False
            st.rerun()
        
        st.divider()
        
        st.subheader("📊 게임 통계")
        display_game_info()
        
        st.divider()
        
        st.subheader("📜 이동 히스토리")
        if st.session_state.move_history_display:
            for move in st.session_state.move_history_display:
                st.text(move)
        else:
            st.text("아직 수가 없습니다.")
        
        st.divider()
        show_asset_upload()
    
    # 메인 콘텐츠
    col_main, col_info = st.columns([3, 1])
    
    with col_main:
        st.subheader("게임판")
        display_status()
        display_board_interactive(
            st.session_state.game,
            st.session_state.assets,
            st.session_state.game_over,
            handle_player_move,
        )
    
    with col_info:
        st.subheader("ℹ️ 규칙")
        st.markdown("""
        **오목**
        - 5개의 자신의 돌을 먼저 연결하면 승리
        - 플레이어: ●(검은 돌)
        - AI: ○(흰 돌)
        
        **LangChain 기술**
        - Groq API 사용
        - openai/gpt-oss-20b 모델
        - LangGraph 워크플로우
        """)
    
    # AI 턴 처리
    if st.session_state.ai_thinking and not st.session_state.game_over:
        with st.spinner("🤖 AI가 최적의 수를 계산 중 (19×19)..."):
            time.sleep(1)  # UX 개선용
            result = get_ai_move()
            
            if result:
                move, confidence, analysis = result
                
                if move:
                    # AI 수 배치
                    row, col = move
                    success, winner = st.session_state.game.make_move(row, col, 2)
                    
                    if success:
                        st.session_state.move_history_display.append(
                            f"AI: ({row}, {col}) [신뢰도: {confidence:.1%}]"
                        )
                        
                        if winner:
                            st.session_state.winner = 2
                            st.session_state.game_over = True
        
        st.session_state.ai_thinking = False
        st.rerun()


if __name__ == "__main__":
    main()
