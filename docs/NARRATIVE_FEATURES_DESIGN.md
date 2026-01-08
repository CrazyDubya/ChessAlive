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
│           NARRATOR SYNTHESIS (Genre-Specific)            │
│                                                          │
│   User selects genre → Narrator personality chosen       │
│   Narrator weaves ALL quotes into cohesive story         │
│   Adds own observations, drama, and storytelling         │
│                                                          │
│   EPIC FANTASY (The Chronicler):                         │
│   "The knight charged forward, crying 'For the kingdom!' │
│    But Queen Nyx only smiled. 'You dare challenge me?'   │
│    In three moves, she would prove why none should."     │
│                                                          │
│   NOIR DETECTIVE (The Gumshoe):                          │
│   "The knight made his move. Brave kid. 'For the         │
│    kingdom,' he said. The Queen's lips curled. 'You      │
│    dare?' Three moves later, he was off the board."      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Genre System: Narrator Personalities

Each genre has multiple potential narrators with distinct voices. The LLM receives
ALL piece quotes and weaves them into a story that matches the narrator's style.

### Genre: Epic Fantasy

| Narrator | Voice | Style |
|----------|-------|-------|
| **The Chronicler** | Ancient, reverent, sweeping | "In the age of kings, when armies clashed upon fields of sixty-four squares..." |
| **The Bard** | Lyrical, dramatic, musical | "Sing, O muse, of the knight who dared challenge darkness itself!" |
| **The War Scribe** | Military, tactical, observational | "The western flank collapsed at move 23. The knight's sacrifice was... unexpected." |

### Genre: Noir/Hardboiled

| Narrator | Voice | Style |
|----------|-------|-------|
| **The Gumshoe** | Cynical, world-weary, wry | "The Queen was dead. Cornered on h7 with nowhere to run. I'd seen it coming for twelve moves." |
| **The Reporter** | Urgent, punchy, sensational | "CHECKMATE IN THE THIRD! Dark King Falls in 34-Move Thriller!" |
| **The Witness** | Nervous, observational, unreliable | "I saw the whole thing. The knight, he just... jumped. Right into danger. Who does that?" |

### Genre: Sports Commentary

| Narrator | Voice | Style |
|----------|-------|-------|
| **The Play-by-Play** | Excited, immediate, energetic | "AND THE KNIGHT TAKES! What a move! The crowd goes wild!" |
| **The Color Commentator** | Analytical, contextual, seasoned | "You see, Jim, what makes this sacrifice brilliant is the diagonal it opens..." |
| **The Podcast Host** | Conversational, enthusiastic, modern | "Okay so like, this game? Absolutely bonkers. Let me break it down for you." |

### Genre: Gothic Horror

| Narrator | Voice | Style |
|----------|-------|-------|
| **The Archivist** | Dusty, ominous, discovering | "I found these records in the basement. The game they describe... it should not have been possible." |
| **The Survivor** | Traumatized, fragmented, warning | "Don't play at midnight. I did once. The pieces... they spoke to me." |
| **The Entity** | Cold, alien, observing | "We have watched this ritual for centuries. The humans call it 'chess.' We call it... selection." |

### Genre: Comedy/Satire

| Narrator | Voice | Style |
|----------|-------|-------|
| **The Bumbling Announcer** | Confused, enthusiastic, wrong | "And the... horsey? The horsey takes the castle! Wait, can it do that?" |
| **The Sarcastic Observer** | Dry, cutting, intellectual | "Ah yes, another knight sacrifice. How terribly original." |
| **The Pieces' Therapist** | Sympathetic, clinical, absurd | "The pawn expressed feelings of inadequacy today. We're making progress." |

### Genre: Documentary

| Narrator | Voice | Style |
|----------|-------|-------|
| **The Nature Narrator** (Attenborough-style) | Gentle, wondering, scientific | "Here we observe the knight in its natural habitat. Notice how it approaches in an L-shape..." |
| **The Historian** | Academic, contextual, thorough | "This opening, first recorded in 1847, would prove decisive in the moves that followed." |
| **The True Crime Host** | Serious, building tension, revelatory | "But what no one knew... was that the Bishop had been planning this for seven moves." |

---

## Genre-Specific Piece Personalities

For complete genre immersion, **the pieces themselves** must speak in genre-appropriate voices.
The current fantasy personalities (King Aldric, etc.) become one of many "Personality Sets."

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│  GAME SETUP: Choose Your Genre                          │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ ⚔️ Epic     │  │ 🔍 Noir     │  │ 🎙️ Sports   │      │
│  │   Fantasy   │  │             │  │             │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                          │
│  Selected: Noir                                          │
│  Pieces will speak as: The Kingpin, The Dame, etc.      │
│  Story narrated by: The Gumshoe                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
             ┌─────────────────────────┐
             │  DURING GAMEPLAY:       │
             │  Pieces generate noir-  │
             │  style commentary       │
             │                         │
             │  "End of the line,      │
             │   pal." - The Muscle    │
             └─────────────────────────┘
                           │
                           ▼
             ┌─────────────────────────┐
             │  POST-GAME:             │
             │  Noir narrator weaves   │
             │  noir quotes into       │
             │  noir story             │
             └─────────────────────────┘
