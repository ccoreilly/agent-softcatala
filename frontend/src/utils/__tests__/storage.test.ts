import { storage } from '../storage';
import { ChatSession } from '../../types';

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

describe('Storage Utility', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getSessions', () => {
    it('should return empty array when no sessions stored', () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      
      const sessions = storage.getSessions();
      
      expect(sessions).toEqual([]);
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('chat-sessions');
    });

    it('should return parsed sessions from localStorage', () => {
      const mockSessions: ChatSession[] = [
        {
          id: '1',
          name: 'Test Session',
          messages: [],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      ];
      
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockSessions));
      
      const sessions = storage.getSessions();
      
      expect(sessions).toEqual(mockSessions);
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('chat-sessions');
    });

    it('should return empty array when localStorage contains invalid JSON', () => {
      mockLocalStorage.getItem.mockReturnValue('invalid json');
      
      const sessions = storage.getSessions();
      
      expect(sessions).toEqual([]);
    });

    it('should handle localStorage access errors gracefully', () => {
      mockLocalStorage.getItem.mockImplementation(() => {
        throw new Error('localStorage access denied');
      });
      
      const sessions = storage.getSessions();
      
      expect(sessions).toEqual([]);
    });
  });

  describe('saveSessions', () => {
    it('should save sessions to localStorage', () => {
      const mockSessions: ChatSession[] = [
        {
          id: '1',
          name: 'Test Session',
          messages: [],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      ];
      
      storage.saveSessions(mockSessions);
      
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'chat-sessions',
        JSON.stringify(mockSessions)
      );
    });

    it('should handle localStorage save errors gracefully', () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('localStorage quota exceeded');
      });
      
      const mockSessions: ChatSession[] = [
        {
          id: '1',
          name: 'Test Session',
          messages: [],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      ];
      
      // Should not throw
      expect(() => storage.saveSessions(mockSessions)).not.toThrow();
    });

    it('should handle circular references in session data', () => {
      const circularSession = {
        id: '1',
        name: 'Test Session',
        messages: [],
        createdAt: '2023-01-01T00:00:00Z',
        updatedAt: '2023-01-01T00:00:00Z'
      } as any;
      
      // Create circular reference
      circularSession.self = circularSession;
      
      // Should handle gracefully
      expect(() => storage.saveSessions([circularSession])).not.toThrow();
    });
  });

  describe('Session persistence integration', () => {
    it('should maintain data integrity through save/load cycle', () => {
      const originalSessions: ChatSession[] = [
        {
          id: '1',
          name: 'Session 1',
          messages: [
            { id: '1', content: 'Hello', role: 'user', timestamp: '2023-01-01T00:00:00Z' },
            { id: '2', content: 'Hi there!', role: 'assistant', timestamp: '2023-01-01T00:01:00Z' }
          ],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:01:00Z'
        },
        {
          id: '2',
          name: 'Session 2',
          messages: [],
          createdAt: '2023-01-02T00:00:00Z',
          updatedAt: '2023-01-02T00:00:00Z'
        }
      ];
      
      // Save sessions
      storage.saveSessions(originalSessions);
      
      // Simulate what localStorage would do
      const savedData = mockLocalStorage.setItem.mock.calls[0][1];
      mockLocalStorage.getItem.mockReturnValue(savedData);
      
      // Load sessions
      const loadedSessions = storage.getSessions();
      
      expect(loadedSessions).toEqual(originalSessions);
    });

    it('should handle Unicode characters and special symbols', () => {
      const sessionsWithUnicode: ChatSession[] = [
        {
          id: '1',
          name: '🚀 Test Session with émojis and ñ characters',
          messages: [
            { id: '1', content: 'Hello 世界! 🌍', role: 'user', timestamp: '2023-01-01T00:00:00Z' }
          ],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      ];
      
      storage.saveSessions(sessionsWithUnicode);
      
      const savedData = mockLocalStorage.setItem.mock.calls[0][1];
      mockLocalStorage.getItem.mockReturnValue(savedData);
      
      const loadedSessions = storage.getSessions();
      
      expect(loadedSessions).toEqual(sessionsWithUnicode);
    });
  });

  describe('Edge cases', () => {
    it('should handle empty sessions array', () => {
      storage.saveSessions([]);
      
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('chat-sessions', '[]');
    });

    it('should handle very large session data', () => {
      const largeSessions: ChatSession[] = Array.from({ length: 1000 }, (_, i) => ({
        id: `${i}`,
        name: `Session ${i}`,
        messages: Array.from({ length: 100 }, (_, j) => ({
          id: `${i}-${j}`,
          content: `Message ${j} with lots of text content that could make the storage quite large`,
          role: j % 2 === 0 ? 'user' : 'assistant',
          timestamp: new Date(2023, 0, 1, 0, j).toISOString()
        })),
        createdAt: new Date(2023, 0, 1, i).toISOString(),
        updatedAt: new Date(2023, 0, 1, i, 30).toISOString()
      }));
      
      // Should handle large data without throwing
      expect(() => storage.saveSessions(largeSessions)).not.toThrow();
    });

    it('should handle null and undefined values gracefully', () => {
      expect(() => storage.saveSessions(null as any)).not.toThrow();
      expect(() => storage.saveSessions(undefined as any)).not.toThrow();
    });
  });
});