"""
Streamlit을 사용한 오목 게임 UI
- 인터랙티브 게임판 표시
- 플레이어 입력 처리
- AI 수 계산 및 표시
"""

import streamlit as st
from game import GomokuGame
from ai_agent import GomokuAIAgent
import time
from typing import Optional


# 페이지 설정
st.set_page_config(
    page_title="오목 게임 🎮",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
    <style>
    .board-cell {
        width: 40px;
        height: 40px;
        display: inline-block;
        border: 1px solid #ccc;
        text-align: center;
        line-height: 40px;
        cursor: pointer;
    }
    .board-cell:hover {
        background-color: #f0f0f0;
    }
    .player-stone {
        color: black;
        font-weight: bold;
    }
    .ai-stone {
        color: white;
        background-color: black;
        font-weight: bold;
    }
    .status-box {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .status-waiting {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
    }
    .status-player {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .status-ai {
        background-color: #fce4ec;
        border-left: 4px solid #e91e63;
    }
    .status-win {
        background-color: #c8e6c9;
        border-left: 4px solid #4caf50;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_session():
    """세션 상태 초기화"""
    if "game" not in st.session_state:
        st.session_state.game = GomokuGame(15)
        st.session_state.ai_agent = GomokuAIAgent()
        st.session_state.winner = None
        st.session_state.game_over = False
        st.session_state.move_history_display = []
        st.session_state.ai_thinking = False


def display_board():
    """게임판을 Streamlit에 표시"""
    game = st.session_state.game
    board = game.board
    board_size = game.board_size

    # 게임판 표시
    cols = st.columns(board_size)
    
    for col_idx in range(board_size):
        with cols[col_idx]:
            for row_idx in range(board_size):
                cell_value = board[row_idx][col_idx]
                
                # 돌 표시
                if cell_value == 0:
                    button_text = "·"
                    button_key = f"cell_{row_idx}_{col_idx}"
                    
                    if st.button(button_text, key=button_key, use_container_width=True):
                        if not st.session_state.game_over:
                            handle_player_move(row_idx, col_idx)
                
                elif cell_value == 1:
                    st.markdown("**●**", unsafe_allow_html=True)
                else:  # cell_value == 2
                    st.markdown("**○**", unsafe_allow_html=True)


def handle_player_move(row: int, col: int):
    """플레이어의 수 처리"""
    game = st.session_state.game
    
    # 플레이어 수 배치
    success, winner = game.make_move(row, col, 1)
    
    if not success:
        st.warning("❌ 유효하지 않은 수입니다!")
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
            st.markdown(
                '<div class="status-box status-win"><h2>🎉 플레이어 승리!</h2></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="status-box status-win"><h2>🤖 AI 승리!</h2></div>',
                unsafe_allow_html=True
            )
    else:
        if st.session_state.ai_thinking:
            st.markdown(
                '<div class="status-box status-ai"><h3>🤖 AI가 생각 중...</h3></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="status-box status-player"><h3>🎯 플레이어의 차례</h3></div>',
                unsafe_have_html=True
            )


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
            st.session_state.game = GomokuGame(15)
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
    
    # 메인 콘텐츠
    col_main, col_info = st.columns([3, 1])
    
    with col_main:
        # 게임판 표시
        st.subheader("게임판")
        display_status()
        
        # 게임판 그리기
        display_board()
    
    with col_info:
        st.subheader("ℹ️ 규칙")
        st.markdown("""
        **오목**
        - 5개의 자신의 돌을 먼저 연결하면 승리
        - 플레이어: ●
        - AI: ○
        
        **LangChain 기술**
        - Groq API 사용
        - openai/gpt-oss-20b 모델
        - LangGraph 워크플로우
        """)
    
    # AI 턴 처리
    if st.session_state.ai_thinking and not st.session_state.game_over:
        with st.spinner("🤖 AI가 최적의 수를 계산 중..."):
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
