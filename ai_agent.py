"""
LangGraph를 사용한 AI 오목 에이전트
- Groq API를 통한 LLM 활용
- 게임판 분석 및 최적 수 결정
"""

from typing import TypedDict, List, Tuple, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os
import re
import json

# .env 파일 로드
load_dotenv()


class GomokuState(TypedDict):
    """AI 에이전트의 상태"""
    board: List[List[int]]  # 게임판 상태
    board_size: int
    valid_moves: List[Tuple[int, int]]  # 가능한 수들
    analysis: str  # LLM의 분석 결과
    selected_move: Optional[Tuple[int, int]]  # 최종 선택 수
    confidence: float  # 결정 신뢰도


class GomokuAIAgent:
    """Groq API를 사용한 오목 AI 에이전트"""

    def __init__(self, model: str = "openai/gpt-oss-20b", temperature: float = 0.7):
        """
        AI 에이전트 초기화
        
        Args:
            model: 사용할 Groq 모델 (기본: llama-3.1-70b-versatile)
            temperature: LLM 창의성 (0~1, 낮을수록 일관적)
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY 환경 변수를 설정하세요 (.env 파일)")

        self.llm = ChatGroq(
            temperature=temperature,
            model_name=model,
            groq_api_key=api_key
        )
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(GomokuState)

        # 노드 등록
        workflow.add_node("analyze", self._analyze_board)
        workflow.add_node("select_move", self._select_best_move)
        workflow.add_node("validate", self._validate_move)

        # 엣지 연결
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "select_move")
        workflow.add_edge("select_move", "validate")
        workflow.add_edge("validate", END)

        return workflow.compile()

    def _check_winner_on_board(
        self,
        board: List[List[int]],
        row: int,
        col: int,
        player: int,
    ) -> bool:
        """보드 상태에서 특정 착수가 5목 완성인지 확인"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        board_size = len(board)

        for dr, dc in directions:
            count = 1

            r, c = row + dr, col + dc
            while 0 <= r < board_size and 0 <= c < board_size and board[r][c] == player:
                count += 1
                r += dr
                c += dc

            r, c = row - dr, col - dc
            while 0 <= r < board_size and 0 <= c < board_size and board[r][c] == player:
                count += 1
                r -= dr
                c -= dc

            if count >= 5:
                return True

        return False

    def _find_immediate_win(
        self,
        board: List[List[int]],
        valid_moves: List[Tuple[int, int]],
        player: int,
    ) -> Optional[Tuple[int, int]]:
        """한 수에 즉시 승리 가능한 좌표 탐색"""
        for row, col in valid_moves:
            board[row][col] = player
            is_win = self._check_winner_on_board(board, row, col, player)
            board[row][col] = 0
            if is_win:
                return (row, col)
        return None

    def _board_to_string(self, board: List[List[int]]) -> str:
        """
        게임판을 문자열로 변환 (LLM에 입력하기 위해)
        
        Args:
            board: 게임판
            
        Returns:
            포맷팅된 문자열
        """
        symbols = {0: ".", 1: "X", 2: "O"}
        lines = []

        # 헤더
        board_size = len(board)
        lines.append("  " + " ".join(f"{i:2d}" for i in range(board_size)))

        # 보드
        for row_idx, row in enumerate(board):
            row_str = f"{row_idx:2d}"
            for cell in row:
                row_str += " " + symbols[cell]
            lines.append(row_str)

        return "\n".join(lines)

    def _analyze_board(self, state: GomokuState) -> GomokuState:
        """
        보드 분석: LLM에게 현재 게임 상황 분석 요청
        
        Args:
            state: 현재 상태
            
        Returns:
            분석 결과가 추가된 상태
        """
        board_string = self._board_to_string(state["board"])
        valid_moves_str = ", ".join([f"({r},{c})" for r, c in state["valid_moves"][:10]])

        system_prompt = """당신은 오목의 전문가입니다.
게임판을 분석하고 최적의 수를 제안합니다.
- X: 플레이어의 돌
- O: 당신의 돌(AI)
- .: 빈칸

현재 당신(O)은 플레이어(X)와 대전 중입니다.
다음을 고려하세요:
1. 5개의 자신의 돌이 연결되는 것을 막기
2. 자신의 돌 4개를 연결하여 이기는 기회 찾기
3. 공격적인 수와 방어적인 수의 균형"""

        user_message = f"""현재 게임판:
{board_string}

가능한 수 (일부): {valid_moves_str}

현재 게임판 상황을 분석하고:
1. 플레이어의 위협 분석
2. AI의 공격 기회
3. 추천할 최적 수 (행,열 형식으로)
를 제시하세요."""

        user_message += """

    반드시 마지막 줄을 아래 형식으로 끝내세요:
    FINAL_MOVE: (row,col)
    """

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ])
            state["analysis"] = response.content
            return state
        except Exception as e:
            raise RuntimeError(f"LLM 호출 실패: {e}")

    def _select_best_move(self, state: GomokuState) -> GomokuState:
        """
        분석 결과에서 최적 수 추출
        
        Args:
            state: 분석이 완료된 상태
            
        Returns:
            선택된 수가 추가된 상태
        """
        analysis = state["analysis"]

        # 최우선: 강제 포맷 라인 파싱
        final_pattern = r"FINAL_MOVE\s*:\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)"
        final_match = re.search(final_pattern, analysis, re.IGNORECASE)
        if final_match:
            row, col = int(final_match.group(1)), int(final_match.group(2))
            if (row, col) in state["valid_moves"]:
                state["selected_move"] = (row, col)
                state["confidence"] = 0.95
                return state

        # 프롬프트에서 (행,열) 형식의 좌표 찾기
        pattern = r"\((\d+)\s*,\s*(\d+)\)"
        matches = re.findall(pattern, analysis)

        if matches:
            # 보조 파싱: 마지막 좌표 대신 첫 번째 유효 좌표를 우선 사용
            row, col = -1, -1
            for m_row, m_col in matches:
                cand = (int(m_row), int(m_col))
                if cand in state["valid_moves"]:
                    row, col = cand
                    break

            if row == -1:
                row, col = int(matches[-1][0]), int(matches[-1][1])

            if (row, col) in state["valid_moves"]:
                state["selected_move"] = (row, col)
                state["confidence"] = 0.8
            else:
                # 유효하지 않으면 임의로 선택
                state["selected_move"] = state["valid_moves"][0] if state["valid_moves"] else None
                state["confidence"] = 0.3
        else:
            # 좌표를 찾을 수 없으면 첫 번째 유효한 수 선택
            state["selected_move"] = state["valid_moves"][0] if state["valid_moves"] else None
            state["confidence"] = 0.2

        return state

    def _validate_move(self, state: GomokuState) -> GomokuState:
        """
        선택된 수가 유효한지 검증
        
        Args:
            state: 수가 선택된 상태
            
        Returns:
            검증 완료 상태
        """
        if state["selected_move"] is None:
            raise ValueError("유효한 수를 찾을 수 없습니다")

        row, col = state["selected_move"]
        if (row, col) not in state["valid_moves"]:
            # 대체 수 선택
            state["selected_move"] = state["valid_moves"][0]
            state["confidence"] = 0.1

        return state

    def get_best_move(
        self,
        board: List[List[int]],
        board_size: int,
        valid_moves: List[Tuple[int, int]]
    ) -> Tuple[Tuple[int, int], float, str]:
        """
        최적의 수 계산
        
        Args:
            board: 게임판
            board_size: 게임판 크기
            valid_moves: 유효한 수들
            
        Returns:
            (최적 수, 신뢰도, 분석 텍스트)
        """
        # 1) 규칙 기반 즉시 승리 우선
        win_move = self._find_immediate_win(board, valid_moves, player=2)
        if win_move:
            return (
                win_move,
                1.0,
                f"즉시 승리 수를 발견했습니다. FINAL_MOVE: ({win_move[0]},{win_move[1]})",
            )

        # 2) 상대 즉시 승리 차단 우선
        block_move = self._find_immediate_win(board, valid_moves, player=1)
        if block_move:
            return (
                block_move,
                0.98,
                f"상대의 즉시 승리 수를 차단합니다. FINAL_MOVE: ({block_move[0]},{block_move[1]})",
            )

        initial_state = GomokuState(
            board=board,
            board_size=board_size,
            valid_moves=valid_moves,
            analysis="",
            selected_move=None,
            confidence=0.0
        )

        result = self.workflow.invoke(initial_state)
        
        return (
            result["selected_move"],
            result["confidence"],
            result["analysis"]
        )


# 테스트 함수
def test_ai_agent():
    """AI 에이전트 테스트"""
    from game import GomokuGame

    # 게임 초기화
    game = GomokuGame(15)
    game.make_move(7, 7, 1)  # 플레이어
    game.make_move(7, 8, 2)  # AI
    game.make_move(6, 7, 1)
    game.make_move(8, 7, 2)

    # AI 에이전트 초기화
    print("🤖 AI 에이전트 초기화 중...")
    try:
        agent = GomokuAIAgent()
        print("✅ 초기화 완료\n")

        # 최적 수 계산
        print("🧠 게임판 분석 중...")
        board_state = game.get_game_info()
        valid_moves = game.get_valid_moves()

        move, confidence, analysis = agent.get_best_move(
            board_state["board"],
            board_state["board_size"],
            valid_moves
        )

        print(f"📍 선택된 수: {move}")
        print(f"💪 신뢰도: {confidence:.1%}\n")
        print("📝 AI 분석:\n")
        print(analysis)

    except ValueError as e:
        print(f"❌ 에러: {e}")
        print("→ .env 파일에 GROQ_API_KEY를 설정하세요")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")


if __name__ == "__main__":
    test_ai_agent()
