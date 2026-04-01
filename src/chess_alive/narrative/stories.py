"""AI-powered game story generation with rich character context."""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum

from ..llm.client import LLMClient
from ..core.game import ChessGame, MoveRecord, GameResult
from ..core.piece import Color, PieceType, DEFAULT_PERSONALITIES, PiecePersonality


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


# Rich narrator definitions with full context
NARRATORS = {
    NarratorStyle.CHRONICLER: {
        "name": "The Chronicler",
        "title": "Keeper of the Sixty-Four Squares",
        "voice": "You speak with ancient reverence, as one who has witnessed a thousand battles. Your words flow like an old saga, rich with destiny and portent.",
        "tone": "Epic, sweeping, mythological. You see chess as eternal warfare between Light and Shadow.",
        "opening_style": "Begin with cosmic scope - the eternal struggle, the weight of history",
        "how_you_quote": "Treat piece quotes as prophecy fulfilled, words spoken before destiny struck",
        "vocabulary": ["valiant", "realm", "destiny", "fate", "glory", "shadow", "sovereign", "fell", "ancient", "eternal"],
        "example": "In the age before memory, when the Sixty-Four Squares were young, two kingdoms arose—one of blazing Light, one of creeping Shadow. And so it was written that they would clash, as they always have, as they always shall...",
    },
    NarratorStyle.GUMSHOE: {
        "name": "The Gumshoe",
        "title": "Private Eye, 64th Precinct",
        "voice": "You're a world-weary detective narrating a case. Everything's a setup, everyone's got an angle. You've seen it all on this board.",
        "tone": "Noir, cynical, punchy sentences. Chess is crime—captures are hits, the king is the mark.",
        "opening_style": "Start with the ending or a body (captured piece). Work backwards.",
        "how_you_quote": "Piece quotes are witness testimony, last words, or threats you overheard",
        "vocabulary": ["dame", "patsy", "setup", "fall guy", "clean", "dirty", "angle", "the take", "heat", "score"],
        "example": "The Queen was dead. Cornered on h7 with nowhere to run. I'd seen it coming for twelve moves—the way the Knight kept circling, the Bishop lurking on that long diagonal. In this game, everybody's got a price. Hers just came due.",
    },
    NarratorStyle.PLAY_BY_PLAY: {
        "name": "The Announcer",
        "title": "Voice of the Championship",
        "voice": "You're calling the biggest match of the century! Every move is electric. The crowd is on their feet. This is HISTORY!",
        "tone": "Breathless excitement, dramatic pauses, incredible energy. Chess is the ultimate sport.",
        "opening_style": "Set the stakes—championship, rivalry, everything on the line",
        "how_you_quote": "Piece quotes are player interviews, trash talk, victory speeches",
        "vocabulary": ["INCREDIBLE", "stunning", "unbelievable", "clutch", "MVP", "upset", "dynasty", "legacy", "championship"],
        "example": "LADIES AND GENTLEMEN, WE ARE WITNESSING HISTORY! The Knight—SIR GALAHAD—has just executed the most AUDACIOUS fork this commentator has EVER seen! The crowd is going ABSOLUTELY WILD!",
    },
    NarratorStyle.NATURE: {
        "name": "The Naturalist",
        "title": "Sir David Attenborough of Chess",
        "voice": "You observe the chess pieces as magnificent creatures in their natural habitat. Every move is behavior, every capture is the food chain.",
        "tone": "Gentle wonder, scientific curiosity, profound respect for nature's brutality",
        "opening_style": "Set the scene of the habitat—the board as ecosystem",
        "how_you_quote": "Piece quotes are the inner thoughts of creatures, instincts given voice",
        "vocabulary": ["observe", "remarkable", "specimen", "habitat", "instinct", "prey", "apex predator", "territory", "migration"],
        "example": "Here, on the vast savanna of sixty-four squares, we observe a remarkable specimen—the Knight. Watch how it moves in its distinctive L-shaped pattern, a adaptation that has puzzled naturalists for centuries. It approaches the enemy Pawn... and strikes.",
    },
    NarratorStyle.COMEDY: {
        "name": "The Bumbler",
        "title": "Guy Who Just Learned Chess Yesterday",
        "voice": "You're enthusiastically narrating despite having NO IDEA what's happening. You get piece names wrong, misunderstand rules, but your heart is in it.",
        "tone": "Confused but committed, accidentally profound, hilariously wrong",
        "opening_style": "Confidently misstate the situation",
        "how_you_quote": "Piece quotes confuse you further—why are they talking?!",
        "vocabulary": ["horsey", "pointy hat guy", "castle thingy", "the big one", "somehow", "apparently", "I think?", "wait what"],
        "example": "Okay so the horsey just... jumped? Over the other guys? Is that legal?? And now the pointy hat man is threatening the... okay I'm being told that's a 'Bishop' and apparently he's been 'controlling the diagonal' this whole time. Sure. Sure!",
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
class GameMoment:
    """A significant moment in the game."""
    move_number: int
    half_move: int
    san: str
    piece_name: str
    piece_personality: PiecePersonality
    color: str
    moment_type: str  # move, capture, check, checkmate, castling, promotion
    captured_piece_name: Optional[str] = None
    captured_personality: Optional[PiecePersonality] = None
    commentary: Optional[str] = None


@dataclass
class GameStory:
    """Generated story about a chess game."""
    format: StoryFormat
    narrator_style: NarratorStyle
    content: str
    title: Optional[str] = None
    piece_quotes_used: List[str] = field(default_factory=list)


class StoryGenerator:
    """Generates rich narrative stories from chess games."""

    def __init__(self, llm_client: LLMClient):
        """Initialize the story generator."""
        self.client = llm_client

    def _get_personality(self, piece_type: PieceType, color: Color) -> PiecePersonality:
        """Get the personality for a piece."""
        return DEFAULT_PERSONALITIES.get(
            (piece_type, color),
            PiecePersonality(name=f"{color.name_str} {piece_type.name_str}")
        )

    def _build_character_context(self) -> str:
        """Build rich character descriptions for the LLM."""
        white_chars = []
        black_chars = []

        for (ptype, color), personality in DEFAULT_PERSONALITIES.items():
            desc = f"**{personality.name}** ({ptype.name_str}): {personality.archetype}. "
            desc += f"Speaks {personality.speaking_style}. "
            desc += f"{personality.backstory}"

            if color == Color.WHITE:
                white_chars.append(desc)
            else:
                black_chars.append(desc)

        return f"""
THE KINGDOM OF LIGHT (White):
{chr(10).join(white_chars)}

THE DARK REALM (Black):
{chr(10).join(black_chars)}
"""

    def _extract_rich_moments(self, game: ChessGame) -> List[GameMoment]:
        """Extract moments with full personality context."""
        moments = []

        for i, record in enumerate(game.move_history):
            piece_type = record.piece.piece_type
            color = record.piece.color
            personality = self._get_personality(piece_type, color)

            moment_type = "move"
            captured_name = None
            captured_personality = None

            if record.captured_piece:
                moment_type = "capture"
                captured_name = record.captured_piece.display_name
                captured_personality = self._get_personality(
                    record.captured_piece.piece_type,
                    record.captured_piece.color
                )
            elif record.is_checkmate:
                moment_type = "checkmate"
            elif record.is_check:
                moment_type = "check"
            elif record.is_castling:
                moment_type = "castling"
            elif record.is_promotion:
                moment_type = "promotion"

            moments.append(GameMoment(
                move_number=(i // 2) + 1,
                half_move=i,
                san=record.san,
                piece_name=personality.name,
                piece_personality=personality,
                color=color.name_str,
                moment_type=moment_type,
                captured_piece_name=captured_name,
                captured_personality=captured_personality,
                commentary=getattr(record, 'commentary', None),
            ))

        return moments

    def _build_game_narrative(self, moments: List[GameMoment]) -> str:
        """Build a narrative description of what happened."""
        lines = []

        for m in moments:
            if m.moment_type == "capture":
                lines.append(
                    f"Move {m.move_number}: {m.piece_name} ({m.color}) captures "
                    f"{m.captured_piece_name} with {m.san}!"
                )
            elif m.moment_type == "check":
                lines.append(f"Move {m.move_number}: {m.piece_name} delivers CHECK with {m.san}!")
            elif m.moment_type == "checkmate":
                lines.append(f"Move {m.move_number}: {m.piece_name} delivers CHECKMATE with {m.san}!")
            elif m.moment_type == "castling":
                lines.append(f"Move {m.move_number}: The King retreats to safety—{m.san}!")
            elif m.moment_type == "promotion":
                lines.append(f"Move {m.move_number}: A humble pawn achieves glory—{m.san}!")

        # Add opening if no dramatic moments yet
        if not lines and moments:
            first_few = moments[:4]
            lines.append("The opening moves set the stage:")
            for m in first_few:
                lines.append(f"  {m.piece_name} to {m.san}")

        return "\n".join(lines)

    def _get_narrator_prompt(self, style: NarratorStyle) -> str:
        """Build a rich narrator system prompt."""
        n = NARRATORS[style]

        return f"""You are {n['name']}, {n['title']}.

YOUR VOICE:
{n['voice']}

YOUR TONE:
{n['tone']}

HOW YOU BEGIN STORIES:
{n['opening_style']}

HOW YOU USE CHARACTER QUOTES:
{n['how_you_quote']}

WORDS YOU FAVOR: {', '.join(n['vocabulary'])}

EXAMPLE OF YOUR STYLE:
"{n['example']}"

CRITICAL RULES:
1. NEVER break character or mention being an AI
2. NEVER use generic chess commentary—make it YOUR style
3. Every line should drip with your personality
4. Piece names are CHARACTER names (King Aldric, Queen Nyx, Sir Galahad, etc.)
5. This is DRAMA, not a game recap
"""

    async def generate_tweet(
        self,
        game: ChessGame,
        piece_quotes: Optional[List[PieceQuote]] = None,
        narrator_style: NarratorStyle = NarratorStyle.CHRONICLER,
    ) -> GameStory:
        """Generate a tweet-length story (280 chars max)."""

        moments = self._extract_rich_moments(game)
        key_moments = [m for m in moments if m.moment_type != "move"]
        result = game.result.name if game.result else "IN_PROGRESS"

        # Build dramatic context
        drama = []
        if key_moments:
            for m in key_moments[-3:]:  # Last 3 dramatic moments
                if m.moment_type == "capture":
                    drama.append(f"{m.piece_name} slew {m.captured_piece_name}")
                elif m.moment_type == "checkmate":
                    drama.append(f"{m.piece_name} delivered the killing blow")
                elif m.moment_type == "check":
                    drama.append(f"{m.piece_name} threatened the enemy king")

        # Get a featured character
        featured = None
        if moments:
            for m in reversed(moments):
                if m.moment_type in ["capture", "check", "checkmate"]:
                    featured = m
                    break
            if not featured:
                featured = moments[-1]

        prompt = f"""Write a TWEET (max 280 characters) about this chess battle.

THE BATTLE:
- Moves played: {len(moments)}
- Result: {result}
- Key drama: {'; '.join(drama) if drama else 'Tension building...'}

FEATURED CHARACTER:
{f'**{featured.piece_name}** - {featured.piece_personality.archetype}, speaks {featured.piece_personality.speaking_style}. {featured.piece_personality.backstory}' if featured else 'The armies face off.'}

{f'Give {featured.piece_name} a short quote in their voice!' if featured else ''}

REQUIREMENTS:
- MAXIMUM 280 characters (count carefully!)
- End with #ChessAlive
- Make it DRAMATIC in your narrator voice
- Include a character quote if possible

Write ONLY the tweet, nothing else."""

        content = await self.client.complete(
            prompt,
            system_prompt=self._get_narrator_prompt(narrator_style),
            temperature=0.9,
            max_tokens=150,
        )

        # Clean up and ensure length
        content = content.strip().strip('"')
        if len(content) > 280:
            # Try to cut at a sentence
            if '. ' in content[:277]:
                content = content[:content.rfind('. ', 0, 277) + 1]
            else:
                content = content[:277] + "..."

        return GameStory(
            format=StoryFormat.TWEET,
            narrator_style=narrator_style,
            content=content,
            piece_quotes_used=[],
        )

    async def generate_short_story(
        self,
        game: ChessGame,
        piece_quotes: Optional[List[PieceQuote]] = None,
        narrator_style: NarratorStyle = NarratorStyle.CHRONICLER,
    ) -> GameStory:
        """Generate a short story (3-4 paragraphs)."""

        moments = self._extract_rich_moments(game)
        result = game.result.name if game.result else "IN_PROGRESS"

        # Build character roster for this game
        characters_involved = {}
        for m in moments:
            key = (m.piece_name, m.color)
            if key not in characters_involved:
                characters_involved[key] = {
                    "name": m.piece_name,
                    "personality": m.piece_personality,
                    "color": m.color,
                    "actions": [],
                }
            characters_involved[key]["actions"].append(m)

            if m.captured_piece_name and m.captured_personality:
                cap_key = (m.captured_piece_name, "Black" if m.color == "White" else "White")
                if cap_key not in characters_involved:
                    characters_involved[cap_key] = {
                        "name": m.captured_piece_name,
                        "personality": m.captured_personality,
                        "color": cap_key[1],
                        "actions": [],
                        "fell_to": m.piece_name,
                    }

        # Build character descriptions
        char_descriptions = []
        for key, char in list(characters_involved.items())[:6]:
            p = char["personality"]
            desc = f"**{char['name']}** ({char['color']}): {p.archetype}. Speaks {p.speaking_style}."
            if "fell_to" in char:
                desc += f" [CAPTURED by {char['fell_to']}]"
            char_descriptions.append(desc)

        # Build narrative of events
        narrative = self._build_game_narrative(moments)

        prompt = f"""Write a SHORT STORY (3-4 paragraphs) about this chess battle.

CHARACTERS IN THIS BATTLE:
{chr(10).join(char_descriptions)}

WHAT HAPPENED:
{narrative}

RESULT: {result} after {len(moments)} moves

STORY REQUIREMENTS:
1. Opening paragraph: Set the scene in YOUR narrator voice. Introduce the tension.
2. Middle: The battle unfolds. Give key characters DIALOGUE in their voice.
3. Climax: The decisive moment—make it DRAMATIC
4. Resolution: The aftermath. What does it mean?

CHARACTER VOICE EXAMPLES:
- King Aldric (wise ruler): "For the realm, we must hold."
- Queen Nyx (shadow assassin): "You dare challenge me? How... amusing."
- Sir Galahad (chivalrous): "For honor! For glory!"
- The Black Rider (fearsome): "Chaos rides with me!"

Write the story. Include at least 3 character quotes. Make it VIVID."""

        content = await self.client.complete(
            prompt,
            system_prompt=self._get_narrator_prompt(narrator_style),
            temperature=0.85,
            max_tokens=1000,
        )

        # Generate title
        n = NARRATORS[narrator_style]
        title_prompt = f"Create a {n['tone'].split(',')[0].lower()} title (3-6 words) for a story where {result}. Just the title."

        title = await self.client.complete(
            title_prompt,
            system_prompt=self._get_narrator_prompt(narrator_style),
            temperature=0.9,
            max_tokens=30,
        )

        return GameStory(
            format=StoryFormat.SHORT_STORY,
            narrator_style=narrator_style,
            content=content.strip(),
            title=title.strip().strip('"').strip("*"),
            piece_quotes_used=[],
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
