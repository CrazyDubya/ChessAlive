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
        "setting": "The Shadow Army has breached the outer walls. Flames lick at the eastern towers. King Aldric's forces are scattered, desperate. In this moment—this single, crystalline moment—the fate of the realm hangs upon one move. The ancient prophecy spoke of this: 'When darkness covers the sixty-four squares, a single piece shall turn the tide.' That piece is you.",
        "piece_roles": {
            "king": "King Aldric, the Beleaguered Sovereign",
            "queen": "Queen Seraphina, Commander of Light",
            "rook": "The Tower Sentinel, ancient and immovable",
            "bishop": "Bishop Luminos, whose diagonal sight pierces shadow",
            "knight": "Sir Galahad, last of the cavalry",
            "pawn": "A humble footsoldier, dreaming of glory",
        },
        "narrator_voice": "ancient chronicler who has seen empires rise and fall",
        "atmosphere": "torchlight, distant screams, the weight of destiny",
    },
    PuzzleFlavor.CASE_FILES: {
        "name": "The Case Files",
        "genre": "Noir Detective",
        "setting": "Rain hammers the windows of my office on 64th Street. The dame walked in at midnight—said her King was in trouble, real trouble. The kind of trouble that ends with chalk outlines on marble floors. I've seen this setup before: the pieces are in place, the trap is set, and somebody's about to take a fall. Question is—can you see the angle before the hammer drops?",
        "piece_roles": {
            "king": "The Kingpin, sweating in his penthouse",
            "queen": "The Femme Fatale, with secrets in her eyes",
            "rook": "The Muscle, dumb but deadly",
            "bishop": "The Fixer, always working an angle",
            "knight": "The Wildcard, nobody knows whose side he's on",
            "pawn": "The Fall Guy, expendable and knows it",
        },
        "narrator_voice": "world-weary detective who's seen too much",
        "atmosphere": "cigarette smoke, rain on glass, the tick of a clock",
    },
    PuzzleFlavor.CHAMPIONSHIP: {
        "name": "The Championship",
        "genre": "Sports Drama",
        "setting": "GAME SEVEN! THE CROWD IS ON THEIR FEET! It's been a brutal series, folks—blood, sweat, and brilliance on every square. The score is tied. The clock is running. And right now, in this INCREDIBLE moment, everything comes down to ONE. SINGLE. MOVE. The underdog faces the dynasty. The rookie faces the legend. THIS IS WHY WE PLAY THE GAME!",
        "piece_roles": {
            "king": "The Captain, carrying the weight of the franchise",
            "queen": "The MVP, unstoppable when focused",
            "rook": "The Veteran, been here before",
            "bishop": "The Strategist, seeing plays before they happen",
            "knight": "The Rookie Star, fearless and flashy",
            "pawn": "The Bench Player, waiting for their moment",
        },
        "narrator_voice": "legendary sports broadcaster calling the game of his career",
        "atmosphere": "roaring crowd, sweat on the brow, glory within reach",
    },
    PuzzleFlavor.HAUNTED_BOARD: {
        "name": "The Haunted Board",
        "genre": "Gothic Horror",
        "setting": "They say this board has been playing the same game for three hundred years. Every night, when the clock strikes twelve, the pieces... move. You can hear them whispering if you listen close. The last Lord of Ashworth Manor sits frozen on e1, cursed to play forever until someone—anyone—can break the spell. The Specter Bride watches from d8. She used to be alive, they say. Now she just... waits. Find the winning move. End the nightmare. Before it ends you.",
        "piece_roles": {
            "king": "The Last Lord, trapped between worlds",
            "queen": "The Specter Bride, beautiful and terrible",
            "rook": "The Stone Guardian, older than the manor itself",
            "bishop": "The Mad Priest, whose sanity shattered on these squares",
            "knight": "The Revenant, seeking vengeance from beyond",
            "pawn": "The Lost Soul, a servant who never escaped",
        },
        "narrator_voice": "ominous archivist reading from a crumbling tome",
        "atmosphere": "candlelight, whispers, the creak of old wood",
    },
    PuzzleFlavor.NATURE_DOC: {
        "name": "Chess in the Wild",
        "genre": "Nature Documentary",
        "setting": "And here, in the vast checkered savanna of the sixty-four squares, we observe a remarkable scene. The White pieces have established their territory along the lower ranks, while the Black herd maintains dominance in the north. But nature, as we know, abhors a stalemate. One species must prove its superiority. The tension is... palpable. Watch now, as instinct takes over, and the eternal dance of predator and prey unfolds before our very eyes.",
        "piece_roles": {
            "king": "the alpha male, protecting his domain",
            "queen": "the apex predator, swift and merciless",
            "rook": "the territorial guardian, master of straight lines",
            "bishop": "the cunning stalker, patient on the diagonal",
            "knight": "the unpredictable hunter, with its mysterious L-shaped gait",
            "pawn": "the humble forager, dreaming of metamorphosis",
        },
        "narrator_voice": "Sir David Attenborough, full of gentle wonder",
        "atmosphere": "golden sunlight, the rustle of pieces, nature's brutal beauty",
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
