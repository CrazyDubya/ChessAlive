# ChessAlive Narrative Features Design

*Foundational design for Game Stories, Narrative Puzzles, and Position Analysis*

---

## Core Concept: The Narrator Layer

The key insight: **Pieces speak, but the Narrator tells the story.**

```
┌─────────────────────────────────────────────────────────┐
│                      GAME IN PROGRESS                    │
│                                                          │
│   Pieces generate commentary:                            │
│   • "For the kingdom!" - Sir Galahad                    │
│   • "You dare challenge me?" - Queen Nyx                │
│   • "The shadows grow long..." - Bishop Umbra           │
│                                                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   NARRATOR SYNTHESIS                     │
│                                                          │
│   Takes: Piece quotes + Move data + Game outcome         │
│   Produces: Dramatic narrative with embedded quotes      │
│                                                          │
│   "The knight charged forward, crying 'For the kingdom!' │
│    But Queen Nyx only smiled. 'You dare challenge me?'   │
│    In three moves, she would prove why none should."     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Architecture Overview

### Data Flow

```
DURING GAME:
┌──────────┐    ┌─────────────┐    ┌──────────────┐
│  Move    │───▶│ Commentary  │───▶│ Quote Buffer │
│  Made    │    │ Engine      │    │ (stored)     │
└──────────┘    └─────────────┘    └──────────────┘

POST-GAME (on button click):
┌──────────────┐    ┌────────────┐    ┌─────────────┐
│ Quote Buffer │───▶│  Narrator  │───▶│  Output     │
│ + PGN + Eval │    │  LLM       │    │  (story/    │
│              │    │            │    │   tweet)    │
└──────────────┘    └────────────┘    └─────────────┘
```

### New Component: GameRecorder

Captures everything needed for post-game narrative generation:

```python
@dataclass
class GameRecord:
    """Complete record of a game for narrative generation."""

    # Game data
    pgn: str                          # Full game notation
    moves: list[str]                  # SAN moves in order
    result: str                       # "1-0", "0-1", "1/2-1/2"
    termination: str                  # "checkmate", "resignation", "stalemate"

    # Commentary captured during game
    piece_quotes: list[PieceQuote]    # All commentary with context

    # Key moments (for analysis)
    captures: list[CaptureEvent]
    checks: list[CheckEvent]
    promotions: list[PromotionEvent]
    castling: list[CastlingEvent]

    # Optional: engine evaluation (if available)
    eval_history: list[float] | None  # Centipawn evals per move

@dataclass
class PieceQuote:
    """A piece's commentary with full context."""
    move_number: int
    piece_type: str                   # "knight", "queen", etc.
    piece_color: str                  # "white", "black"
    personality_name: str             # "Sir Galahad", "Queen Nyx"
    quote: str                        # The actual commentary
    context: str                      # "capture", "check", "move", etc.
    position_fen: str                 # Board state when quote was made
```

---

## Feature 1: AI Game Stories

### User Experience

```
┌─────────────────────────────────────────────┐
│            GAME OVER - White Wins           │
│                                             │
│  ♔ Checkmate! King Malachar has fallen.     │
│                                             │
│  ┌─────────────┐  ┌─────────────────────┐   │
│  │ 📖 Generate │  │ 🐦 Generate Tweet   │   │
│  │    Story    │  │                     │   │
│  └─────────────┘  └─────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ 📋 Copy PGN                         │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### Output Formats

#### Tweet Format (280 chars, shareable)

```
The Narrator prompt for tweets:
- Be dramatic and punchy
- Include 1 piece quote maximum
- End with intrigue or impact
- Use chess imagery
```

**Example outputs:**

> In 34 moves, a kingdom fell. "The shadows grow long," Bishop Umbra
> had warned. He was right. Queen Nyx's final strike came from nowhere.
> Checkmate. #ChessAlive

> "For the kingdom!" Sir Galahad cried, sacrificing himself on move 23.
> His sacrifice opened the diagonal. Three moves later, Queen Seraphina
> delivered justice. The Dark King is no more.

> They called it a draw, but Queen Nyx's laugh echoed across the board.
> "We'll meet again," she promised King Aldric. Both knew she was right.