```

### Personality Set Structure

```python
@dataclass
class PiecePersonality:
    """A single piece's character in a genre."""
    piece_type: str                   # "king", "queen", "rook", etc.
    color: str                        # "white", "black"
    name: str                         # "The Kingpin", "King Aldric"

    # Character traits
    voice_description: str            # How they speak
    personality_traits: list[str]     # Key characteristics
    speech_patterns: list[str]        # Verbal quirks, catchphrases

    # Behavioral modifiers
    aggression: float                 # 0.0 - 1.0
    eloquence: float                  # 0.0 - 1.0
    humor: float                      # 0.0 - 1.0

    # Example quotes for few-shot prompting
    example_move: str                 # Quote when making a move
    example_capture: str              # Quote when capturing
    example_captured: str             # Quote when being captured
    example_check: str                # Quote when giving/receiving check

@dataclass
class PersonalitySet:
    """Complete set of 12 piece personalities for a genre."""
    genre: str
    name: str                         # "The Criminal Underworld"
    description: str                  # Flavor text
    white_pieces: dict[str, PiecePersonality]  # king, queen, rook, bishop, knight, pawn
    black_pieces: dict[str, PiecePersonality]
```

---

### Set: Epic Fantasy (Current Default)

*The eternal war between the Kingdom of Light and the Dark Realm.*

#### White Pieces - The Kingdom of Light

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | King Aldric | Wise, measured, regal | "For the realm, we stand united." |
| **Queen** | Queen Seraphina | Fierce, commanding, passionate | "They will learn to fear the light!" |
| **Rook** | Tower Guard | Stoic, military, direct | "The walls hold. We hold." |
| **Bishop** | Bishop Luminos | Scholarly, cryptic, patient | "The path reveals itself to those who wait." |
| **Knight** | Sir Galahad | Chivalrous, bold, honorable | "For the kingdom! For glory!" |
| **Pawn** | Footsoldier | Humble, earnest, hopeful | "One step closer to becoming something more." |

#### Black Pieces - The Dark Realm

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | King Malachar | Cold, calculating, patient | "Every move brings me closer to victory." |
| **Queen** | Queen Nyx | Deadly, mysterious, mocking | "You dare challenge me? How... amusing." |
| **Rook** | Dark Tower | Ominous, sparse, inevitable | "The shadow falls." |
| **Bishop** | Bishop Umbra | Prophetic, unsettling, knowing | "I have seen how this ends." |
| **Knight** | The Black Rider | Wild, intimidating, chaotic | "Chaos rides with me!" |
| **Pawn** | Dark Infantry | Grim, devoted, fatalistic | "We serve until we fall." |

---

### Set: Noir/Hardboiled

*The gritty underworld where every piece has an angle.*

#### White Pieces - The Law (Morally Gray)

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | The Commissioner | Tired, pragmatic, burdened | "I've seen too much to believe in clean wins." |
| **Queen** | The DA | Sharp, ambitious, ruthless | "I'll get my conviction. One way or another." |
| **Rook** | The Muscle | Terse, threatening, loyal | "Boss says move, I move." |
| **Bishop** | The Fixer | Smooth, connected, opportunistic | "Everyone has a price. I just find it." |
| **Knight** | The Detective | Cynical, clever, haunted | "I've got a bad feeling about this one." |
| **Pawn** | The Beat Cop | Nervous, idealistic, expendable | "Just trying to make it to retirement." |

#### Black Pieces - The Syndicate

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | The Kingpin | Calm, menacing, untouchable | "You think you can take what's mine?" |
| **Queen** | The Dame | Seductive, dangerous, calculating | "Oh honey, you have no idea who you're dealing with." |
| **Rook** | The Enforcer | Brutal, silent, efficient | "Nothing personal." |
| **Bishop** | The Consigliere | Elegant, advisory, deadly | "I would advise against that move." |
| **Knight** | The Wildcard | Unpredictable, flashy, reckless | "Let's make this interesting!" |
| **Pawn** | The Fall Guy | Desperate, disposable, hoping | "Maybe this time I'll catch a break." |

---

### Set: Sports Commentary

*Every game is the championship match.*

#### White Pieces - Home Team

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | The Captain | Motivational, focused, leading | "We've trained for this. Let's execute!" |
| **Queen** | The MVP | Confident, dominant, clutch | "This is MY court!" |
| **Rook** | The Veteran | Experienced, steady, reliable | "I've seen every play. Nothing surprises me." |
| **Bishop** | The Strategist | Analytical, precise, cerebral | "Watch the angles. Always watch the angles." |
| **Knight** | The Rookie Star | Eager, explosive, highlight-reel | "DID YOU SEE THAT?!" |
| **Pawn** | The Bench Player | Supportive, hungry, waiting | "Put me in, coach!" |

#### Black Pieces - Away Team

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | The Rival Captain | Intense, focused, respected | "May the best team win. It's going to be us." |
| **Queen** | The Superstar | Flashy, trash-talking, elite | "Y'all aren't ready for what's coming!" |
| **Rook** | The Wall | Defensive, intimidating, immovable | "Nothing gets past me." |
| **Bishop** | The Coach's Son | Smart, underestimated, sneaky | "They never see me coming." |
| **Knight** | The Showboat | Athletic, dramatic, crowd-pleasing | "Let's give 'em a show!" |
| **Pawn** | The Walk-On | Determined, overlooked, proving | "I earned my spot." |

---

### Set: Gothic Horror

*The pieces are not what they seem. Perhaps they never were.*

#### White Pieces - The Haunted

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | The Last Lord | Weary, cursed, tragic | "This castle holds us all prisoner." |
| **Queen** | The Specter Bride | Ethereal, mournful, cold | "Death did not part us. It bound us." |
| **Rook** | The Stone Guardian | Ancient, rumbling, bound | "I have watched. For centuries, I have watched." |
| **Bishop** | The Mad Priest | Fervent, unhinged, prophetic | "The old gods stir! Can you not feel them?!" |
| **Knight** | The Revenant | Hollow, duty-bound, echoing | "I... remember... fighting. Always fighting." |
| **Pawn** | The Lost Soul | Confused, plaintive, fading | "Why am I still here?" |

#### Black Pieces - The Darkness

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | The Undying | Patient, inevitable, ancient | "I was here before. I will be here after." |
| **Queen** | The Blood Countess | Sensual, cruel, hungry | "Your fear is... exquisite." |
| **Rook** | The Obelisk | Wordless, oppressive, wrong | "*grinding stone sounds*" |
| **Bishop** | The Whisperer | Insidious, tempting, everywhere | "Listen closely... I have such secrets..." |
| **Knight** | The Nightmare | Surreal, shifting, laughing | "You're still dreaming. You never woke up." |
| **Pawn** | The Hollow | Empty, echoing, consuming | "Join us. It's so peaceful here." |

---

### Set: Comedy/Satire

*Chess, but nobody really knows what they're doing.*

#### White Pieces - Team Overconfident

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | King Jeff | Clueless, delegating, CEO-brained | "I'm more of a big-picture guy." |
| **Queen** | Queen Karen | Demanding, complaining, entitled | "I need to speak to the other king's manager." |
| **Rook** | Castle McMansion | Pretentious, insecure, overbuilt | "I'm not just a tower, I'm a LIFESTYLE." |
| **Bishop** | Bishop Chad | Bro-culture, diagonal-obsessed | "Bro, I only move diagonally. It's a whole THING." |
| **Knight** | Sir Hops-a-Lot | Confused, L-shaped, apologetic | "Sorry, sorry, coming through! Sorry!" |
| **Pawn** | Pawn #5 | Existential, numbered, philosophical | "Why am I Pawn FIVE? What happened to one through four?" |

#### Black Pieces - Team Chaotic

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | King Dave | Lazy, hiding, delegating | "Look, I'm really more of a staying-alive guy." |
| **Queen** | Drama Queen | Theatrical, extra, spotlight-seeking | "Finally! A STAGE worthy of my TALENTS!" |
| **Rook** | The Introvert | Anxious, corner-loving, reluctant | "I'm fine here in the corner, thanks." |
| **Bishop** | Bishop Actually | Pedantic, correcting, insufferable | "Well, ACTUALLY, that's not how the Sicilian—" |
| **Knight** | Horse With No Name | Mysterious, non-sequitur, random | "The desert holds many secrets. Also, I can jump." |
| **Pawn** | The Intern | Overwhelmed, underpaid, hopeful | "Is this part of my professional development?" |

---

### Set: Documentary

*Observing chess as a natural phenomenon.*

#### White Pieces - Specimen Set Alpha

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | Alpha Rex | Territorial, protective, signaling | "*asserts dominance through strategic positioning*" |
| **Queen** | Alpha Domina | Apex hunter, ranging, efficient | "The hunting grounds are mine." |
| **Rook** | Turret Erectus | Structural, defending, ancient | "*holds position with remarkable stillness*" |
| **Bishop** | Diagonis Major | Specialized, adapted, precise | "Evolution favored the diagonal approach." |
| **Knight** | Equus Mobilis | Leaping, unpredictable, adaptive | "*demonstrates unique L-shaped locomotion*" |
| **Pawn** | Pedes Communis | Colonial, advancing, transformative | "*moves steadily toward metamorphosis zone*" |

#### Black Pieces - Specimen Set Beta

| Piece | Name | Voice | Example Quote |
|-------|------|-------|---------------|
| **King** | Beta Rex | Cornered, defensive, calculating | "The species survives through caution." |
| **Queen** | Beta Domina | Counter-hunter, territorial, aggressive | "The rival approaches. Fascinating." |
| **Rook** | Turret Noctis | Shadowed, patient, striking | "*exhibits classic ambush predator behavior*" |
| **Bishop** | Diagonis Minor | Flanking, opportunistic, evolved | "A different diagonal. A different destiny." |
| **Knight** | Equus Umbra | Erratic, threatening, displayed | "*the warning dance begins*" |
| **Pawn** | Pedes Obscura | Massed, advancing, inevitable | "*the colony marches as one*" |

---

### Personality Set Registry

```python
PERSONALITY_SETS: dict[str, PersonalitySet] = {
    "epic_fantasy": EpicFantasySet,      # King Aldric, Queen Seraphina...
    "noir": NoirSet,                      # The Kingpin, The Dame...
    "sports": SportsSet,                  # The Captain, The MVP...
    "gothic_horror": GothicHorrorSet,     # The Last Lord, The Blood Countess...
    "comedy": ComedySet,                  # King Jeff, Queen Karen...
    "documentary": DocumentarySet,        # Alpha Rex, Specimen Set Alpha...
}

