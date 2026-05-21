import { useEffect } from 'react';
import { Board3D } from './components/Board3D';
import { CommentaryPanel } from './components/CommentaryPanel';
import { GameInfo } from './components/GameInfo';
import { Controls } from './components/Controls';
import { useChess } from './hooks/useChess';
import './App.css';

function App() {
  const { newGame, isConnected } = useChess();

  // Auto-start a new game when connected
  useEffect(() => {
    if (isConnected) {
      console.log('Connected to backend, starting new game...');
      newGame({
        white_name: 'Player 1',
        black_name: 'Player 2',
        commentary_enabled: false, // Start disabled for faster gameplay
      });
    }
  }, [isConnected, newGame]);

  return (
    <div className="app">
      <div className="game-container">
        <Board3D />
        <GameInfo />
        <CommentaryPanel />
      </div>

      {/* Game controls */}
      <div className="controls-container">
        <Controls />
      </div>

      {/* ChessAlive branding */}
      <div className="branding">
        <h1>ChessAlive 3D</h1>
        <p>Where every piece has a voice</p>
      </div>
    </div>
  );
}

export default App;
