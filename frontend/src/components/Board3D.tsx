// 3D Chess Board component using React Three Fiber

import { useRef, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import type { ThreeEvent } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment, Text } from '@react-three/drei';
import * as THREE from 'three';
import { useGameStore } from '../store/gameStore';
import { useChess } from '../hooks/useChess';
import type { Color } from '../types/chess';

// Board dimensions
const BOARD_SIZE = 8;
const SQUARE_SIZE = 1;
const PIECE_HEIGHT = 0.5;

// Colors
const LIGHT_SQUARE = '#f0d9b5';
const DARK_SQUARE = '#b58863';
const SELECTED_COLOR = '#829769';
const LEGAL_MOVE_COLOR = '#646f40';

// Piece mappings
const PIECE_SYMBOLS: Record<string, string> = {
  WHITE_PAWN: '♙', WHITE_KNIGHT: '♘', WHITE_BISHOP: '♗',
  WHITE_ROOK: '♖', WHITE_QUEEN: '♕', WHITE_KING: '♔',
  BLACK_PAWN: '♟', BLACK_KNIGHT: '♞', BLACK_BISHOP: '♝',
  BLACK_ROOK: '♜', BLACK_QUEEN: '♛', BLACK_KING: '♚',
};

// Parse FEN to get board state
function parseFen(fen: string): (string | null)[][] {
  const board: (string | null)[][] = Array(8).fill(null).map(() => Array(8).fill(null));
  const rows = fen.split(' ')[0].split('/');

  for (let row = 0; row < 8; row++) {
    let col = 0;
    for (const char of rows[row]) {
      if (char >= '1' && char <= '8') {
        col += parseInt(char);
      } else {
        const isWhite = char === char.toUpperCase();
        const color = isWhite ? 'WHITE' : 'BLACK';
        const pieceMap: Record<string, string> = {
          p: 'PAWN', n: 'KNIGHT', b: 'BISHOP',
          r: 'ROOK', q: 'QUEEN', k: 'KING',
        };
        board[row][col] = `${color}_${pieceMap[char.toLowerCase()]}`;
        col++;
      }
    }
  }

  return board;
}

