import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';

// Mock the storage utility
jest.mock('../utils/storage', () => ({
  storage: {
    getSessions: jest.fn(),
    saveSessions: jest.fn(),
  }
}));

// Mock the transport adapter
jest.mock('../lib/transport', () => ({
  chatAgentAdapter: {}
}));

// Mock the lib/utils
jest.mock('../lib/utils', () => ({
  cn: (...classes: string[]) => classes.filter(Boolean).join(' ')
}));

// Get the mocked storage functions
const { storage: mockStorage } = require('../utils/storage');

describe('Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockStorage.getSessions.mockReturnValue([]);
    mockStorage.saveSessions.mockImplementation(() => {});
  });

  describe('New Conversation Flow', () => {
    it('should complete full new conversation workflow from empty state', async () => {
      const user = userEvent.setup();
      render(<App />);

      // 1. Verify app starts with sidebar collapsed and empty state
      expect(screen.getByText('Benvingut a l\'Agent de Softcatalà')).toBeInTheDocument();
      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      expect(sidebarContainer).toHaveClass('w-0');

      // 2. Click "Iniciar Nova Conversa" button from empty state
      const newConversationButton = screen.getByText('Iniciar Nova Conversa');
      await user.click(newConversationButton);

      // 3. Verify new session is created and saved
      expect(mockStorage.saveSessions).toHaveBeenCalled();
      const savedSessions = mockStorage.saveSessions.mock.calls[0][0];
      expect(savedSessions).toHaveLength(1);
      expect(savedSessions[0].name).toBe('Nova Conversa');

      // 4. Verify UI switches to chat interface
      expect(screen.getByTestId('thread')).toBeInTheDocument();
      expect(screen.getByTestId('composer')).toBeInTheDocument();
      expect(screen.getByText('Nova Conversa')).toBeInTheDocument();
    });

    it('should complete new conversation workflow from sidebar', async () => {
      const user = userEvent.setup();
      render(<App />);

      // 1. Expand sidebar
      const toggleButton = screen.getByRole('button', { name: /menu/i });
      await user.click(toggleButton);

      // 2. Verify sidebar is expanded
      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      expect(sidebarContainer).toHaveClass('w-80');

      // 3. Click new conversation button in sidebar
      const newConversationButton = screen.getByText('+ Nova Conversa');
      await user.click(newConversationButton);

      // 4. Verify session creation
      expect(mockStorage.saveSessions).toHaveBeenCalled();

      // 5. Verify UI updates properly
      expect(screen.getByText('Nova Conversa')).toBeInTheDocument();
      expect(screen.getByTestId('thread')).toBeInTheDocument();
    });
  });

  describe('Sidebar Behavior Integration', () => {
    it('should maintain sidebar state during session operations', async () => {
      const user = userEvent.setup();
      const mockSessions = [
        {
          id: '1',
          name: 'Test Session',
          messages: [],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      ];
      mockStorage.getSessions.mockReturnValue(mockSessions);

      render(<App />);

      // 1. Start with collapsed sidebar
      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      expect(sidebarContainer).toHaveClass('w-0');

      // 2. Expand sidebar
      const toggleButton = screen.getByRole('button', { name: /menu/i });
      await user.click(toggleButton);
      expect(sidebarContainer).toHaveClass('w-80');

      // 3. Create new session
      const newConversationButton = screen.getByText('+ Nova Conversa');
      await user.click(newConversationButton);

      // 4. Verify sidebar remains expanded
      expect(sidebarContainer).toHaveClass('w-80');

      // 5. Collapse sidebar
      await user.click(toggleButton);
      expect(sidebarContainer).toHaveClass('w-0');

      // 6. Verify session is still active in header
      expect(screen.getByText('Nova Conversa')).toBeInTheDocument();
    });

    it('should handle overlapping elements correctly when toggling sidebar', async () => {
      const user = userEvent.setup();
      render(<App />);

      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      const mainContent = document.querySelector('.flex-1.flex.flex-col');
      const toggleButton = screen.getByRole('button', { name: /menu/i });

      // 1. Initially collapsed - check no overlap
      expect(sidebarContainer).toHaveClass('w-0');
      expect(sidebarContainer).toHaveClass('overflow-hidden');

      // 2. Expand sidebar
      await user.click(toggleButton);
      expect(sidebarContainer).toHaveClass('w-80');

      // 3. Verify main content is still accessible
      expect(mainContent).toBeInTheDocument();
      expect(screen.getByText('Agent de Softcatalà')).toBeInTheDocument();

      // 4. Collapse again
      await user.click(toggleButton);
      expect(sidebarContainer).toHaveClass('w-0');

      // 5. Verify content is still properly rendered
      expect(screen.getByText('Agent de Softcatalà')).toBeInTheDocument();
    });
  });

  describe('Session Management Integration', () => {
    it('should handle complete session lifecycle', async () => {
      const user = userEvent.setup();
      render(<App />);

      // 1. Create first session
      const newConversationButton = screen.getByText('Iniciar Nova Conversa');
      await user.click(newConversationButton);

      // Mock the storage to return the session we just created
      const firstSession = {
        id: '1',
        name: 'Nova Conversa',
        messages: [],
        createdAt: '2023-01-01T00:00:00Z',
        updatedAt: '2023-01-01T00:00:00Z'
      };
      mockStorage.getSessions.mockReturnValue([firstSession]);

      // 2. Expand sidebar to see sessions
      const toggleButton = screen.getByRole('button', { name: /menu/i });
      await user.click(toggleButton);

      // 3. Create second session
      const sidebarNewButton = screen.getByText('+ Nova Conversa');
      await user.click(sidebarNewButton);

      // 4. Mock storage with both sessions
      const secondSession = {
        id: '2',
        name: 'Nova Conversa',
        messages: [],
        createdAt: '2023-01-01T01:00:00Z',
        updatedAt: '2023-01-01T01:00:00Z'
      };
      mockStorage.getSessions.mockReturnValue([secondSession, firstSession]);

      // 5. Rename the current session
      const sessionItem = screen.getAllByText('Nova Conversa')[1].closest('.session-item')!;
      await user.hover(sessionItem);

      const editButton = screen.getByTitle('Canviar nom de la sessió');
      await user.click(editButton);

      const input = screen.getByDisplayValue('Nova Conversa');
      await user.clear(input);
      await user.type(input, 'My Renamed Session');
      await user.keyboard('{Enter}');

      // 6. Verify renaming worked
      expect(mockStorage.saveSessions).toHaveBeenCalled();
    });

    it('should handle session switching correctly', async () => {
      const user = userEvent.setup();
      const mockSessions = [
        {
          id: '1',
          name: 'Session 1',
          messages: [{ id: '1', content: 'Hello', role: 'user', timestamp: '2023-01-01T00:00:00Z' }],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        },
        {
          id: '2',
          name: 'Session 2',
          messages: [],
          createdAt: '2023-01-02T00:00:00Z',
          updatedAt: '2023-01-02T00:00:00Z'
        }
      ];
      mockStorage.getSessions.mockReturnValue(mockSessions);

      render(<App />);

      // 1. Verify first session is selected by default
      expect(screen.getByText('Session 1')).toBeInTheDocument();
      expect(screen.getByText('1 missatges')).toBeInTheDocument();

      // 2. Expand sidebar
      const toggleButton = screen.getByRole('button', { name: /menu/i });
      await user.click(toggleButton);

      // 3. Click on second session
      await user.click(screen.getByText('Session 2'));

      // 4. Verify session switch occurred
      expect(screen.getByText('Session 2')).toBeInTheDocument();
      expect(screen.getByText('0 missatges')).toBeInTheDocument();
    });

    it('should handle session deletion workflow', async () => {
      const user = userEvent.setup();
      const mockSessions = [
        {
          id: '1',
          name: 'Session to Delete',
          messages: [],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        },
        {
          id: '2',
          name: 'Remaining Session',
          messages: [],
          createdAt: '2023-01-02T00:00:00Z',
          updatedAt: '2023-01-02T00:00:00Z'
        }
      ];
      mockStorage.getSessions.mockReturnValue(mockSessions);

      render(<App />);

      // 1. Expand sidebar
      const toggleButton = screen.getByRole('button', { name: /menu/i });
      await user.click(toggleButton);

      // 2. Mock window.confirm
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

      // 3. Delete first session
      const sessionItem = screen.getByText('Session to Delete').closest('.session-item')!;
      await user.hover(sessionItem);

      const deleteButton = screen.getByTitle('Eliminar sessió');
      await user.click(deleteButton);

      // 4. Verify deletion workflow
      expect(confirmSpy).toHaveBeenCalledWith('Estàs segur que vols eliminar "Session to Delete"?');
      expect(mockStorage.saveSessions).toHaveBeenCalled();

      confirmSpy.mockRestore();
    });
  });

  describe('Responsive Behavior Integration', () => {
    it('should maintain functionality across different viewport sizes', async () => {
      const user = userEvent.setup();
      render(<App />);

      // 1. Test mobile-like behavior (sidebar collapsed by default)
      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      expect(sidebarContainer).toHaveClass('w-0');

      // 2. Verify hamburger menu works
      const toggleButton = screen.getByRole('button', { name: /menu/i });
      await user.click(toggleButton);
      expect(sidebarContainer).toHaveClass('w-80');

      // 3. Verify new conversation still works
      const newConversationButton = screen.getByText('+ Nova Conversa');
      await user.click(newConversationButton);
      expect(mockStorage.saveSessions).toHaveBeenCalled();

      // 4. Verify layout remains intact
      expect(screen.getByText('Nova Conversa')).toBeInTheDocument();
      expect(screen.getByTestId('thread')).toBeInTheDocument();
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle storage errors gracefully', () => {
      mockStorage.getSessions.mockImplementation(() => {
        throw new Error('Storage error');
      });

      // Should not crash the app
      expect(() => render(<App />)).not.toThrow();
    });

    it('should handle malformed session data', () => {
      mockStorage.getSessions.mockReturnValue([
        {
          id: '1',
          // Missing required fields
          createdAt: '2023-01-01T00:00:00Z',
        }
      ]);

      // Should not crash the app
      expect(() => render(<App />)).not.toThrow();
    });
  });

  describe('Performance Integration', () => {
    it('should handle multiple rapid session operations', async () => {
      const user = userEvent.setup();
      render(<App />);

      const toggleButton = screen.getByRole('button', { name: /menu/i });
      
      // 1. Rapidly toggle sidebar multiple times
      for (let i = 0; i < 5; i++) {
        await user.click(toggleButton);
      }

      // 2. Create multiple sessions quickly
      await user.click(screen.getByText('+ Nova Conversa'));
      await user.click(screen.getByText('+ Nova Conversa'));

      // Should handle this without issues
      expect(mockStorage.saveSessions).toHaveBeenCalled();
    });
  });
});