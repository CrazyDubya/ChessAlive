"""Narrative puzzle system with story-wrapped chess puzzles."""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
import chess

from ..llm.client import LLMClient
from ..core.piece import DEFAULT_PERSONALITIES, PieceType, Color


class PuzzleTheme(Enum):
    """Chess puzzle themes."""
    BACK_RANK_MATE = "backRankMate"
    FORK = "fork"
    PIN = "pin"
    SKEWER = "skewer"
    DISCOVERED_ATTACK = "discoveredAttack"
    SACRIFICE = "sacrifice"
    PROMOTION = "promotion"
    CHECKMATE_IN_ONE = "mateIn1"
    CHECKMATE_IN_TWO = "mateIn2"


class PuzzleFlavor(Enum):
    """Narrative flavors for puzzles."""
    KINGDOM_SIEGE = "kingdom_siege"       # Epic Fantasy
    CASE_FILES = "case_files"             # Noir Detective
    CHAMPIONSHIP = "championship"          # Sports
    HAUNTED_BOARD = "haunted_board"       # Gothic Horror
    NATURE_DOC = "nature_documentary"     # Documentary


FLAVOR_SETTINGS = {
    PuzzleFlavor.KINGDOM_SIEGE: {
        "name": "Kingdom Under Siege",
        "genre": "Epic Fantasy",
        "setting": "The Dark Kingdom has invaded. Castle walls crumble. Each puzzle is a battle for survival.",
        "piece_roles": {
            "king": "Your Liege",
            "queen": "The Queen Commander",
            "rook": "Tower Defender",
            "bishop": "Battle Mage",
            "knight": "Cavalry Champion",
            "pawn": "Brave Infantry",
        },
        "narrator_voice": "ancient chronicler",
    },
    PuzzleFlavor.CASE_FILES: {
        "name": "The Case Files",
        "genre": "Noir Detective",
        "setting": "The city's dark. The board's darker. Every puzzle is a case to crack.",
        "piece_roles": {
            "king": "The Kingpin",
            "queen": "The Femme Fatale",
            "rook": "The Muscle",
            "bishop": "The Fixer",
            "knight": "The Wildcard",
            "pawn": "The Fall Guy",
        },
        "narrator_voice": "world-weary detective",
    },
    PuzzleFlavor.CHAMPIONSHIP: {
        "name": "The Championship",
        "genre": "Sports Drama",
        "setting": "Game 7. Finals. Everything on the line. This is your moment.",
        "piece_roles": {
            "king": "The Captain",
            "queen": "The MVP",
            "rook": "The Veteran",
            "bishop": "The Strategist",
            "knight": "The Rookie Star",
            "pawn": "The Bench Player",
        },
        "narrator_voice": "excited sports announcer",
    },
    PuzzleFlavor.HAUNTED_BOARD: {
        "name": "The Haunted Board",
        "genre": "Gothic Horror",
        "setting": "The pieces whisper in the darkness. Some games... never truly end.",
        "piece_roles": {
            "king": "The Last Lord",
            "queen": "The Specter Bride",
            "rook": "The Stone Guardian",
            "bishop": "The Mad Priest",
            "knight": "The Revenant",
            "pawn": "The Lost Soul",
        },
        "narrator_voice": "ominous archivist",
    },
    PuzzleFlavor.NATURE_DOC: {
        "name": "Chess in the Wild",
        "genre": "Nature Documentary",
        "setting": "Here we observe the chess pieces in their natural habitat...",
        "piece_roles": {
            "king": "the alpha",
            "queen": "the apex predator",
            "rook": "the territorial guardian",
            "bishop": "the cunning stalker",
            "knight": "the unpredictable hunter",
            "pawn": "the humble forager",
        },
        "narrator_voice": "gentle naturalist",
    },
}


THEME_NARRATIVES = {
    PuzzleTheme.BACK_RANK_MATE: {
        "setup": "The enemy king cowers behind walls, thinking himself safe. But walls can become prisons.",
        "narrator_piece": "rook",
        "success": "The walls have fallen! Checkmate delivered with precision.",
        "failure": "The escape route remains open. Look again at the back rank.",
    },
    PuzzleTheme.FORK: {
        "setup": "Two targets stand vulnerable. One strike can threaten both.",
        "narrator_piece": "knight",
        "success": "A devastating fork! Both targets scatter, but the damage is done.",
        "failure": "The fork isn't there. Find where two enemies align.",
    },
    PuzzleTheme.PIN: {
        "setup": "The enemy hides behind their own soldiers. What protects them... traps them.",
        "narrator_piece": "bishop",
        "success": "Pinned! They cannot move without losing everything.",
        "failure": "The pin isn't in place. Look for a piece shielding another.",
    },
    PuzzleTheme.SACRIFICE: {
        "setup": "Sometimes you must give to receive. The question is: what's worth losing?",
        "narrator_piece": "queen",
        "success": "A brilliant sacrifice! The position opens like a flower.",
        "failure": "That's just a loss, not a sacrifice. Think deeper.",
    },
    PuzzleTheme.CHECKMATE_IN_ONE: {
        "setup": "One move. One chance. The enemy king awaits judgment.",
        "narrator_piece": "queen",
        "success": "Checkmate! Swift and decisive justice.",
        "failure": "The king escapes. The mate must be forced, not hoped for.",
    },
    PuzzleTheme.CHECKMATE_IN_TWO: {
        "setup": "Two moves to victory. The path is narrow but clear.",
        "narrator_piece": "rook",
        "success": "Checkmate in two! A calculated finish.",
        "failure": "The sequence breaks. Visualize both moves before committing.",
    },
}


