"""
Streamlit을 사용한 오목 게임 UI (개선 버전)
- 실제 바둑판 격자 표시
- 나무 텍스처 배경
- 실제 바둑돌 표현
"""

import streamlit as st
from game import GomokuGame
from ai_agent import GomokuAIAgent
import time
from typing import Optional
import os
from PIL import Image, ImageDraw
import io


# 페이지 설정
st.set_page_config(
    page_title="오목 게임 🎮",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ===== 설정 (이미지 경로) =====
ASSETS_DIR = "assets"
BOARD_IMAGE_PATH = os.path.join(ASSETS_DIR, "board.png")  # 나무 텍스처
BLACK_STONE_PATH = os.path.join(ASSETS_DIR, "black_stone.png")  # 검은 돌
WHITE_STONE_PATH = os.path.join(ASSETS_DIR, "white_stone.png")  # 흰 돌


def create_default_board(size_px=600):
    """
    기본 바둑판 이미지 생성 (19x19)
    
    Args:
        size_px: 보드 크기 (픽셀)
    """
    img = Image.new('RGB', (size_px, size_px), color=(210, 160, 100))
    
    # 격자 그리기
    board_size = 19
    cell_size = size_px // (board_size + 1)
    
    # 격자선 (어두운 갈색)
    for i in range(board_size):
        x = cell_size * (i + 1)
        y_start = cell_size
        y_end = size_px - cell_size
        draw.line([(x, y_start), (x, y_end)], fill=(50, 30, 10), width=2)
        
        y = cell_size * (i + 1)
        x_start = cell_size
        x_end = size_px - cell_size
        draw.line([(x_start, y), (x_end, y)], fill=(50, 30, 10), width=2)
    
    # 별 표시 (손바닥 위치) - 9개 위치 (19x19)
    star_positions = [
        (3, 3), (3, 9), (3, 15),
        (9, 3), (9, 9), (9, 15),
        (15, 3), (15, 9), (15, 15)
    ]
    
    for row, col in star_positions:
        x = cell_size * (col + 1)
        y = cell_size * (row + 1)
        radius = 4
        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=(50, 30, 10)
        )
    
    return img


def create_default_stone(color='black', size=40):
    """
    기본 바둑돌 이미지 생성
    
    Args:
        color: 'black' 또는 'white'
        size: 돌 크기 (픽셀)
    """
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    if color == 'black':
        # 검은 돌 (그라데이션 효과)
        draw.ellipse([(0, 0), (size-1, size-1)], fill=(20, 20, 20))
        draw.ellipse([(2, 2), (size-3, size-3)], fill=(40, 40, 40))
    else:  # white
        # 흰 돌 (그라데이션 효과)
        draw.ellipse([(0, 0), (size-1, size-1)], fill=(240, 240, 240))
        draw.ellipse([(2, 2), (size-3, size-3)], fill=(220, 220, 220))
    
    return img


def load_or_create_assets():
    """에셋 로드 또는 생성"""
    assets = {}
    
    # 나무 텍스처 보드
    if os.path.exists(BOARD_IMAGE_PATH):
        assets['board'] = Image.open(BOARD_IMAGE_PATH)
    else:
        assets['board'] = create_default_board()
    
    # 검은 돌
    if os.path.exists(BLACK_STONE_PATH):
        assets['black_stone'] = Image.open(BLACK_STONE_PATH)
    else:
        assets['black_stone'] = create_default_stone('black')
    
    # 흰 돌
    if os.path.exists(WHITE_STONE_PATH):
        assets['white_stone'] = Image.open(WHITE_STONE_PATH)
    else:
        assets['white_stone'] = create_default_stone('white')
    
    return assets


def draw_board_with_stones(game: GomokuGame, assets: dict):
    """
    바둑판(19x19)과 돌을 하나의 이미지로 그리기
    보드 텍스처 위에 격자선을 겹쳐 표시
    
    Args:
        game: 게임 객체
        assets: 이미지 딕셔너리
    """
    board_img = assets['board'].copy().convert('RGB')
    board_size = 19  # 고정: 19x19
    width, height = board_img.size
    
    cell_width = width / (board_size + 1)
    cell_height = height / (board_size + 1)
    
    # 돌 크기 (셀 크기의 70%)
    stone_size = int(min(cell_width, cell_height) * 0.7)
    
    # 검은 돌 및 흰 돌 리사이즈
    black_stone = assets['black_stone'].resize((stone_size, stone_size), Image.Resampling.LANCZOS)
    white_stone = assets['white_stone'].resize((stone_size, stone_size), Image.Resampling.LANCZOS)
    
    # 보드에 돌 그리기
    for row in range(board_size):
        for col in range(board_size):
            if game.board[row][col] != 0:
                # 돌의 중심 위치 계산
                x = int(cell_width * (col + 1) - stone_size / 2)
                y = int(cell_height * (row + 1) - stone_size / 2)
                
                if game.board[row][col] == 1:  # 플레이어 (검은 돌)
                    board_img.paste(black_stone, (x, y), black_stone)
                else:  # AI (흰 돌)
                    board_img.paste(white_stone, (x, y), white_stone)
    
    # 텍스처 위에 격자선 그리기
    draw = ImageDraw.Draw(board_img)
    line_color = (50, 30, 10)  # 어두운 갈색
    line_width = 2
    
    # 세로줄
    for i in range(board_size):
        x = int(cell_width * (i + 1))
        y_start = int(cell_height)
        y_end = int(height - cell_height)
        draw.line([(x, y_start), (x, y_end)], fill=line_color, width=line_width)
    
    # 가로줄
    for i in range(board_size):
        y = int(cell_height * (i + 1))
        x_start = int(cell_width)
        x_end = int(width - cell_width)
        draw.line([(x_start, y), (x_end, y)], fill=line_color, width=line_width)
    
    return board_img, cell_width, cell_height, stone_size


def initialize_session():
    """세션 상태 초기화"""
    if "game" not in st.session_state:
        st.session_state.game = GomokuGame(15)
        st.session_state.ai_agent = GomokuAIAgent()
        st.session_state.winner = None
        st.session_state.game_over = False
        st.session_state.move_history_display = []
        st.session_state.ai_thinking = False
        st.session_state.assets = load_or_create_assets()


def display_board_interactive(assets: dict):
    """
    인터랙티브 바둑판 표시
    클릭으로 돌 배치
    """
    game = st.session_state.game
    
    # 바둑판 그리기
    board_img, cell_width, cell_height, stone_size = draw_board_with_stones(game, assets)
    
    # 이미지를 Streamlit에 표시
    st.image(board_img, use_container_width=True)
    
    # 클릭 입력 받기
    col1, col2 = st.columns(2)
    
    with col1:
        row_input = st.number_input("행 (0-18):", min_value=0, max_value=18, value=9, step=1)
    
    with col2:
        col_input = st.number_input("열 (0-18):", min_value=0, max_value=18, value=9, step=1)
    
    if st.button("🎯 돌 놓기", use_container_width=True):
        if not st.session_state.game_over:
            handle_player_move(int(row_input), int(col_input))



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
        display_board_interactive(st.session_state.assets)
    
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