#### Short Story Format (2-4 paragraphs)

```
The Narrator prompt for stories:
- Opening: Set the scene, introduce tension
- Middle: Key turning point with piece quotes
- Climax: The decisive moment
- Resolution: Aftermath and meaning
- Weave in 3-5 piece quotes naturally
```

**Example output:**

> The battle began as all great battles do—with patience. King Aldric's
> forces advanced methodically, pawns forming a wall of steel. "Hold the
> line," the Tower Guard commanded, his voice steady as stone.
>
> But war rewards the bold. On move 17, Sir Galahad saw his chance.
> "For the kingdom!" The knight leapt deep into enemy territory,
> forking King Malachar and his dark queen. Queen Nyx's eyes narrowed.
> "You dare challenge me?" She took the knight herself, but the damage
> was done.
>
> With the exchange won, Queen Seraphina swept across the board like
> divine vengeance. Bishop Umbra saw the end coming. "The shadows grow
> long," he murmured, but even shadows cannot stop checkmate.
>
> In 34 moves, the Dark Kingdom fell. King Aldric stood alone on the
> battlefield, victorious but weary. Somewhere, Queen Nyx's laughter
> still echoed. This war was won. But the game never truly ends.

### Narrator Personality

The Narrator is distinct from the pieces—an omniscient storyteller:

```python
NARRATOR_SYSTEM_PROMPT = """
You are the Narrator of ChessAlive, a dramatic storyteller who transforms
chess games into epic tales.

Your voice is:
- Omniscient but not cold—you care about the outcome
- Literary and evocative—use vivid imagery
- Respectful of the pieces' personalities—quote them accurately
- Aware this is chess—use chess terminology naturally

You have access to:
- The complete game record (moves, result)
- Quotes from the pieces during the game
- Key moments (captures, checks, promotions)

Your job is to weave these elements into compelling narrative.
Do NOT invent quotes—only use the ones provided.
DO add your own observations, dramatic framing, and storytelling.
"""
```

---

## Feature 2: Narrative Puzzles

### Core Structure

```python
@dataclass
class NarrativePuzzle:
    """A chess puzzle with story context."""

    # Puzzle data
    fen: str                          # Starting position
    solution: list[str]               # Correct moves (SAN)
    themes: list[str]                 # "back-rank", "fork", "pin", etc.
    difficulty: int                   # Rating (800-2500)

    # Narrative wrapper
    title: str                        # "The Last Stand"
    setup: str                        # Story context before puzzle
    piece_speaker: str                # Who narrates this puzzle
    piece_quote: str                  # Their framing of the challenge
    success_text: str                 # Shown on solving
    failure_text: str                 # Shown on wrong move

    # Optional progression
    chapter: str | None               # "The Western Campaign"
    sequence: int | None              # Puzzle 3 of 10
```

### Example Puzzle

