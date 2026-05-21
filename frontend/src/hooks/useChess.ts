// WebSocket hook for ChessAlive backend connection

import { useEffect, useRef, useCallback, useState } from 'react';
import { useGameStore } from '../store/gameStore';
import type { WSMessage, GameState, MoveResult } from '../types/chess';
import { invoke } from '@tauri-apps/api/core';
import { isTauri } from '@tauri-apps/api/core';

// WebSocket URL - same for both web and Tauri (backend runs locally)
const WS_URL = 'ws://127.0.0.1:8001/ws';

// Detect if running in Tauri desktop context
const isDesktop = async (): Promise<boolean> => {
  try {
    return await isTauri();
  } catch {
    return false;
  }
};

// Backend status type
interface BackendStatus {
  running: boolean;
  port: number;
}

export function useChess() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const [isDesktopMode, setIsDesktopMode] = useState(false);

  const {
    setGameState,
    addCommentary,
    setConnected,
    setError,
  } = useGameStore();

  // Check backend status (desktop mode)
  const checkBackendStatus = useCallback(async () => {
    try {
      const inTauri = await isDesktop();
      if (inTauri) {
        // Try to call Tauri command, but gracefully handle if it doesn't exist
        try {
          const status = await invoke<BackendStatus>('get_backend_status');
          return status.running;
        } catch (tauriError) {
          // Command doesn't exist or backend isn't running
          // Assume backend is running on port 8001
          console.log('Tauri backend check not available, assuming backend is running');
          return true;
        }
      }
      return true; // Assume backend is running in web mode
    } catch (error) {
      console.error('Error checking backend status:', error);
      return true; // Assume backend is running rather than blocking connection
    }
  }, []);

  // Handle incoming messages
  const handleMessage = useCallback((message: WSMessage) => {
    console.log('Handling message type:', message.type);
    switch (message.type) {
      case 'state_update':
        console.log('State update received:', message.data);
        setGameState(message.data as GameState);
        break;

      case 'move_result':
        const result = message.data as MoveResult;
        if (result.success) {
          setGameState({
            fen: result.fen,
            turn: result.is_game_over ? 'WHITE' : (result.legal_moves.length > 0 ? 'WHITE' : 'BLACK'), // Simplified
            legal_moves: result.legal_moves,
            is_check: result.is_check,
            is_checkmate: result.is_checkmate,
            is_stalemate: false,
            is_game_over: result.is_game_over,
            result: result.result,
            fullmove_number: 1,
            halfmove_clock: 0,
            white_name: 'White',
            black_name: 'Black',
          });
          if (result.commentary.length > 0) {
            addCommentary(result.commentary);
          }
        }
        break;

      case 'commentary':
        if (message.data) {
          addCommentary([message.data]);
        }
        break;

      case 'error':
        setError(message.error || 'Unknown error');
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [setGameState, addCommentary, setError]);

  // Send message
  const send = useCallback((type: string, data?: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data }));
    }
  }, []);

  // Make a move
  const makeMove = useCallback((move: string) => {
    send('move', { move });
  }, [send]);

  // Start new game
  const newGame = useCallback((options?: {
    white_name?: string;
    black_name?: string;
    commentary_enabled?: boolean;
  }) => {
    send('new_game', {
      white_name: options?.white_name || 'Player 1',
      black_name: options?.black_name || 'Player 2',
      commentary_enabled: options?.commentary_enabled ?? true,
    });
  }, [send]);

  // Request game state
  const getState = useCallback(() => {
    send('get_state');
  }, [send]);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    // Detect if running in desktop mode
    isDesktop().then(setIsDesktopMode);

    const connectInternal = async () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      // Check if backend is running (especially in desktop mode)
      const backendRunning = await checkBackendStatus();
      if (!backendRunning) {
        setError('Backend not running. Please start the server.');
        return;
      }

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Connected to ChessAlive server');
        setConnected(true);
        setError(null);
      };

      ws.onclose = () => {
        console.log('Disconnected from ChessAlive server');
        setConnected(false);

        // Reconnect after 2 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connectInternal();
        }, 2000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error');
      };

      ws.onmessage = (event) => {
        console.log('WebSocket received message:', event.data);
        try {
          const message: WSMessage = JSON.parse(event.data);
          console.log('Parsed message:', message);
          handleMessage(message);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };
    };

    connectInternal();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, []);

  return {
    makeMove,
    newGame,
    getState,
    isConnected: useGameStore((s) => s.isConnected),
    isDesktopMode,
    checkBackendStatus,
  };
}