# Built-in puzzle collection
PUZZLE_DATABASE = [
    {
        "id": "p001",
        "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
        "solution": ["Qxf7#"],
        "theme": PuzzleTheme.CHECKMATE_IN_ONE,
        "difficulty": 800,
        "name": "Scholar's Mate",
    },
    {
        "id": "p002",
        "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
        "solution": ["Ng5", "d5", "Nxf7"],
        "theme": PuzzleTheme.FORK,
        "difficulty": 1000,
        "name": "Fried Liver Attack",
    },
    {
        "id": "p003",
        "fen": "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1",
        "solution": ["Re8#"],
        "theme": PuzzleTheme.BACK_RANK_MATE,
        "difficulty": 600,
        "name": "Back Rank Basics",
    },
    {
        "id": "p004",
        "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQ1RK1 b kq - 5 4",
        "solution": ["Nxe4"],
        "theme": PuzzleTheme.FORK,
        "difficulty": 900,
        "name": "Central Fork",
    },
    {
        "id": "p005",
        "fen": "r2qk2r/ppp2ppp/2n1bn2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 7",
        "solution": ["Bxf7+", "Kxf7", "Ng5+"],
        "theme": PuzzleTheme.SACRIFICE,
        "difficulty": 1200,
        "name": "Greek Gift",
    },
    {
        "id": "p006",
        "fen": "r1bqr1k1/ppp2ppp/2n2n2/3p4/1bPP4/2N1PN2/PP3PPP/R1BQKB1R w KQ - 0 8",
        "solution": ["a3", "Ba5", "b4"],
        "theme": PuzzleTheme.PIN,
        "difficulty": 1100,
        "name": "Bishop Trap",
    },
    {
        "id": "p007",
        "fen": "r2q1rk1/ppp2ppp/2n1bn2/3pp3/2PP4/2N1PN2/PP2BPPP/R1BQ1RK1 w - - 0 9",
        "solution": ["cxd5", "exd5", "Nxd5"],
        "theme": PuzzleTheme.DISCOVERED_ATTACK,
        "difficulty": 1150,
        "name": "Central Explosion",
    },
    {
        "id": "p008",
        "fen": "8/8/8/8/8/5k2/4p3/4K3 w - - 0 1",
        "solution": ["Kf1"],
        "theme": PuzzleTheme.PROMOTION,
        "difficulty": 700,
        "name": "Stopping the Pawn",
    },
]


@dataclass
class NarrativePuzzle:
    """A chess puzzle with narrative wrapper."""
    id: str
    fen: str
    solution: List[str]
    theme: PuzzleTheme
    difficulty: int

    # Narrative elements
    title: str
    flavor: PuzzleFlavor
    setup_text: str
    narrator_piece: str
    success_text: str
    failure_text: str

    # State
    attempts: int = 0
    solved: bool = False
    user_moves: List[str] = field(default_factory=list)


@dataclass
class PuzzleResult:
    """Result of a puzzle attempt."""
    correct: bool
    message: str
    narrator_quote: str
    move_played: str
    expected_move: str


