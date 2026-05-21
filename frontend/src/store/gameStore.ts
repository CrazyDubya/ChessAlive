// Zustand store for chess game state

import { create } from 'zustand';
import type { GameState, CommentaryMessage, Piece } from '../types/chess';

interface GameStore {
  // Game state
  gameState: GameState | null;
  selectedSquare: string | null;
  legalMovesFromSquare: string[];

  // Commentary
  commentary: CommentaryMessage[];
  showCommentary: boolean;

  // Connection
  isConnected: boolean;
  error: string | null;

  // Actions
  setGameState: (state: GameState) => void;
  selectSquare: (square: string | null) => void;
  setLegalMovesFromSquare: (moves: string[]) => void;
  addCommentary: (messages: CommentaryMessage[]) => void;
  clearCommentary: () => void;
  toggleCommentary: () => void;
  setConnected: (connected: boolean) => void;
  setError: (error: string | null) => void;

  // Helpers
  getPieceAtSquare: (square: string) => Piece | null;
}

export const useGameStore = create<GameStore>((set, get) => ({
  // Initial state
  gameState: null,
  selectedSquare: null,
  legalMovesFromSquare: [],
  commentary: [],
  showCommentary: true,
  isConnected: false,
  error: null,

  // Actions
  setGameState: (state) => set({ gameState: state }),

  selectSquare: (square) => set({ selectedSquare: square }),

  setLegalMovesFromSquare: (moves) => set({ legalMovesFromSquare: moves }),

  addCommentary: (messages) =>
    set((state) => ({
      commentary: [...state.commentary, ...messages].slice(-50), // Keep last 50
    })),

  clearCommentary: () => set({ commentary: [] }),

  toggleCommentary: () =>
    set((state) => ({ showCommentary: !state.showCommentary })),

  setConnected: (connected) => set({ isConnected: connected }),

  setError: (error) => set({ error }),

  // Helpers
  getPieceAtSquare: (square: string) => {
    const state = get();
    if (!state.gameState) return null;

    // Parse FEN to get piece at square
    const fen = state.gameState.fen;
    const parts = fen.split(' ');
    const board = parts[0];
    const rows = board.split('/');

    const col = square.charCodeAt(0) - 'a'.charCodeAt(0);
    const row = 8 - parseInt(square[1]);

    if (row < 0 || row > 7 || col < 0 || col > 7) return null;

    let currentCol = 0;
    for (const char of rows[row]) {
      if (currentCol === col) {
        const isWhite = char === char.toUpperCase();
        const typeMap: Record<string, string> = {
          p: 'PAWN', n: 'KNIGHT', b: 'BISHOP',
          r: 'ROOK', q: 'QUEEN', k: 'KING',
        };
        return {
          type: typeMap[char.toLowerCase()] as any,
          color: isWhite ? 'WHITE' : 'BLACK',
          name: `${isWhite ? 'White' : 'Black'} ${typeMap[char.toLowerCase()]}`,
          square,
          is_captured: false,
        };
      }
      if (char >= '1' && char <= '8') {
        currentCol += parseInt(char);
      } else {
        currentCol++;
      }
    }
    return null;
  },
}));

// Helper to get legal moves for a specific piece
export function getLegalMovesForSquare(fen: string, square: string, allLegalMoves: string[]): string[] {
  // Filter legal moves that start from this square
  return allLegalMoves.filter(move => {
    // Handle different move formats
    if (move.length >= 2) {
      // For moves like "e4" (pawn push) or "Nf3" (knight)
      const piece = getPieceAtSquareFromFen(fen, square);
      if (!piece) return false;

      if (piece.type === 'PAWN') {
        // Pawn moves - check if this pawn can make the move
        const file = square[0];
        if (move[0] === file) return true;
        // Capture moves like "exd5"
        if (move.length >= 4 && move[0] === file && move[1] === 'x') return true;
        return false;
      } else {
        // Piece moves start with the piece letter
        const pieceLetter = piece.type[0] === 'KNIGHT' ? 'N' : piece.type[0];
        if (move[0] === pieceLetter) return true;
        return false;
      }
    }
    return false;
  });
}

function getPieceAtSquareFromFen(fen: string, square: string) {
  const parts = fen.split(' ');
  const board = parts[0];
  const rows = board.split('/');

  const col = square.charCodeAt(0) - 'a'.charCodeAt(0);
  const row = 8 - parseInt(square[1]);

  if (row < 0 || row > 7 || col < 0 || col > 7) return null;

  let currentCol = 0;
  for (const char of rows[row]) {
    if (currentCol === col) {
      const isWhite = char === char.toUpperCase();
      const typeMap: Record<string, string> = {
        p: 'PAWN', n: 'KNIGHT', b: 'BISHOP',
        r: 'ROOK', q: 'QUEEN', k: 'KING',
      };
      return {
        type: typeMap[char.toLowerCase()],
        color: isWhite ? 'WHITE' : 'BLACK',
      };
    }
    if (char >= '1' && char <= '8') {
      currentCol += parseInt(char);
    } else {
      currentCol++;
    }
  }
  return null;
}
