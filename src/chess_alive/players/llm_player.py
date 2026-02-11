"""LLM-based player that uses OpenRouter to make chess moves."""

from __future__ import annotations

import json
import re
from typing import Optional, TYPE_CHECKING
import chess

if TYPE_CHECKING:
    from ..llm.client import LLMClient

from .base import Player, PlayerType
from ..core.game import ChessGame
from ..core.piece import Color


class LLMPlayer(Player):
    """Player that uses an LLM to decide chess moves."""

    def __init__(
        self,
        color: Color,
        name: Optional[str] = None,
        llm_client: Optional["LLMClient"] = None,
        style: str = "balanced",
    ):
        """
        Initialize an LLM player.

        Args:
            color: The player's color
            name: Optional player name
            llm_client: LLM client for making API calls
            style: Playing style hint ("aggressive", "defensive", "balanced", "creative")
        """
        super().__init__(color, name or f"LLM ({color.name_str})")
        self._client = llm_client
        self.style = style
        self._move_history_context: list[str] = []

    @property
    def player_type(self) -> PlayerType:
        return PlayerType.LLM

    def set_client(self, client: "LLMClient"):
        """Set the LLM client."""
        self._client = client

    async def get_move(self, game: ChessGame) -> Optional[chess.Move]:
        """Get move from LLM."""
        if game.current_turn != self.color:
            return None

        if self._client is None:
            raise RuntimeError("LLM client not configured for LLMPlayer")

        # Build the prompt
        prompt = self._build_move_prompt(game)

        # Get LLM response
        response = await self._client.complete(
            prompt,
            system_prompt=self._get_system_prompt(),
            temperature=0.3,  # Lower temperature for more consistent moves
        )

        # Try JSON parsing first, then fall back to text parsing
        move = self._parse_json_response(response, game)
        if move and game.is_legal_move(move):
            return move

        # Fall back to text-based MOVE: pattern
        move = self._parse_move_from_response(response, game)
        if move and game.is_legal_move(move):
            return move

        # Fallback: try to extract any legal move mentioned
        move = self._fallback_move_extraction(response, game)
        if move:
            return move

        # Last resort: pick a random legal move
        legal_moves = game.get_legal_moves()
        if legal_moves:
            import random
            return random.choice(legal_moves)

        return None

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        style_hints = {
            "aggressive": "You prefer attacking play, piece sacrifices for initiative, and putting pressure on the opponent's king.",
            "defensive": "You prefer solid, positional play, careful defense, and waiting for opponent mistakes.",
            "balanced": "You play a balanced style, combining tactical awareness with positional understanding.",
            "creative": "You enjoy creative, unexpected moves and are willing to take risks for interesting positions.",
        }

        style_hint = style_hints.get(self.style, style_hints["balanced"])

        return f"""You are an expert chess player playing as {self.color.name_str}.
{style_hint}

When asked for a move, analyze the position carefully and respond with your chosen move.

IMPORTANT: Respond with a JSON object in this exact format:
{{"move": "<your move in SAN>", "reasoning": "<brief analysis>"}}

Examples:
{{"move": "e4", "reasoning": "Control the center"}}
{{"move": "Nf3", "reasoning": "Develop knight toward center"}}
{{"move": "O-O", "reasoning": "Castle for king safety"}}
{{"move": "exd5", "reasoning": "Win a pawn in the center"}}

If you cannot use JSON, format your response as: MOVE: <your move>

Always choose a legal move from the provided list of legal moves."""

    def _build_move_prompt(self, game: ChessGame) -> str:
        """Build the prompt for getting a move."""
        # Get board state
        board_str = str(game.board)

        # Get legal moves
        legal_moves = [game.board.san(m) for m in game.get_legal_moves()]

        # Build recent move history
        recent_moves = []
        for i, record in enumerate(game.move_history[-10:]):  # Last 10 moves
            move_num = (len(game.move_history) - 10 + i) // 2 + 1
            if record.piece.color == Color.WHITE:
                recent_moves.append(f"{move_num}. {record.san}")
            else:
                if recent_moves and not recent_moves[-1].endswith("..."):
                    recent_moves[-1] += f" {record.san}"
                else:
                    recent_moves.append(f"{move_num}... {record.san}")

        move_history_str = " ".join(recent_moves) if recent_moves else "Game just started"

        # Check game state
        state_notes = []
        if game.is_check:
            state_notes.append("You are in CHECK!")
        if len(legal_moves) < 10:
            state_notes.append(f"Limited options: only {len(legal_moves)} legal moves available.")

        state_str = " ".join(state_notes) if state_notes else ""

        prompt = f"""Current position (you are playing {self.color.name_str}):

{board_str}

FEN: {game.fen}

Move history: {move_history_str}

Legal moves available: {', '.join(legal_moves)}

{state_str}

It's your turn. Analyze the position and choose the best move.
Respond with JSON: {{"move": "<SAN>", "reasoning": "<analysis>"}}"""

        return prompt

    def _parse_json_response(
        self, response: str, game: ChessGame
    ) -> Optional[chess.Move]:
        """Parse a JSON-structured move response.

        Tries to extract a JSON object with a "move" field from the response.
        Handles cases where the JSON is embedded in surrounding text.
        """
        # Try to find JSON in the response
        json_match = re.search(r'\{[^{}]*"move"\s*:\s*"[^"]*"[^{}]*\}', response)
        if json_match:
            try:
                data = json.loads(json_match.group())
                move_str = data.get("move", "").strip()
                if move_str:
                    return game.parse_move(move_str)
            except (json.JSONDecodeError, AttributeError):
                pass

        # Try the whole response as JSON
        try:
            data = json.loads(response.strip())
            move_str = data.get("move", "").strip()
            if move_str:
                return game.parse_move(move_str)
        except (json.JSONDecodeError, AttributeError):
            pass

        return None

    def _parse_move_from_response(
        self, response: str, game: ChessGame
    ) -> Optional[chess.Move]:
        """Parse a move from the LLM response using text patterns."""
        # Look for "MOVE: <move>" pattern
        move_pattern = r"MOVE:\s*([A-Za-z0-9\-\+\#\=]+)"
        match = re.search(move_pattern, response, re.IGNORECASE)

        if match:
            move_str = match.group(1).strip()
            return game.parse_move(move_str)

        return None

    def _fallback_move_extraction(
        self, response: str, game: ChessGame
    ) -> Optional[chess.Move]:
        """Try to extract any valid move from the response."""
        # Get all legal moves in SAN
        legal_san = {game.board.san(m): m for m in game.get_legal_moves()}

        # Check if any legal move appears in the response
        for san, move in legal_san.items():
            # Use word boundary matching
            if re.search(rf"\b{re.escape(san)}\b", response):
                return move

        # Try UCI format
        uci_pattern = r"\b([a-h][1-8][a-h][1-8][qrbn]?)\b"
        for match in re.finditer(uci_pattern, response):
            uci = match.group(1)
            try:
                move = chess.Move.from_uci(uci)
                if game.is_legal_move(move):
                    return move
            except ValueError:
                continue

        return None

    async def get_move_with_reasoning(
        self, game: ChessGame
    ) -> tuple[Optional[chess.Move], str]:
        """
        Get move along with the LLM's reasoning.

        Returns:
            Tuple of (move, reasoning_text)
        """
        if game.current_turn != self.color:
            return None, ""

        if self._client is None:
            raise RuntimeError("LLM client not configured for LLMPlayer")

        prompt = self._build_move_prompt(game) + """

Please provide detailed reasoning for your move.
Respond with JSON: {"move": "<SAN>", "reasoning": "<detailed analysis>"}"""

        response = await self._client.complete(
            prompt,
            system_prompt=self._get_system_prompt(),
            temperature=0.4,
        )

        # Try JSON first for both move and reasoning
        reasoning = ""
        move = None

        json_match = re.search(r'\{[^{}]*"move"\s*:\s*"[^"]*"[^{}]*\}', response)
        if json_match:
            try:
                data = json.loads(json_match.group())
                move_str = data.get("move", "").strip()
                reasoning = data.get("reasoning", "")
                if move_str:
                    move = game.parse_move(move_str)
                    if move and game.is_legal_move(move):
                        return move, reasoning
            except (json.JSONDecodeError, AttributeError):
                pass

        # Fall back to text parsing
        reasoning_match = re.search(
            r"REASONING:\s*(.+?)(?=MOVE:|$)", response, re.DOTALL | re.IGNORECASE
        )
        reasoning = reasoning_match.group(1).strip() if reasoning_match else response

        # Extract move
        move = self._parse_move_from_response(response, game)
        if not move or not game.is_legal_move(move):
            move = self._fallback_move_extraction(response, game)

        return move, reasoning