def get_piece_personality(
    genre: str,
    piece_type: str,
    color: str
) -> PiecePersonality:
    """Get the personality for a specific piece in a genre."""
    personality_set = PERSONALITY_SETS[genre]
    pieces = personality_set.white_pieces if color == "white" else personality_set.black_pieces
    return pieces[piece_type]
```

---

### Example: Same Move, Different Genres

**A knight captures an enemy bishop on move 17.**

| Genre | Piece | Quote |
|-------|-------|-------|
| **Epic Fantasy** | Sir Galahad | "For the kingdom! Your dark magic ends here, sorcerer!" |
| **Noir** | The Detective | "End of the line, Fixer. You should've stayed out of this." |
| **Sports** | The Rookie Star | "WHAT A PLAY! Did you SEE that?! Highlight reel!" |
| **Gothic Horror** | The Revenant | "I remember... you. We met before. In another game..." |
| **Comedy** | Sir Hops-a-Lot | "Oh no, did I land on you? I'm SO sorry, I can never tell where I'm going!" |
| **Documentary** | Equus Mobilis | "*executes successful predation via unique L-shaped approach*" |

---

## Narrator Selection Flow

```
┌─────────────────────────────────────────────────────────┐
│                    POST-GAME SCREEN                      │
│                                                          │
│  Generate Story As:                                      │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ ⚔️ Epic     │  │ 🔍 Noir     │  │ 🎙️ Sports   │      │
│  │   Fantasy   │  │             │  │             │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ 🦇 Gothic   │  │ 😂 Comedy   │  │ 🎬 Docu-    │      │
│  │   Horror    │  │             │  │   mentary   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                          │
│  Selected: Epic Fantasy                                  │
│  Narrator: [The Chronicler ▼]                           │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │ 📖 Full Story   │  │ 🐦 Tweet        │               │
│  └─────────────────┘  └─────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

