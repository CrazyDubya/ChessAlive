import { useState } from 'react';
import { useChess } from '../hooks/useChess';
import './Controls.css';

export function Controls() {
  const { newGame, isConnected } = useChess();
  const [selectedMode, setSelectedMode] = useState<string>('PLAYER_VS_PLAYER');
  const [commentaryEnabled, setCommentaryEnabled] = useState(true);

  const modes = [
    { value: 'PLAYER_VS_PLAYER', label: '👥 Player vs Player' },
    { value: 'PLAYER_VS_COMPUTER', label: '🤖 Player vs Computer' },
    { value: 'COMPUTER_VS_COMPUTER', label: '💻 Computer vs Computer' },
  ];

  const handleNewGame = () => {
    newGame({
      white_name: 'Player 1',
      black_name: 'Player 2',
      commentary_enabled: commentaryEnabled,
    });
  };

  return (
    <div className="controls">
      <div className="controls-header">
        <h3>Game Controls</h3>
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </div>
      </div>

      <div className="controls-section">
        <label>Game Mode:</label>
        <select
          value={selectedMode}
          onChange={(e) => setSelectedMode(e.target.value)}
          disabled={!isConnected}
        >
          {modes.map((mode) => (
            <option key={mode.value} value={mode.value}>
              {mode.label}
            </option>
          ))}
        </select>
      </div>

      <div className="controls-section">
        <label>
          <input
            type="checkbox"
            checked={commentaryEnabled}
            onChange={(e) => setCommentaryEnabled(e.target.checked)}
            disabled={!isConnected}
          />
          Enable Commentary
        </label>
      </div>

      <button
        className="new-game-btn"
        onClick={handleNewGame}
        disabled={!isConnected}
      >
        🎮 New Game
      </button>

      <div className="controls-info">
        <p>💡 <strong>Tip:</strong> Click pieces to select, then click destination to move</p>
      </div>
    </div>
  );
}
