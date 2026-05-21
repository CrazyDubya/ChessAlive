// Commentary Panel component for displaying piece dialogue

import { useGameStore } from '../store/gameStore';
import type { CommentaryMessage } from '../types/chess';
import './CommentaryPanel.css';

function CommentaryBubble({ message }: { message: CommentaryMessage }) {
  const isWhite = message.piece.color === 'WHITE';

  return (
    <div className={`commentary-bubble ${isWhite ? 'white' : 'black'}`}>
      <div className="commentary-header">
        <span className="piece-icon">
          {getPieceIcon(message.piece.type, message.piece.color)}
        </span>
        <span className="piece-name">{message.piece.name}</span>
        <span className="piece-type">{message.piece.type.toLowerCase()}</span>
      </div>
      <div className="commentary-text">
        "{message.text}"
      </div>
    </div>
  );
}

function getPieceIcon(type: string, color: string): string {
  const icons: Record<string, Record<string, string>> = {
    WHITE: {
      PAWN: '♙', KNIGHT: '♘', BISHOP: '♗',
      ROOK: '♖', QUEEN: '♕', KING: '♔',
    },
    BLACK: {
      PAWN: '♟', KNIGHT: '♞', BISHOP: '♝',
      ROOK: '♜', QUEEN: '♛', KING: '♚',
    },
  };
  return icons[color]?.[type] || '?';
}

export function CommentaryPanel() {
  const { commentary, showCommentary, toggleCommentary } = useGameStore();

  return (
    <div className={`commentary-panel ${showCommentary ? '' : 'collapsed'}`}>
      <div className="panel-header">
        <h3>💬 Piece Commentary</h3>
        <button onClick={toggleCommentary} className="toggle-btn">
          {showCommentary ? '▼' : '▲'}
        </button>
      </div>

      {showCommentary && (
        <div className="commentary-list">
          {commentary.length === 0 ? (
            <div className="no-commentary">
              Piece commentary will appear here...
            </div>
          ) : (
            commentary.map((msg, idx) => (
              <CommentaryBubble
                key={`${idx}-${msg.piece.square}`}
                message={msg}
              />
            )
          ))}
        </div>
      )}
    </div>
  );
}