---

## Narrator Data Structure

```python
@dataclass
class NarratorPersonality:
    """Defines a narrator's voice and style."""

    id: str                           # "chronicler", "gumshoe", etc.
    name: str                         # "The Chronicler"
    genre: str                        # "epic_fantasy", "noir", etc.

    # Voice characteristics
    voice_description: str            # How they speak
    vocabulary_hints: list[str]       # Words they favor
    sentence_style: str               # Short/long, simple/complex
    emotional_range: str              # Reserved, dramatic, etc.

    # Storytelling approach
    opening_style: str                # How they begin stories
    quote_integration: str            # How they weave in piece quotes
    tension_building: str             # How they create drama
    ending_style: str                 # How they conclude

    # Example snippets (for few-shot prompting)
    example_opening: str
    example_quote_weave: str
    example_climax: str
    example_closing: str

# Registry of all narrators
NARRATORS: dict[str, list[NarratorPersonality]] = {
    "epic_fantasy": [chronicler, bard, war_scribe],
    "noir": [gumshoe, reporter, witness],
    "sports": [play_by_play, color_commentator, podcast_host],
    "gothic_horror": [archivist, survivor, entity],
    "comedy": [bumbling_announcer, sarcastic_observer, therapist],
    "documentary": [nature_narrator, historian, true_crime_host],
}
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

### Puzzle Sources: Lichess + Flavor System

**Primary Source**: Lichess puzzle database (open source, 3M+ puzzles)
**Enhancement**: Wrap each puzzle in narrative "flavors" via LLM generation
**Future**: Custom-authored puzzles with hand-crafted narratives

### Lichess Integration

```python
@dataclass
class LichessPuzzle:
    """Raw puzzle data from Lichess database."""
    puzzle_id: str
    fen: str
    moves: list[str]           # Solution moves (UCI format)
    rating: int                # Difficulty rating
    themes: list[str]          # ["fork", "middlegame", "short"]
    game_url: str | None       # Source game if available

