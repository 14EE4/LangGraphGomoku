"""오목 보드 UI 렌더링 모듈"""

import os
from io import BytesIO
from typing import Dict

import streamlit as st
from PIL import Image, ImageDraw

from game import GomokuGame


ASSETS_DIR = "assets"
BOARD_IMAGE_PATH = os.path.join(ASSETS_DIR, "board.png")
BLACK_STONE_PATH = os.path.join(ASSETS_DIR, "black_stone.png")
WHITE_STONE_PATH = os.path.join(ASSETS_DIR, "white_stone.png")
BOARD_SIZE = 19

BOARD_STYLE = """
<style>
div[data-testid="stVerticalBlock"] .gomoku-board-row button {
    min-width: 28px !important;
    min-height: 28px !important;
    width: 100% !important;
    padding: 0 !important;
    border-radius: 50% !important;
    border: 1px solid rgba(70, 45, 20, 0.55) !important;
    background: rgba(255, 255, 255, 0.08) !important;
    color: transparent !important;
    box-shadow: none !important;
}

div[data-testid="stVerticalBlock"] .gomoku-board-row button:hover {
    border-color: rgba(70, 45, 20, 0.9) !important;
    background: rgba(255, 255, 255, 0.18) !important;
}
</style>
"""


def create_default_board(size_px: int = 600) -> Image.Image:
    """기본 바둑판 이미지 생성"""
    img = Image.new("RGB", (size_px, size_px), color=(210, 160, 100))
    draw = ImageDraw.Draw(img)

    cell_size = size_px // (BOARD_SIZE + 1)

    for i in range(BOARD_SIZE):
        x = cell_size * (i + 1)
        y_start = cell_size
        y_end = size_px - cell_size
        draw.line([(x, y_start), (x, y_end)], fill=(50, 30, 10), width=2)

        y = cell_size * (i + 1)
        x_start = cell_size
        x_end = size_px - cell_size
        draw.line([(x_start, y), (x_end, y)], fill=(50, 30, 10), width=2)

    star_positions = [
        (3, 3), (3, 9), (3, 15),
        (9, 3), (9, 9), (9, 15),
        (15, 3), (15, 9), (15, 15),
    ]

    for row, col in star_positions:
        x = cell_size * (col + 1)
        y = cell_size * (row + 1)
        radius = 4
        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=(50, 30, 10),
        )

    return img


def create_default_stone(color: str = "black", size: int = 40) -> Image.Image:
    """기본 바둑돌 이미지 생성"""
    img = Image.new("RGBA", (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if color == "black":
        draw.ellipse([(0, 0), (size - 1, size - 1)], fill=(20, 20, 20))
        draw.ellipse([(2, 2), (size - 3, size - 3)], fill=(40, 40, 40))
    else:
        draw.ellipse([(0, 0), (size - 1, size - 1)], fill=(240, 240, 240))
        draw.ellipse([(2, 2), (size - 3, size - 3)], fill=(220, 220, 220))

    return img


def load_or_create_assets() -> Dict[str, Image.Image]:
    """에셋 로드 또는 생성"""
    assets: Dict[str, Image.Image] = {}

    if os.path.exists(BOARD_IMAGE_PATH):
        assets["board"] = Image.open(BOARD_IMAGE_PATH)
    else:
        assets["board"] = create_default_board()

    if os.path.exists(BLACK_STONE_PATH):
        assets["black_stone"] = Image.open(BLACK_STONE_PATH)
    else:
        assets["black_stone"] = create_default_stone("black")

    if os.path.exists(WHITE_STONE_PATH):
        assets["white_stone"] = Image.open(WHITE_STONE_PATH)
    else:
        assets["white_stone"] = create_default_stone("white")

    return assets


def draw_board_with_stones(game: GomokuGame, assets: Dict[str, Image.Image]):
    """보드 텍스처 위에 격자선과 돌을 렌더링"""
    board_img = assets["board"].copy().convert("RGB")

    original_width, original_height = board_img.size
    square_size = min(original_width, original_height)
    left = (original_width - square_size) // 2
    top = (original_height - square_size) // 2
    board_img = board_img.crop((left, top, left + square_size, top + square_size))

    width, height = board_img.size
    cell_width = width / (BOARD_SIZE + 1)
    cell_height = height / (BOARD_SIZE + 1)
    stone_size = int(min(cell_width, cell_height) * 0.7)

    black_stone = assets["black_stone"].resize((stone_size, stone_size), Image.Resampling.LANCZOS)
    white_stone = assets["white_stone"].resize((stone_size, stone_size), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(board_img)
    line_color = (50, 30, 10)

    for i in range(BOARD_SIZE):
        x = int(cell_width * (i + 1))
        y_start = int(cell_height)
        y_end = int(height - cell_height)
        draw.line([(x, y_start), (x, y_end)], fill=line_color, width=2)

    for i in range(BOARD_SIZE):
        y = int(cell_height * (i + 1))
        x_start = int(cell_width)
        x_end = int(width - cell_width)
        draw.line([(x_start, y), (x_end, y)], fill=line_color, width=2)

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if game.board[row][col] != 0:
                x = int(cell_width * (col + 1) - stone_size / 2)
                y = int(cell_height * (row + 1) - stone_size / 2)
                stone = black_stone if game.board[row][col] == 1 else white_stone
                board_img.paste(stone, (x, y), stone)

    return board_img


def display_board_interactive(game: GomokuGame, assets: Dict[str, Image.Image], game_over: bool, on_move):
    """19x19 버튼 그리드로 보드 표시 및 클릭 처리"""
    st.caption("💡 바둑판의 교점을 직접 클릭해서 돌을 놓으세요")
    st.markdown(BOARD_STYLE, unsafe_allow_html=True)

    board_img = draw_board_with_stones(game, assets)
    st.image(board_img, use_container_width=True)

    for row in range(BOARD_SIZE):
        row_columns = st.columns(BOARD_SIZE, gap="small")
        for col in range(BOARD_SIZE):
            with row_columns[col]:
                cell_value = game.board[row][col]
                label = "●" if cell_value == 1 else "○" if cell_value == 2 else ""
                disabled = cell_value != 0 or game_over
                clicked = st.button(
                    label,
                    key=f"cell_{row}_{col}",
                    disabled=disabled,
                    use_container_width=True,
                )
                if clicked and not game_over:
                    on_move(row, col)

    st.divider()