// Square component
function Square({
  position,
  isLight,
  isSelected,
  isLegalMove,
  onClick,
}: {
  position: [number, number, number];
  isLight: boolean;
  isSelected: boolean;
  isLegalMove: boolean;
  onClick: () => void;
}) {
  const meshRef = useRef<THREE.Mesh>(null);

  const color = useMemo(() => {
    if (isSelected) return SELECTED_COLOR;
    if (isLegalMove) return LEGAL_MOVE_COLOR;
    return isLight ? LIGHT_SQUARE : DARK_SQUARE;
  }, [isLight, isSelected, isLegalMove]);

  return (
    <mesh
      ref={meshRef}
      position={position}
      onClick={onClick}
      onPointerOver={(e: ThreeEvent<PointerEvent>) => {
        e.stopPropagation();
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        document.body.style.cursor = 'default';
      }}
    >
      <boxGeometry args={[SQUARE_SIZE, 0.1, SQUARE_SIZE]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}

// Piece component
function ChessPiece({
  position,
  pieceType,
  color,
  onClick,
}: {
  position: [number, number, number];
  pieceType: string;
  color: Color;
  onClick: () => void;
}) {
  const symbol = PIECE_SYMBOLS[pieceType];
  const isWhite = color === 'WHITE';

  return (
    <group position={position} onClick={onClick}>
      {/* Piece body - solid 3D piece */}
      <mesh position={[0, 0.3, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.35, 0.4, 0.6, 32]} />
        <meshStandardMaterial
          color={isWhite ? '#f0f0f0' : '#1a1a1a'}
          metalness={0.8}
          roughness={0.2}
        />
      </mesh>

      {/* Piece symbol on top */}
      <Text
        position={[0, 0.7, 0]}
        fontSize={0.4}
          color={isWhite ? '#000000' : '#ffffff'}
          anchorX="center"
          anchorY="middle"
      >
        {symbol}
      </Text>
    </group>
  );
}

// Board component
function ChessBoard() {
  const { gameState, selectedSquare, selectSquare, legalMovesFromSquare } = useGameStore();
  const { makeMove } = useChess();

  const board = useMemo(() => {
    return gameState ? parseFen(gameState.fen) : Array(8).fill(null).map(() => Array(8).fill(null));
  }, [gameState?.fen]);

  const handleSquareClick = (row: number, col: number) => {
    const square = String.fromCharCode(97 + col) + (8 - row);

    if (selectedSquare) {
      // Try to make a move
      const fromCol = selectedSquare.charCodeAt(0) - 97;
      const fromRow = 8 - parseInt(selectedSquare[1]);

      // Find the piece at the selected square
      const piece = board[fromRow][fromCol];
      if (piece) {
        // Construct the move (simplified - just try UCI format)
        const move = `${selectedSquare}${square}`;
        makeMove(move);
      }
      selectSquare(null);
    } else {
      // Select this square if there's a piece
      if (board[row][col]) {
        selectSquare(square);
      }
    }
  };

  // Generate squares
  const squares = [];
  for (let row = 0; row < BOARD_SIZE; row++) {
    for (let col = 0; col < BOARD_SIZE; col++) {
      const isLight = (row + col) % 2 === 0;
      const square = String.fromCharCode(97 + col) + (8 - row);
      const isSelected = selectedSquare === square;

      // Check if this square is a legal move destination
      const isLegalMove = selectedSquare ? legalMovesFromSquare.some(move => {
        // Simplified check - would need proper move parsing
        return move.includes(square);
      }) : false;

      squares.push(
        <Square
          key={`${row}-${col}`}
          position={[
            (col - BOARD_SIZE / 2 + 0.5) * SQUARE_SIZE,
            0,
            (row - BOARD_SIZE / 2 + 0.5) * SQUARE_SIZE,
          ]}
          isLight={isLight}
          isSelected={isSelected}
          isLegalMove={isLegalMove}
          onClick={() => handleSquareClick(row, col)}
        />
      );
    }
  }

  // Generate pieces
  const pieces = [];
  for (let row = 0; row < BOARD_SIZE; row++) {
    for (let col = 0; col < BOARD_SIZE; col++) {
      const piece = board[row][col];
      if (piece) {
        const [color] = piece.split('_') as [Color, string];
        pieces.push(
          <ChessPiece
            key={`piece-${row}-${col}`}
            position={[
              (col - BOARD_SIZE / 2 + 0.5) * SQUARE_SIZE,
              PIECE_HEIGHT / 2 + 0.05,
              (row - BOARD_SIZE / 2 + 0.5) * SQUARE_SIZE,
            ]}
            pieceType={piece}
            color={color}
            onClick={() => handleSquareClick(row, col)}
          />
        );
      }
    }
  }

  return (
    <group>
      {squares}
      {pieces}
    </group>
  );
}

// Scene component
function Scene() {
  return (
    <>
      <PerspectiveCamera makeDefault position={[0, 10, 10]} fov={50} />
      <OrbitControls
        enablePan={false}
        minPolarAngle={Math.PI / 8}
        maxPolarAngle={Math.PI / 2.2}
        minDistance={5}
        maxDistance={25}
        maxAzimuthAngle={Math.PI / 1.5}
        minAzimuthAngle={-Math.PI / 1.5}
      />

      {/* Lighting */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 15, 5]} intensity={1.0} castShadow />
      <directionalLight position={[-10, 15, -5]} intensity={0.5} />
      <pointLight position={[0, 10, 0]} intensity={0.3} />

      {/* Environment */}
      <Environment preset="city" />

      {/* Board */}
      <ChessBoard />
    </>
  );
}

// Main export
export function Board3D() {
  const { gameState } = useGameStore();

  if (!gameState) {
    return (
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '24px',
        color: '#666'
      }}>
        Loading ChessAlive 3D...
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Canvas shadows>
        <Scene />
      </Canvas>
    </div>
  );
}