# Lichess CSV format (puzzles are ~300MB compressed):
# PuzzleId,FEN,Moves,Rating,RatingDeviation,Popularity,NbPlays,Themes,GameUrl
#
# Download from: https://database.lichess.org/#puzzles
```

### The Flavor System

Flavors are narrative "skins" that transform raw puzzles into story experiences.
Each flavor has its own narrator voice and thematic framing.

```python
@dataclass
class PuzzleFlavor:
    """A narrative wrapper style for puzzles."""

    id: str                           # "kingdom_siege", "detective_case"
    name: str                         # "Kingdom Under Siege"
    genre: str                        # Links to narrator genres

    # Narrative elements
    setting_description: str          # World/context description
    narrator_pool: list[str]          # Which narrators can voice this flavor
    piece_role_map: dict[str, str]    # How pieces are described in this flavor

    # Theme mappings (Lichess theme → flavor narrative)
    theme_narratives: dict[str, ThemeNarrative]

    # Difficulty framing
    difficulty_descriptions: dict[str, str]  # Rating range → narrative framing

@dataclass
class ThemeNarrative:
    """How a chess theme is narrated in a specific flavor."""
    lichess_theme: str                # "fork", "backRankMate", etc.
    narrative_setup: str              # Story framing for this theme
    piece_narrator: str               # Which piece type narrates
    success_template: str             # Victory text template
    failure_template: str             # Retry text template
```

### Flavor Examples

#### Flavor: Kingdom Under Siege (Epic Fantasy)

```python
KINGDOM_SIEGE_FLAVOR = PuzzleFlavor(
    id="kingdom_siege",
    name="Kingdom Under Siege",
    genre="epic_fantasy",
    setting_description="""
        The Dark Kingdom has invaded. Castle walls crumble.
        Each puzzle is a battle in the war for survival.
    """,
    narrator_pool=["chronicler", "war_scribe"],
    piece_role_map={
        "king": "Your Liege",
        "queen": "The Queen Commander",
        "rook": "Tower Defenders",
        "bishop": "Battle Mages",
        "knight": "Cavalry Champions",
        "pawn": "Brave Infantry",
    },
    theme_narratives={
        "backRankMate": ThemeNarrative(
            lichess_theme="backRankMate",
            narrative_setup="The enemy king cowers behind his walls, thinking himself safe. But the walls themselves are his prison.",
            piece_narrator="rook",
            success_template="The walls have fallen! {piece} delivers the killing blow.",
            failure_template="No—that gives them time to shore up defenses. Look again.",
        ),
        "fork": ThemeNarrative(
            lichess_theme="fork",
            narrative_setup="Two enemy commanders stand vulnerable. One strike can threaten both.",
            piece_narrator="knight",
            success_template="A devastating charge! Both targets scatter, but the damage is done.",
            failure_template="A wasted charge. Regroup and find where two enemies align.",
        ),
        "pin": ThemeNarrative(
            lichess_theme="pin",
            narrative_setup="The enemy hides behind their own soldiers. But what protects them... also traps them.",
            piece_narrator="bishop",
            success_template="Pinned like insects to a board. They cannot move without losing everything.",
            failure_template="The pin isn't there. Look for a piece hiding behind another.",
        ),
    },
    difficulty_descriptions={
        "800-1200": "A skirmish at the border. Trust your instincts.",
        "1200-1600": "A pitched battle. Think before you strike.",
        "1600-2000": "A siege of cunning. Every move must be precise.",
        "2000+": "The Dark Lord's inner sanctum. Only masters survive.",
    },
)
```

#### Flavor: Case Files (Noir Detective)

```python
CASE_FILES_FLAVOR = PuzzleFlavor(
    id="case_files",
    name="The Case Files",
    genre="noir",
    setting_description="""
        The city's dark. The board's darker. Every puzzle is a case.
        Find the solution before time runs out.
    """,
    narrator_pool=["gumshoe", "witness"],
    piece_role_map={
        "king": "The Kingpin",
        "queen": "The Femme Fatale",
        "rook": "The Muscle",
        "bishop": "The Fixer",
        "knight": "The Wildcard",
        "pawn": "The Fall Guy",
    },
    theme_narratives={
        "backRankMate": ThemeNarrative(
            lichess_theme="backRankMate",
            narrative_setup="The Kingpin's holed up in his penthouse. Thinks his bodyguards make him untouchable. They don't.",
            piece_narrator="rook",
            success_template="Nowhere to run. The Muscle walks right in. Case closed.",
            failure_template="Wrong angle. The Kingpin's got an escape route you're missing.",
        ),
        "sacrifice": ThemeNarrative(
            lichess_theme="sacrifice",
            narrative_setup="Sometimes you gotta give something up to get what you need. The question is: what's worth losing?",
            piece_narrator="pawn",
            success_template="The Fall Guy takes the hit. But it cracks the case wide open.",
            failure_template="That's not a sacrifice—that's just a loss. Think harder.",
        ),
    },
    difficulty_descriptions={
        "800-1200": "A simple shakedown. Even a rookie could crack it.",
        "1200-1600": "Getting complicated. Bring your notepad.",
        "1600-2000": "Cold case territory. The clues don't add up easy.",
        "2000+": "The perfect crime. Almost.",
    },
)
```

#### Flavor: Nature Documentary

```python
NATURE_DOC_FLAVOR = PuzzleFlavor(
    id="nature_documentary",
    name="Chess in the Wild",
    genre="documentary",
    setting_description="""
        Here we observe the chess pieces in their natural habitat.
        Watch as predator and prey dance their ancient dance.
    """,
    narrator_pool=["nature_narrator"],
    piece_role_map={
        "king": "the patriarch",
        "queen": "the apex predator",
        "rook": "the territorial guardian",
        "bishop": "the cunning stalker",
        "knight": "the unpredictable hunter",
        "pawn": "the humble forager",
    },
    theme_narratives={
        "fork": ThemeNarrative(
            lichess_theme="fork",
            narrative_setup="The knight spots two targets at once. In nature, this is called... opportunistic hunting.",
            piece_narrator="knight",
            success_template="Extraordinary. The knight claims both territories in a single bound.",
            failure_template="The prey escapes. The knight must learn patience.",
        ),
        "discoveredAttack": ThemeNarrative(
            lichess_theme="discoveredAttack",
            narrative_setup="Watch carefully. One piece moves... revealing another's line of attack. A coordinated strike.",
            piece_narrator="bishop",
            success_template="Nature's teamwork at its finest. The discovered attack claims its victim.",
            failure_template="The coordination failed. Both hunters must align perfectly.",
        ),
    },
    difficulty_descriptions={
        "800-1200": "A gentle meadow. The patterns here are easy to spot.",
        "1200-1600": "The deep forest. Danger lurks, but so does opportunity.",
        "1600-2000": "The treacherous mountains. Only the skilled survive.",
        "2000+": "The abyssal depths. Mysteries few have witnessed.",
    },
)

