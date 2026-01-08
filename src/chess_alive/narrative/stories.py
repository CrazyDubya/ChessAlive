"""AI-powered game story generation."""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

from ..llm.client import LLMClient
from ..core.game import ChessGame, MoveRecord, GameResult
from ..core.piece import Color, PieceType, DEFAULT_PERSONALITIES


class StoryFormat(Enum):
    """Available story output formats."""
    TWEET = "tweet"           # 280 chars max
    SHORT_STORY = "short"     # 3-4 paragraphs
    EPIC = "epic"             # Full narrative


class NarratorStyle(Enum):
    """Narrator voice styles."""
    CHRONICLER = "chronicler"       # Epic fantasy - reverent, sweeping
    GUMSHOE = "gumshoe"             # Noir - cynical, world-weary
    PLAY_BY_PLAY = "play_by_play"   # Sports - excited, energetic
    NATURE = "nature"               # Documentary - gentle, scientific
    COMEDY = "comedy"               # Satirical - confused, witty


NARRATOR_PROMPTS = {
    NarratorStyle.CHRONICLER: {
        "name": "The Chronicler",
        "voice": "ancient, reverent, sweeping",
        "style": "In the age of kings, when armies clashed upon fields of sixty-four squares...",
        "vocabulary": ["valiant", "realm", "destiny", "fate", "glory", "darkness"],
    },
    NarratorStyle.GUMSHOE: {
        "name": "The Gumshoe",
        "voice": "cynical, world-weary, wry",
        "style": "The Queen was dead. Cornered on h7 with nowhere to run. I'd seen it coming for twelve moves.",
        "vocabulary": ["dame", "case", "hustle", "shakedown", "clean", "dirty"],
    },
    NarratorStyle.PLAY_BY_PLAY: {
        "name": "The Announcer",
        "voice": "excited, immediate, energetic",
        "style": "AND THE KNIGHT TAKES! What a move! The crowd goes wild!",
        "vocabulary": ["incredible", "stunning", "unbelievable", "clutch", "MVP"],
    },
    NarratorStyle.NATURE: {
        "name": "The Naturalist",
        "voice": "gentle, wondering, scientific",
        "style": "Here we observe the knight in its natural habitat. Notice how it approaches in an L-shape...",
        "vocabulary": ["observe", "fascinating", "specimen", "behavior", "instinct"],
    },
    NarratorStyle.COMEDY: {
        "name": "The Bumbler",
        "voice": "confused, enthusiastic, wrong",
        "style": "And the... horsey? The horsey takes the castle! Wait, can it do that?",
        "vocabulary": ["horsey", "pointy hat guy", "tower thingy", "somehow", "apparently"],
    },
}


@dataclass
class PieceQuote:
    """A quote from a piece during the game."""
    move_number: int
    piece_name: str
    piece_type: str
    color: str
    quote: str
    context: str  # "move", "capture", "check", "checkmate"


@dataclass
class GameStory:
    """Generated story about a chess game."""
    format: StoryFormat
    narrator_style: NarratorStyle
    content: str
    title: Optional[str] = None
    piece_quotes_used: List[str] = field(default_factory=list)


