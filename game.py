"""
오목 게임 로직 모듈
- 게임판 관리
- 돌 배치 및 검증
- 승패 판정
- 합법적 수 계산
"""

from typing import List, Tuple, Optional


class GomokuGame:
    """오목 게임을 관리하는 클래스"""

    def __init__(self, board_size: int = 15):
        """
        게임 초기화
        
        Args:
            board_size: 게임판 크기 (기본: 15x15)
                - 0: 빈칸
                - 1: 플레이어 돌
                - 2: AI 돌
        """
        self.board_size = board_size
        self.board = [[0] * board_size for _ in range(board_size)]
        self.move_history = []  # (row, col, player) 형태로 저장
        self.current_player = 1  # 1: 플레이어, 2: AI

    def reset(self):
        """게임판 초기화"""
        self.board = [[0] * self.board_size for _ in range(self.board_size)]
        self.move_history = []
        self.current_player = 1

    def is_valid_move(self, row: int, col: int) -> bool:
        """
        수가 유효한지 확인
        
        Args:
            row: 행 좌표 (0-based)
            col: 열 좌표 (0-based)
            
        Returns:
            유효한 수(빈칸)이면 True
        """
        if row < 0 or row >= self.board_size or col < 0 or col >= self.board_size:
            return False
        return self.board[row][col] == 0

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """
        현재 합법적인 모든 수 반환
        
        Returns:
            (row, col) 좌표 리스트
        """
        valid_moves = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.is_valid_move(row, col):
                    valid_moves.append((row, col))
        return valid_moves

    def place_stone(self, row: int, col: int, player: int) -> bool:
        """
        돌 배치
        
        Args:
            row: 행 좌표
            col: 열 좌표
            player: 플레이어 (1 또는 2)
            
        Returns:
            성공하면 True, 실패하면 False
        """
        if not self.is_valid_move(row, col):
            return False

        self.board[row][col] = player
        self.move_history.append((row, col, player))
        return True

    def check_winner(self, row: int, col: int) -> Optional[int]:
        """
        방금 놓인 돌(row, col)을 기준으로 승자 판정
        특정 돌을 기준으로 4개 방향(가로, 세로, 대각선 2개)을 검사
        
        Args:
            row: 마지막으로 놓인 돌의 행
            col: 마지막으로 놓인 돌의 열
            
        Returns:
            1 또는 2 (승자), 아직 승자가 없으면 None
        """
        player = self.board[row][col]
        if player == 0:
            return None

        # 4개 방향: 가로, 세로, 대각선1, 대각선2
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for dr, dc in directions:
            count = 1  # 현재 돌 포함

            # 한 방향 탐색
            r, c = row + dr, col + dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.board[r][c] == player:
                    count += 1
                    r += dr
                    c += dc
                else:
                    break

            # 반대 방향 탐색
            r, c = row - dr, col - dc
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.board[r][c] == player:
                    count += 1
                    r -= dr
                    c -= dc
                else:
                    break

            if count >= 5:
                return player

        return None

    def get_board_state(self) -> str:
        """
        게임판 현재 상태를 문자열로 반환
        
        Returns:
            게임판 시각화 문자열
        """
        # 헤더
        result = "     " + " ".join(f"{i:2d}" for i in range(self.board_size)) + "\n"
        result += "   " + "─" * (self.board_size * 3) + "\n"

        # 보드
        symbols = {0: "·", 1: "●", 2: "○"}
        for row in range(self.board_size):
            result += f"{row:2d} │"
            for col in range(self.board_size):
                result += f" {symbols[self.board[row][col]]} "
            result += f"│ {row}\n"

        result += "   " + "─" * (self.board_size * 3) + "\n"
        result += "     " + " ".join(f"{i:2d}" for i in range(self.board_size)) + "\n"
        return result

    def print_board(self):
        """게임판을 콘솔에 출력"""
        print(self.get_board_state())

    def get_game_info(self) -> dict:
        """
        현재 게임 상태 정보 반환
        
        Returns:
            dict: 게임 상태 정보
        """
        return {
            "board_size": self.board_size,
            "board": [row[:] for row in self.board],  # 깊은 복사
            "move_count": len(self.move_history),
            "current_player": self.current_player,
            "move_history": self.move_history[:]
        }

    def undo_last_move(self) -> bool:
        """
        마지막 수 취소
        
        Returns:
            취소 성공하면 True
        """
        if not self.move_history:
            return False

        row, col, _ = self.move_history.pop()
        self.board[row][col] = 0
        return True

    def make_move(self, row: int, col: int, player: int) -> Tuple[bool, Optional[int]]:
        """
        수를 두고 게임 상태 확인
        
        Args:
            row: 행
            col: 열
            player: 플레이어 (1 또는 2)
            
        Returns:
            (성공 여부, 승자) 튜플
            - 성공 여부: 돌을 놓았으면 True
            - 승자: 게임이 끝났으면 1 또는 2, 아니면 None
        """
        if not self.place_stone(row, col, player):
            return False, None

        winner = self.check_winner(row, col)
        return True, winner


if __name__ == "__main__":
    # 테스트
    game = GomokuGame(15)
    game.print_board()

    print("\n=== 테스트: 플레이어 수 배치 ===")
    game.make_move(7, 7, 1)
    game.make_move(7, 8, 2)
    game.make_move(6, 7, 1)
    game.make_move(8, 7, 2)
    game.make_move(5, 7, 1)
    game.print_board()

    print(f"\n합법적 수 개수: {len(game.get_valid_moves())}")
    print(f"게임 정보: {game.get_game_info()}")