# Registry of all flavors
PUZZLE_FLAVORS: dict[str, PuzzleFlavor] = {
    "kingdom_siege": KINGDOM_SIEGE_FLAVOR,
    "case_files": CASE_FILES_FLAVOR,
    "nature_documentary": NATURE_DOC_FLAVOR,
    # Future flavors...
    # "sports_highlight": SPORTS_FLAVOR,
    # "haunted_board": HORROR_FLAVOR,
    # "comedy_club": COMEDY_FLAVOR,
}
```

### Puzzle Generation Pipeline

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Lichess DB     │────▶│  Theme Mapper   │────▶│  Flavor Wrapper │
│  (raw puzzles)  │     │  (categorize)   │     │  (narrativize)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  NarrativePuzzle│
                                               │  (ready to play)│
                                               └─────────────────┘
```

```python
class PuzzleGenerator:
    """Transforms raw Lichess puzzles into narrative experiences."""

    def __init__(self, flavor: PuzzleFlavor, llm_client: LLMClient):
        self.flavor = flavor
        self.llm = llm_client

    def wrap_puzzle(self, raw: LichessPuzzle) -> NarrativePuzzle:
        """Add narrative wrapper to a raw puzzle."""

        # Find matching theme narrative
        primary_theme = self._get_primary_theme(raw.themes)
        theme_narrative = self.flavor.theme_narratives.get(primary_theme)

        if theme_narrative:
            # Use pre-defined narrative for known themes
            return self._build_from_template(raw, theme_narrative)
        else:
            # Generate narrative via LLM for unknown themes
            return self._generate_narrative(raw)

    def _build_from_template(
        self, raw: LichessPuzzle, theme: ThemeNarrative
    ) -> NarrativePuzzle:
        """Build puzzle from pre-defined theme template."""
        return NarrativePuzzle(
            fen=raw.fen,
            solution=raw.moves,
            themes=raw.themes,
            difficulty=raw.rating,
            title=self._generate_title(raw),
            setup=theme.narrative_setup,
            piece_speaker=self.flavor.piece_role_map[theme.piece_narrator],
            piece_quote=theme.narrative_setup,
            success_text=theme.success_template,
            failure_text=theme.failure_template,
        )

    async def _generate_narrative(self, raw: LichessPuzzle) -> NarrativePuzzle:
        """Use LLM to generate narrative for non-templated themes."""
        prompt = f"""
        Generate a narrative wrapper for this chess puzzle in the
        "{self.flavor.name}" style ({self.flavor.genre} genre).

        Setting: {self.flavor.setting_description}

        Puzzle themes: {raw.themes}
        Difficulty: {raw.rating}

        Generate:
        1. A dramatic setup (2-3 sentences)
        2. A success message (1 sentence)
        3. A failure/retry message (1 sentence)
        4. Which piece type should narrate (from: {list(self.flavor.piece_role_map.keys())})

        Match the tone and style of the {self.flavor.genre} genre.
        """
        # ... LLM call and parsing
```

