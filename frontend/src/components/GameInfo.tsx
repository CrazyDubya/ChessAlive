// Game Info panel showing turn, controls, and game state

import { useGameStore } from '../store/gameStore';
import { useChess } from '../hooks/useChess';
import './GameInfo.css';

export function GameInfo() {
  const { gameState, isConnected } = useGameStore();
  const { newGame, isDesktopMode } = useChess();

  const turnColor = gameState?.turn === 'WHITE' ? 'White' : 'Black';

  return (
    <div className="game-info">
      <div className="connection-status">
        <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
        {isConnected ? 'Connected' : 'Connecting...'}
        {isDesktopMode && <span className="desktop-badge">Desktop App</span>}
      </div>

      {gameState && (
        <>
          <div className="turn-indicator">
            <span className="turn-label">Turn:</span>
            <span className={`turn-color ${gameState.turn.toLowerCase()}`}>
              {turnColor}
            </span>
            {gameState.is_check && (
              <span className="check-badge">CHECK!</span>
            )}
          </div>

          {gameState.is_checkmate && (
            <div className="game-status checkmate">
              Checkmate! {gameState.turn === 'WHITE' ? 'Black' : 'White'} wins!
            </div>
          )}

          {gameState.is_stalemate && (
            <div className="game-status stalemate">
              Stalemate - Draw
            </div>
          )}

          {gameState.is_game_over && !gameState.is_checkmate && !gameState.is_stalemate && (
            <div className="game-status">
              Game Over: {gameState.result}
            </div>
          )}

          <div className="move-count">
            Move {gameState.fullmove_number}
          </div>
        </>
      )}

      <div className="controls">
        <button onClick={() => newGame()} className="new-game-btn">
          New Game
        </button>
      </div>

      <div className="instructions">
        <p>Click a piece to select it, then click a destination square to move.</p>
        <p>Drag to rotate the board. Scroll to zoom.</p>
      </div>
    </div>
  );
}