```
┌─────────────────────────────────────────────────────────┐
│  CHAPTER 2: THE SIEGE OF THORNWALL                      │
│  Puzzle 7 of 10                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ♜ . . . . . ♜ ♚        (Black's position)             │
│  ♟ ♟ . . . ♟ ♟ ♟                                       │
│  . . . . . . . .                                        │
│  . . . . . . . .                                        │
│  . . . . . . . .                                        │
│  . . . . . . . .                                        │
│  ♙ ♙ ♙ . . ♙ ♙ ♙                                       │
│  ♖ . . . ♖ . ♔ .        (White's position)             │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  THE TOWER GUARD speaks:                                │
│                                                         │
│  "The enemy king hides behind his walls, thinking       │
│   himself safe. But these walls have a weakness.        │
│   The back rank is unguarded. My brother and I          │
│   can end this siege—if you show us the path."          │
│                                                         │
│  White to move. Find the checkmate.                     │
│                                                         │
│  ┌─────────────────────────────────────────────┐        │
│  │  Your move: [________________] [Submit]     │        │
│  └─────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

**On correct solution (Re8+):**

> THE TOWER GUARD: "The walls have fallen. Rxe8+... and when they
> block, my brother delivers the final blow. Thornwall is ours."
>
> ✓ Puzzle Complete! (+15 XP)

**On incorrect move:**

> THE TOWER GUARD: "No, that gives them time to escape. Look again—
> the back rank is the key. Where can we strike with lethal force?"

### Puzzle Categories

| Category | Description | Piece Narrator |
|----------|-------------|----------------|
| **Knight Trials** | Fork, discovered attack | Sir Galahad |
| **Queen's Gambit** | Queen sacrifices, dominance | Queen Seraphina |
| **Tower Defense** | Back rank, rook endgames | Tower Guard |
| **Bishop's Cunning** | Diagonals, fianchetto | Bishop Luminos |
| **Pawn's Journey** | Promotion, pawn structure | Footsoldier |
| **King's Peril** | King safety, escaping check | King Aldric |
| **Shadow Tactics** | Traps, defensive resources | Queen Nyx |

### Puzzle Sources

For MVP, curate puzzles from:
- Lichess puzzle database (open source, 3M+ puzzles)
- Add narrative wrapper via LLM generation
- Tag with appropriate piece narrator based on theme

---

## Feature 3: Position Analysis

### Trigger Points

Analysis activates on these game events:

| Event | Detection | Piece Response |
|-------|-----------|----------------|
| **Blunder** | Eval swings -2.0+ | Lamenting, explaining mistake |
| **Brilliant** | Eval swings +2.0+ unexpectedly | Celebrating, explaining insight |
| **Turning Point** | Eval crosses 0 threshold | Narrative tension shift |
| **Missed Win** | Engine shows mate was available | "What could have been" |
| **Piece Sacrifice** | Material given for advantage | Dramatic sacrifice narrative |

### Analysis Output Structure

```python
@dataclass
class PositionInsight:
    """Analysis of a key moment from piece perspective."""

    move_number: int
    move_san: str                     # The move played
    eval_before: float                # Centipawn before
    eval_after: float                 # Centipawn after
    insight_type: str                 # "blunder", "brilliant", etc.

    # Piece commentary
    primary_piece: str                # Main speaker
    primary_quote: str                # Their perspective

    # Optional second opinion
    secondary_piece: str | None       # Another piece's view
    secondary_quote: str | None

    # Narrator synthesis
    narrator_context: str             # What this meant for the game
```

### Example Analysis

```
┌─────────────────────────────────────────────────────────┐
│  GAME ANALYSIS - Your game vs. Stockfish               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ═══ TURNING POINT: Move 23 ═══                        │
│                                                         │
│  You played: Nf5?                                       │
│  Evaluation: +1.2 → -0.8                                │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ SIR GALAHAD:                                    │    │
│  │ "I saw the enemy queen and my blood ran hot.    │    │
│  │  The leap to f5 felt like destiny. But I was    │    │
│  │  wrong. Sometimes the bravest act is to wait."  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ BISHOP LUMINOS:                                 │    │
│  │ "Rd1 was the move. The d-file was our path to   │    │
│  │  victory. Patience over glory—always."          │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  NARRATOR: "This was the moment the tide turned.        │
│  White's advantage, built over 22 careful moves,        │
│  evaporated in a single leap. The knight's eagerness    │
│  would cost the kingdom dearly."                        │
│                                                         │
│  Better was: Rd1 (maintaining +1.2)                     │
│  [Show board] [Next insight →]                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Analysis Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Quick Summary** | Top 3 moments only | Post-game glance |
| **Full Analysis** | All significant moments | Deep learning |
| **Piece Focus** | Filter by specific piece | "How did my knights do?" |
| **Story Mode** | Narrative flow through game | Entertainment + education |

---

## UI Integration Points

### CLI Interface

```
Game Over! White wins by checkmate.

What would you like to do?
  [1] Generate Story
  [2] Generate Tweet
  [3] Analyze Game
  [4] New Game
  [5] Quit

> 1

Generating story...

═══════════════════════════════════════════════════════════
THE FALL OF THE DARK KINGDOM
═══════════════════════════════════════════════════════════

The battle began as all great battles do—with patience...
[full story output]

═══════════════════════════════════════════════════════════

[C]opy to clipboard  [T]weet version  [B]ack to menu
```