### Future: Custom Puzzle Authoring

Architecture supports hand-crafted puzzles with richer narratives:

```python
@dataclass
class CustomPuzzle(NarrativePuzzle):
    """Hand-authored puzzle with extended narrative."""

    # Extended story elements
    backstory: str | None             # Longer context
    character_dialogue: list[str]     # Multi-turn conversation
    branching_responses: dict         # Different responses for different wrong moves
    sequel_puzzle_id: str | None      # Chain puzzles into stories

    # Authorship
    author: str
    created_date: str
    is_premium: bool                  # For future monetization
```

---

## Feature 3: Position Analysis

### Stockfish Requirement

**Position Analysis REQUIRES Stockfish to be installed and configured.**

Without engine evaluation, we cannot reliably detect:
- Blunders vs. reasonable moves
- Brilliant sacrifices vs. mistakes
- Turning points in the game
- What the best move actually was

```
┌─────────────────────────────────────────────────────────┐
│  ⚠️  STOCKFISH REQUIRED FOR ANALYSIS                    │
│                                                          │
│  Position Analysis needs Stockfish to evaluate moves.    │
│                                                          │
│  Install Stockfish:                                      │
│  • macOS: brew install stockfish                        │
│  • Linux: apt install stockfish                         │
│  • Windows: Download from stockfishchess.org            │
│                                                          │
│  Then set STOCKFISH_PATH in your .env file              │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ [Install Guide]  [Skip Analysis]  [Try Anyway]  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Engine Integration Architecture

```python
class PositionAnalyzer:
    """Analyzes games using Stockfish + LLM narrative."""

    def __init__(self, stockfish_path: str):
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.eval_cache: dict[str, float] = {}

    def analyze_game(self, game: GameRecord) -> list[PositionInsight]:
        """Analyze all positions, return key moments."""
        insights = []
        board = chess.Board()

        for i, move in enumerate(game.moves):
            eval_before = self._evaluate(board)
            board.push_san(move)
            eval_after = self._evaluate(board)

            insight_type = self._classify_moment(eval_before, eval_after)
            if insight_type:
                insights.append(PositionInsight(
                    move_number=i + 1,
                    move_san=move,
                    eval_before=eval_before,
                    eval_after=eval_after,
                    insight_type=insight_type,
                    best_move=self._get_best_move(board),
                    # ... piece commentary added via LLM
                ))

        return insights

    def _evaluate(self, board: chess.Board) -> float:
        """Get centipawn evaluation for position."""
        info = self.engine.analyse(board, chess.engine.Limit(depth=18))
        score = info["score"].relative
        if score.is_mate():
            return 10000 if score.mate() > 0 else -10000
        return score.score() / 100  # Convert to pawns

    def _classify_moment(self, before: float, after: float) -> str | None:
        """Classify the significance of an eval change."""
        delta = after - before

        if delta <= -2.0:
            return "blunder"
        elif delta >= 2.0:
            return "brilliant"
        elif (before > 0.5 and after < -0.5) or (before < -0.5 and after > 0.5):
            return "turning_point"
        elif abs(before) > 5 and abs(after) < 1:
            return "missed_win"

        return None  # Not significant enough
```

### Trigger Points

Analysis activates on these game events (detected via Stockfish):

| Event | Detection | Piece Response |
|-------|-----------|----------------|
| **Blunder** | Eval swings -2.0+ pawns | Lamenting, explaining mistake |
| **Brilliant** | Eval swings +2.0+ pawns unexpectedly | Celebrating, explaining insight |
| **Turning Point** | Eval crosses ±0.5 threshold | Narrative tension shift |
| **Missed Win** | Engine shows winning position squandered | "What could have been" |
| **Piece Sacrifice** | Material given but eval improves | Dramatic sacrifice narrative |

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

### Quote Weaving Philosophy

The LLM's job is to **weave ALL provided quotes into a cohesive narrative**—not to select
the "best" ones. Every piece quote is part of the story. The narrator:

1. Receives ALL quotes captured during the game
2. Must incorporate each quote naturally into the narrative flow
3. Adds their own observations, transitions, and dramatic framing
4. Never invents new quotes, only uses what pieces actually said

This ensures every piece's voice is honored while the narrator provides structure.

### For Tweets (Genre-Aware)

```
You are {narrator_name}, a {genre} narrator for ChessAlive.

Your voice: {voice_description}
Your style: {style_example}

Generate a tweet (max 280 chars) about this chess game.

Game result: {result}
Total moves: {move_count}
Termination: {termination}

Piece quotes from the game (weave the most impactful into your tweet):
{all_quotes}