class StoryGenerator:
    """Generates narrative stories from chess games."""

    def __init__(self, llm_client: LLMClient):
        """Initialize the story generator."""
        self.client = llm_client

    def _extract_key_moments(self, game: ChessGame) -> List[dict]:
        """Extract key moments from the game."""
        moments = []

        for i, record in enumerate(game.move_history):
            moment = {
                "move_number": (i // 2) + 1,
                "move": record.san,
                "piece": record.piece.display_name,
                "color": record.piece.color.name_str,
            }

            if record.captured_piece:
                moment["capture"] = record.captured_piece.display_name
                moment["type"] = "capture"
            elif record.is_checkmate:
                moment["type"] = "checkmate"
            elif record.is_check:
                moment["type"] = "check"
            elif record.is_castling:
                moment["type"] = "castling"
            elif record.is_promotion:
                moment["type"] = "promotion"
            else:
                moment["type"] = "move"

            # Include commentary if present
            if hasattr(record, 'commentary') and record.commentary:
                moment["quote"] = record.commentary

            moments.append(moment)

        return moments

    def _get_narrator_system_prompt(self, style: NarratorStyle) -> str:
        """Get the system prompt for a narrator style."""
        narrator = NARRATOR_PROMPTS[style]

        return f"""You are {narrator['name']}, a narrator for ChessAlive.

YOUR VOICE: {narrator['voice']}
EXAMPLE STYLE: "{narrator['style']}"
VOCABULARY TO USE: {', '.join(narrator['vocabulary'])}

You transform chess games into compelling narratives. Your job is to:
1. Weave piece quotes naturally into the story
2. Add dramatic observations and framing
3. Stay completely in character
4. Never break the fourth wall or mention you're an AI
5. Use chess terminology naturally within your style

Remember: You are telling the story of an epic battle between two armies."""

    async def generate_tweet(
        self,
        game: ChessGame,
        piece_quotes: Optional[List[PieceQuote]] = None,
        narrator_style: NarratorStyle = NarratorStyle.CHRONICLER,
    ) -> GameStory:
        """Generate a tweet-length story (280 chars max)."""

        moments = self._extract_key_moments(game)
        result = game.result.name if game.result else "IN_PROGRESS"

        # Build quote list
        quotes_text = ""
        if piece_quotes:
            quotes_text = "\n".join([
                f'- {q.piece_name}: "{q.quote}"'
                for q in piece_quotes[:3]
            ])

        prompt = f"""Generate a TWEET (max 280 characters) about this chess game.

GAME RESULT: {result}
TOTAL MOVES: {len(game.move_history)}
KEY MOMENTS: {len([m for m in moments if m['type'] in ['capture', 'check', 'checkmate']])} captures/checks

{f'PIECE QUOTES TO USE:{chr(10)}{quotes_text}' if quotes_text else ''}

REQUIREMENTS:
- Maximum 280 characters (THIS IS CRITICAL)
- Include 1 piece quote if available
- End with drama or impact
- Include #ChessAlive hashtag
- Match your narrator voice perfectly"""

        content = await self.client.complete(
            prompt,
            system_prompt=self._get_narrator_system_prompt(narrator_style),
            temperature=0.8,
            max_tokens=100,
        )

        # Ensure under 280 chars
        if len(content) > 280:
            content = content[:277] + "..."

        return GameStory(
            format=StoryFormat.TWEET,
            narrator_style=narrator_style,
            content=content.strip(),
            piece_quotes_used=[q.quote for q in (piece_quotes or [])[:1]],
        )

    async def generate_short_story(
        self,
        game: ChessGame,
        piece_quotes: Optional[List[PieceQuote]] = None,
        narrator_style: NarratorStyle = NarratorStyle.CHRONICLER,
    ) -> GameStory:
        """Generate a short story (3-4 paragraphs)."""

        moments = self._extract_key_moments(game)
        result = game.result.name if game.result else "IN_PROGRESS"

        # Get key captures and checks
        key_moments = [m for m in moments if m['type'] in ['capture', 'check', 'checkmate', 'castling']]

        # Build quote list
        quotes_text = ""
        if piece_quotes:
            quotes_text = "\n".join([
                f'Move {q.move_number} - {q.piece_name} ({q.context}): "{q.quote}"'
                for q in piece_quotes
            ])
        else:
            # Use commentary from move records
            quotes_text = "\n".join([
                f'Move {m["move_number"]} - {m["piece"]}: "{m["quote"]}"'
                for m in moments if m.get("quote")
            ][:5])

        prompt = f"""Write a SHORT STORY (3-4 paragraphs) about this chess game.

GAME DATA:
- Result: {result}
- Total moves: {len(game.move_history)}
- Captures: {len([m for m in moments if m['type'] == 'capture'])}
- Checks: {len([m for m in moments if m['type'] == 'check'])}

KEY MOMENTS:
{chr(10).join([f"- Move {m['move_number']}: {m['piece']} {m['move']} ({m['type']})" for m in key_moments[:8]])}

PIECE QUOTES TO WEAVE IN:
{quotes_text if quotes_text else "(Generate quotes in character for key pieces)"}

STRUCTURE:
1. Opening: Set the scene, introduce the conflict
2. Rising action: The battle develops, key exchanges
3. Climax: The decisive moment
4. Resolution: The aftermath and meaning

Write in YOUR narrator voice. Weave ALL quotes naturally into the narrative."""

        content = await self.client.complete(
            prompt,
            system_prompt=self._get_narrator_system_prompt(narrator_style),
            temperature=0.8,
            max_tokens=800,
        )

        # Generate a title
        title_prompt = f"Generate a dramatic 3-5 word title for this chess story in your narrator voice. Result: {result}. Just the title, nothing else."
        title = await self.client.complete(
            title_prompt,
            system_prompt=self._get_narrator_system_prompt(narrator_style),
            temperature=0.9,
            max_tokens=20,
        )

        return GameStory(
            format=StoryFormat.SHORT_STORY,
            narrator_style=narrator_style,
            content=content.strip(),
            title=title.strip().strip('"'),
            piece_quotes_used=[q.quote for q in (piece_quotes or [])],
        )

    async def generate_story(
        self,
        game: ChessGame,
        format: StoryFormat = StoryFormat.SHORT_STORY,
        piece_quotes: Optional[List[PieceQuote]] = None,
        narrator_style: NarratorStyle = NarratorStyle.CHRONICLER,
    ) -> GameStory:
        """Generate a story in the specified format."""

        if format == StoryFormat.TWEET:
            return await self.generate_tweet(game, piece_quotes, narrator_style)
        else:
            return await self.generate_short_story(game, piece_quotes, narrator_style)
