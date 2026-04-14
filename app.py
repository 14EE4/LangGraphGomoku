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
        st.session_state.ai_last_analysis = "아직 AI 분석이 없습니다."
        st.session_state.ai_analysis_history = []
        st.session_state.min_confidence_threshold = 0.5
        st.session_state.ui_notice = None
        st.session_state.ui_notice_level = "info"
        st.session_state.last_click_signature = None


def handle_player_move(row: int, col: int):
    """플레이어의 수 처리"""
    if st.session_state.ai_thinking or st.session_state.game_over:
        return

    game = st.session_state.game
    
    # 플레이어 수 배치
    success, winner = game.make_move(row, col, 1)
    
    if not success:
        st.session_state.ui_notice_level = "error"
        st.session_state.ui_notice = f"유효하지 않은 수입니다! ({row}, {col})"
        return

    st.session_state.ui_notice = None
    
    st.session_state.move_history_display.append(f"플레이어: ({row}, {col})")
    
    # 게임 종료 확인
    if winner:
        st.session_state.winner = 1
        st.session_state.game_over = True
        st.rerun()
        return
    
    # AI 수 계산
    st.session_state.ai_thinking = True
    st.rerun()


def get_ai_move(min_confidence: float, max_retries: int = 2):
    """AI의 최적 수 계산 (신뢰도 임계값 미만이면 재고)"""
    game = st.session_state.game
    
    valid_moves = game.get_valid_moves()
    if not valid_moves:
        st.session_state.game_over = True
        return None
    
    try:
        board_state = game.get_game_info()

        best_result = None
        attempts = max_retries + 1

        for attempt in range(attempts):
            move, confidence, analysis = st.session_state.ai_agent.get_best_move(
                board_state["board"],
                board_state["board_size"],
                valid_moves,
            )

            if best_result is None or confidence > best_result[1]:
                best_result = (move, confidence, analysis)

            if confidence >= min_confidence:
                return move, confidence, analysis, attempt + 1

        # 임계값을 넘지 못하면 가장 높은 신뢰도의 결과를 반환
        if best_result is not None:
            move, confidence, analysis = best_result
            analysis = (
                analysis
                + f"\n\n[재고 결과] 최소 신뢰도 {min_confidence:.0%} 미달, "
                + f"{attempts}회 중 최고 신뢰도 {confidence:.0%} 수를 선택했습니다."
            )
            return move, confidence, analysis, attempts

        return None
    except Exception as e:
        st.session_state.ui_notice_level = "error"
        st.session_state.ui_notice = f"AI 오류: {str(e)}"
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


def display_right_notice():
    """오른쪽 패널 전용 알림 표시"""
    notice = st.session_state.get("ui_notice")
    if not notice:
        return

    level = st.session_state.get("ui_notice_level", "info")
    if level == "error":
        st.error(f"❌ {notice}")
    elif level == "warning":
        st.warning(notice)
    else:
        st.info(notice)


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
    
    # 좌측 사이드바: 원래 탭 복구
    with st.sidebar:
        sidebar_tab_game, sidebar_tab_llm = st.tabs(["게임", "LLM 생각"])

        with sidebar_tab_game:
            st.header("⚙️ 게임 설정")

            st.subheader("🤖 AI 판단 설정")
            st.session_state.min_confidence_threshold = st.slider(
                "최소 신뢰도 임계값",
                min_value=0.1,
                max_value=0.95,
                value=st.session_state.min_confidence_threshold,
                step=0.05,
            )
            st.caption(f"현재 설정: {st.session_state.min_confidence_threshold:.0%} 미만이면 다시 생각")

            st.divider()

            if st.button("🔄 새 게임 시작", use_container_width=True):
                st.session_state.game = GomokuGame(19)
                st.session_state.winner = None
                st.session_state.game_over = False
                st.session_state.move_history_display = []
                st.session_state.ai_thinking = False
                st.session_state.ai_last_analysis = "아직 AI 분석이 없습니다."
                st.session_state.ai_analysis_history = []
                st.session_state.ui_notice = None
                st.session_state.last_click_signature = None
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

        with sidebar_tab_llm:
            st.subheader("🧠 최신 LLM 생각")
            st.text_area(
                "AI 분석",
                value=st.session_state.ai_last_analysis,
                height=260,
                disabled=True,
            )

            st.divider()
            st.subheader("🗂️ 분석 히스토리")
            if st.session_state.ai_analysis_history:
                for idx, item in enumerate(reversed(st.session_state.ai_analysis_history[-5:]), start=1):
                    with st.expander(f"최근 분석 {idx}"):
                        st.write(item)
            else:
                st.caption("아직 기록된 분석이 없습니다.")

    # 메인 레이아웃: 가운데는 보드만, 오른쪽은 보드 외 정보 탭
    spacer_col, board_col, right_col = st.columns([0.08, 1.45, 0.95], gap="large")

    with board_col:
        display_board_interactive(
            st.session_state.game,
            st.session_state.assets,
            st.session_state.game_over,
            st.session_state.ai_thinking,
            handle_player_move,
        )

    with right_col:
        if st.session_state.ai_thinking and not st.session_state.game_over:
            st.info("🤖 AI가 최선의 수를 생각중...")

        right_tab_info, right_tab_notes = st.tabs(["상태", "안내"])

        with right_tab_info:
            st.header("🎮 오목 게임 vs AI")
            st.caption("LangGraph로 구현한 AI와 대전하는 오목 게임입니다.")
            st.divider()
            display_right_notice()
            st.subheader("게임 상태")
            display_status()
            st.divider()
            st.caption("가운데 영역에는 보드만 표시됩니다.")

        with right_tab_notes:
            st.subheader("플레이 가이드")
            st.markdown("""
            - 보드 위 교점을 직접 클릭해 착수합니다.
            - AI는 설정한 최소 신뢰도 미만이면 재고합니다.
            - 상세 분석은 왼쪽 `LLM 생각` 탭에서 확인합니다.
            """)
    
    # AI 턴 처리
    if st.session_state.ai_thinking and not st.session_state.game_over:
        time.sleep(1)  # UX 개선용
        result = get_ai_move(st.session_state.min_confidence_threshold)

        if result:
            move, confidence, analysis, tries = result
            st.session_state.ai_last_analysis = analysis
            st.session_state.ai_analysis_history.append(analysis)

            if move:
                # AI 수 배치
                row, col = move
                success, winner = st.session_state.game.make_move(row, col, 2)

                if success:
                    st.session_state.move_history_display.append(
                        f"AI: ({row}, {col}) [신뢰도: {confidence:.1%}, 시도: {tries}회]"
                    )

                    if winner:
                        st.session_state.winner = 2
                        st.session_state.game_over = True

        st.session_state.ai_thinking = False
        st.rerun()


if __name__ == "__main__":
    main()