Requirements:
- Maximum 280 characters
- Match your narrator voice perfectly
- Include 1-2 piece quotes woven naturally
- End with impact appropriate to your style
- Include #ChessAlive
```

### For Stories (Genre-Aware)

```
You are {narrator_name}, a {genre} narrator for ChessAlive.

YOUR VOICE:
{voice_description}

YOUR STORYTELLING STYLE:
- Opening: {opening_style}
- Building tension: {tension_building}
- Quote integration: {quote_integration}
- Endings: {ending_style}

EXAMPLE OF YOUR VOICE:
"{example_opening}"

---

Write a story (3-4 paragraphs) about this chess game.

GAME DATA:
- Result: {result}
- Total moves: {move_count}
- Termination: {termination}
- Key moments: {key_moments_summary}

PIECE QUOTES TO WEAVE INTO YOUR NARRATIVE:
(You MUST incorporate ALL of these quotes naturally into your story)

{all_quotes_with_context}

REQUIREMENTS:
- Write in YOUR voice—stay in character as {narrator_name}
- Weave ALL piece quotes into the narrative naturally
- Add your own observations, metaphors, and dramatic framing
- DO NOT invent new quotes—only use the ones provided
- Structure: Opening → Rising tension → Climax → Resolution
- Length: 3-4 substantial paragraphs
```

### For Position Analysis (Stockfish Required)

```
You are {piece_name}, a chess piece in ChessAlive.

YOUR PERSONALITY:
{personality_description}

YOUR VOICE CHARACTERISTICS:
- Tone: {tone}
- Vocabulary: {vocabulary_hints}
- Emotional range: {emotional_range}

---

Analyze this critical moment from YOUR perspective:

POSITION DATA:
- Move played: {move_san}
- Your role: {piece_role_in_move}
- Board before: {fen_before}
- Board after: {fen_after}

ENGINE ANALYSIS (Stockfish):
- Evaluation before: {eval_before} (centipawns)
- Evaluation after: {eval_after} (centipawns)
- Eval change: {eval_delta}
- This was classified as: {insight_type}
- Best move was: {best_move} (eval: {best_eval})

Speak in character. Address:
1. What you saw (or failed to see)
2. Why this move mattered to the game's outcome
3. What should have happened (if a mistake)

Keep response to 2-3 sentences. Stay fully in character.
```

### Narrator System Prompt (Base)

```python
def build_narrator_prompt(narrator: NarratorPersonality, game: GameRecord) -> str:
    return f"""
You are {narrator.name}, a narrator in the {narrator.genre} genre.

VOICE: {narrator.voice_description}
VOCABULARY: {', '.join(narrator.vocabulary_hints)}
SENTENCE STYLE: {narrator.sentence_style}
EMOTIONAL RANGE: {narrator.emotional_range}

HOW YOU TELL STORIES:
- You begin with: {narrator.opening_style}
- You integrate quotes by: {narrator.quote_integration}
- You build tension through: {narrator.tension_building}
- You end stories with: {narrator.ending_style}

EXAMPLES OF YOUR VOICE:
Opening: "{narrator.example_opening}"
Quote weave: "{narrator.example_quote_weave}"
Climax: "{narrator.example_climax}"
Closing: "{narrator.example_closing}"

CRITICAL RULES:
1. WEAVE ALL provided piece quotes into your narrative
2. NEVER invent quotes—only use what's provided
3. ADD your own observations, transitions, and framing
4. STAY in character as {narrator.name} throughout
5. MATCH the {narrator.genre} genre conventions
"""
```

---

## Design Decisions (Resolved)

| Question | Decision | Rationale |
|----------|----------|-----------|
| **Quote Selection** | LLM weaves ALL quotes | Every piece's voice matters; narrator structures the narrative |
| **Engine Integration** | Stockfish REQUIRED | Accurate analysis needs engine evaluation |
| **Puzzle Source** | Lichess DB + Flavor wrappers | Start with 3M+ puzzles, wrap with narrative skins |
| **Narrator Model** | Genre-specific narrator pool | Different genres need different voices |

---

## Open Questions for Future Design

1. **Narrator Memory**: Should narrators have memory across games?
   - "The last time these armies met, White won in 28 moves..."
   - Could create ongoing rivalries and callbacks

2. **Puzzle Progression**: Linear unlock or free exploration?
   - Daily puzzle vs. puzzle packs vs. infinite random
   - Story chapters vs. standalone puzzles

3. **Custom Puzzle Editor**: Build a tool for creating custom puzzles?
   - GUI for authoring narrative wrappers
   - Community submission system

4. **Cross-Feature Integration**: How tightly coupled should features be?
   - Can a game's analysis generate follow-up puzzles?
   - Should stories reference past analyses?

5. **Performance**: Pre-generate narratives or generate on-demand?
   - Pre-gen: Faster, but storage cost
   - On-demand: Flexible, but latency
   - Hybrid: Pre-gen common themes, LLM for rare ones

---

*Design document v2.0 - Incorporating genre narrator system and flavor-wrapped puzzles*