class PuzzleEngine:
    """Engine for narrative chess puzzles."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize the puzzle engine."""
        self.client = llm_client
        self.puzzles = PUZZLE_DATABASE.copy()
        self.current_puzzle: Optional[NarrativePuzzle] = None

    def get_puzzle_count(self) -> int:
        """Get total number of available puzzles."""
        return len(self.puzzles)

    def get_random_puzzle(
        self,
        flavor: PuzzleFlavor = PuzzleFlavor.KINGDOM_SIEGE,
        difficulty_range: Optional[tuple] = None,
    ) -> NarrativePuzzle:
        """Get a random puzzle wrapped in narrative."""

        # Filter by difficulty if specified
        candidates = self.puzzles
        if difficulty_range:
            min_diff, max_diff = difficulty_range
            candidates = [p for p in self.puzzles if min_diff <= p["difficulty"] <= max_diff]

        if not candidates:
            candidates = self.puzzles

        raw = random.choice(candidates)
        return self._wrap_puzzle(raw, flavor)

    def get_puzzle_by_theme(
        self,
        theme: PuzzleTheme,
        flavor: PuzzleFlavor = PuzzleFlavor.KINGDOM_SIEGE,
    ) -> Optional[NarrativePuzzle]:
        """Get a puzzle by theme."""
        candidates = [p for p in self.puzzles if p["theme"] == theme]
        if not candidates:
            return None

        raw = random.choice(candidates)
        return self._wrap_puzzle(raw, flavor)

    def _wrap_puzzle(self, raw: dict, flavor: PuzzleFlavor) -> NarrativePuzzle:
        """Wrap a raw puzzle in narrative."""
        theme = raw["theme"]
        flavor_data = FLAVOR_SETTINGS[flavor]
        theme_data = THEME_NARRATIVES.get(theme, {
            "setup": "A critical moment. Find the winning move.",
            "narrator_piece": "queen",
            "success": "Excellent! The solution is found.",
            "failure": "Not quite. Try again.",
        })

        # Get the narrator piece name from flavor
        narrator_type = theme_data["narrator_piece"]
        narrator_name = flavor_data["piece_roles"].get(narrator_type, narrator_type.title())

        # Build narrative setup
        setup = f"{flavor_data['setting']}\n\n{narrator_name} speaks:\n\"{theme_data['setup']}\""

        return NarrativePuzzle(
            id=raw["id"],
            fen=raw["fen"],
            solution=raw["solution"],
            theme=theme,
            difficulty=raw["difficulty"],
            title=raw.get("name", f"Puzzle {raw['id']}"),
            flavor=flavor,
            setup_text=setup,
            narrator_piece=narrator_name,
            success_text=theme_data["success"],
            failure_text=theme_data["failure"],
        )

    def start_puzzle(self, puzzle: NarrativePuzzle) -> chess.Board:
        """Start working on a puzzle."""
        self.current_puzzle = puzzle
        puzzle.attempts = 0
        puzzle.solved = False
        puzzle.user_moves = []
        return chess.Board(puzzle.fen)

    def attempt_move(self, move_san: str) -> PuzzleResult:
        """Attempt a move on the current puzzle."""
        if not self.current_puzzle:
            raise ValueError("No puzzle in progress")

        puzzle = self.current_puzzle
        puzzle.attempts += 1

        # Check if move is in solution
        expected_idx = len(puzzle.user_moves)
        if expected_idx >= len(puzzle.solution):
            return PuzzleResult(
                correct=False,
                message="Puzzle already solved!",
                narrator_quote=puzzle.success_text,
                move_played=move_san,
                expected_move="",
            )

        expected_move = puzzle.solution[expected_idx]

        # Normalize move comparison (handle different notations)
        board = chess.Board(puzzle.fen)
        for prev_move in puzzle.user_moves:
            board.push_san(prev_move)

        try:
            user_move = board.parse_san(move_san)
            expected = board.parse_san(expected_move)
        except ValueError:
            return PuzzleResult(
                correct=False,
                message=f"Invalid move: {move_san}",
                narrator_quote=puzzle.failure_text,
                move_played=move_san,
                expected_move=expected_move,
            )

        if user_move == expected:
            puzzle.user_moves.append(move_san)

            # Check if puzzle complete
            if len(puzzle.user_moves) >= len(puzzle.solution):
                puzzle.solved = True
                return PuzzleResult(
                    correct=True,
                    message="Puzzle solved!",
                    narrator_quote=f"{puzzle.narrator_piece}: \"{puzzle.success_text}\"",
                    move_played=move_san,
                    expected_move=expected_move,
                )
            else:
                # More moves needed
                return PuzzleResult(
                    correct=True,
                    message=f"Correct! {len(puzzle.solution) - len(puzzle.user_moves)} move(s) remaining.",
                    narrator_quote="Good move! Continue...",
                    move_played=move_san,
                    expected_move=expected_move,
                )
        else:
            return PuzzleResult(
                correct=False,
                message="Incorrect move",
                narrator_quote=f"{puzzle.narrator_piece}: \"{puzzle.failure_text}\"",
                move_played=move_san,
                expected_move=expected_move,
            )

    def get_hint(self) -> str:
        """Get a hint for the current puzzle."""
        if not self.current_puzzle:
            return "No puzzle in progress"

        puzzle = self.current_puzzle
        expected_idx = len(puzzle.user_moves)

        if expected_idx >= len(puzzle.solution):
            return "Puzzle already solved!"

        solution_move = puzzle.solution[expected_idx]
        # Give a subtle hint about the move
        if solution_move.endswith("#"):
            return f"{puzzle.narrator_piece} whispers: \"Look for checkmate...\""
        elif solution_move.endswith("+"):
            return f"{puzzle.narrator_piece} hints: \"A check might be in order...\""
        elif "x" in solution_move:
            return f"{puzzle.narrator_piece} suggests: \"Consider a capture...\""
        else:
            # Hint about the piece
            piece_char = solution_move[0] if solution_move[0].isupper() else "P"
            piece_name = {
                "K": "king", "Q": "queen", "R": "rook",
                "B": "bishop", "N": "knight", "P": "pawn"
            }.get(piece_char, "piece")
            return f"{puzzle.narrator_piece} hints: \"The {piece_name} holds the key...\""

    def get_difficulty_label(self, rating: int) -> str:
        """Get a human-readable difficulty label."""
        if rating < 800:
            return "Beginner"
        elif rating < 1200:
            return "Intermediate"
        elif rating < 1600:
            return "Advanced"
        elif rating < 2000:
            return "Expert"
        else:
            return "Master"