### GUI Interface

```
┌─────────────────────────────────────────────────────────┐
│  [New Game]  [Load]  [Save]  │  GAME OVER              │
├─────────────────────────────────────────────────────────┤
│                              │                          │
│      CHESS BOARD             │   COMMENTARY PANEL       │
│                              │                          │
│      ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜        │   Sir Galahad:          │
│      ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟        │   "For the kingdom!"    │
│      . . . . . . . .        │                          │
│      . . . . . . . .        │   Queen Nyx:            │
│      . . . . . . . .        │   "Checkmate. How...    │
│      . . . . . . . .        │    predictable."         │
│      ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙        │                          │
│      ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖        │                          │
│                              │                          │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │
│  │ 📖 Story     │ │ 🐦 Tweet     │ │ 🔍 Analysis  │     │
│  └──────────────┘ └──────────────┘ └──────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (Core Infrastructure)

```
□ GameRecorder class - capture quotes during play
□ PieceQuote storage - persist quotes with context
□ Narrator LLM prompt - define storyteller voice
□ Basic UI buttons - Story/Tweet/Analysis placeholders
```

### Phase 2: Game Stories

```
□ Tweet generation endpoint
□ Short story generation endpoint
□ Copy to clipboard functionality
□ Output formatting (CLI + GUI)
```

### Phase 3: Position Analysis

```
□ Engine evaluation integration (optional Stockfish)
□ Key moment detection logic
□ Piece perspective prompts for analysis
□ Analysis viewer UI
```

### Phase 4: Narrative Puzzles

```
□ Puzzle data structure
□ Puzzle database (start with 50-100 curated)
□ Narrative wrapper generation
□ Puzzle UI (separate from main game)
□ Progress tracking
```

---

## Narrator Prompt Templates

### For Tweets

```
You are the Narrator of ChessAlive. Generate a tweet (max 280 chars)
about this chess game.

Game result: {result}
Total moves: {move_count}
Key moment: {key_moment}
Piece quotes from the game:
{quotes}

Requirements:
- Maximum 280 characters
- Dramatic and punchy
- Include at most ONE piece quote (shortened if needed)
- Use #ChessAlive hashtag
- End with impact or intrigue
```

### For Stories

```
You are the Narrator of ChessAlive, an epic storyteller.

Write a short story (3-4 paragraphs) about this chess game.

Game data:
- Result: {result}
- Moves: {move_count}
- Termination: {termination}
- Key moments: {key_moments}

Piece quotes captured during the game:
{quotes}

Requirements:
- Opening: Set scene and tension
- Middle: The turning point (use piece quotes)
- Climax: The decisive moment
- Resolution: Aftermath and meaning
- Weave in 3-5 piece quotes naturally
- DO NOT invent quotes—only use provided ones
- Add your own dramatic observations
```

### For Position Analysis

```
You are {piece_name}, a chess piece with this personality:
{personality_description}

Analyze this moment from YOUR perspective:
- Move played: {move}
- Position before: {fen_before}
- Position after: {fen_after}
- Evaluation change: {eval_before} → {eval_after}
- This was a: {insight_type}

Speak in character. Explain:
- What you saw (or missed)
- Why this move mattered
- What should have happened (if a mistake)

Keep response to 2-3 sentences. Stay in character.
```

---

## Open Questions for Future Design

1. **Quote Selection**: When many quotes exist, how do we pick the best ones for stories?
   - By dramatic weight?
   - By game importance (captures, checks)?
   - Let the LLM choose?

2. **Puzzle Curation**: Generate narratives on-the-fly or pre-generate and store?
   - On-the-fly: More variety, higher latency
   - Pre-generated: Fast, but less dynamic

3. **Engine Integration**: Require Stockfish for analysis, or make it optional?
   - Required: Better insights
   - Optional: Simpler setup for casual users

4. **Narrator Consistency**: Should the Narrator have memory across games?
   - "The last time these armies met, White won in 28 moves..."

---

*Design document v1.0 - Ready for implementation feedback*
