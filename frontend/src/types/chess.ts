// Chess types for the frontend

export type PieceType = 'PAWN' | 'KNIGHT' | 'BISHOP' | 'ROOK' | 'QUEEN' | 'KING';
export type Color = 'WHITE' | 'BLACK';

export interface PiecePersonality {
  name: string;
  archetype: string;
  speaking_style: string;
  backstory?: string;
  aggression: number;
  caution: number;
  humor: number;
  eloquence: number;
}

export interface Piece {
  type: PieceType;
  color: Color;
  name: string;
  square: string;
  is_captured: boolean;
  personality?: PiecePersonality;
}

export interface CommentaryMessage {
  piece: Piece;
  text: string;
  commentary_type: string;
}

export interface GameState {
  fen: string;
  turn: Color;
  legal_moves: string[];
  is_check: boolean;
  is_checkmate: boolean;
  is_stalemate: boolean;
  is_game_over: boolean;
  result: string | null;
  fullmove_number: number;
  halfmove_clock: number;
  white_name: string;
  black_name: string;
}

export interface MoveResult {
  success: boolean;
  fen: string;
  san: string;
  captured_piece?: {
    type: PieceType;
    color: Color;
    name: string;
  };
  is_check: boolean;
  is_checkmate: boolean;
  is_game_over: boolean;
  result: string | null;
  commentary: CommentaryMessage[];
  legal_moves: string[];
}

// WebSocket message types
export type WSMessageType =
  | 'move'
  | 'get_state'
  | 'new_game'
  | 'get_piece'
  | 'state_update'
  | 'move_result'
  | 'commentary'
  | 'error'
  | 'game_over';

export interface WSMessage {
  type: WSMessageType;
  data?: any;
  error?: string;
}
