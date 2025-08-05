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
    it('should render welcome screen and allow new conversation creation', async () => {
      const user = userEvent.setup();
      render(<App />);

      // 1. Verify app starts with sidebar collapsed and empty state
      expect(screen.getByText('Benvingut a l\'Agent de Softcatalà')).toBeInTheDocument();
      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      expect(sidebarContainer).toHaveClass('w-0');

      // 2. Click "Iniciar Nova Conversa" button from empty state
      const newConversationButton = screen.getByText('Iniciar Nova Conversa');
      await user.click(newConversationButton);

      // 3. Verify storage save was called (indicates session creation attempt)
      expect(mockStorage.saveSessions).toHaveBeenCalled();
    });

    it('should allow expanding sidebar and creating conversation from sidebar', async () => {
      const user = userEvent.setup();
      render(<App />);

      // 1. Expand sidebar
      const toggleButton = screen.getByRole('button', { name: /toggle menu/i });
      await user.click(toggleButton);

      // 2. Verify sidebar is expanded
      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      expect(sidebarContainer).toHaveClass('w-80');

      // 3. Click new conversation button in sidebar
      const newConversationButton = screen.getByText('+ Nova Conversa');
      await user.click(newConversationButton);

      // 4. Verify session creation attempt
      expect(mockStorage.saveSessions).toHaveBeenCalled();
    });
  });

  describe('Sidebar Behavior Integration', () => {
    it('should handle overlapping elements correctly when toggling sidebar', async () => {
      const user = userEvent.setup();
      render(<App />);

      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      const mainContent = document.querySelector('.flex-1.flex.flex-col');
      const toggleButton = screen.getByRole('button', { name: /toggle menu/i });

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
    it('should handle session selection correctly', () => {
      const mockSessions = [
        {
          id: '1',
          name: 'First Session',
          messages: [{ id: '1', content: 'Hello', role: 'user', timestamp: '2023-01-01T00:00:00Z' }],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      ];
      mockStorage.getSessions.mockReturnValue(mockSessions);

      render(<App />);

      // Should show the first session's name in header
      expect(screen.getByText('First Session')).toBeInTheDocument();
      // Should show message count
      expect(screen.getByText('1 missatges')).toBeInTheDocument();
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle storage errors gracefully', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      mockStorage.getSessions.mockImplementation(() => {
        throw new Error('Storage error');
      });

      // Should not crash the app
      expect(() => render(<App />)).not.toThrow();
      
      // Should show empty state when storage fails
      expect(screen.getByText('Benvingut a l\'Agent de Softcatalà')).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });

    it('should handle malformed session data', () => {
      mockStorage.getSessions.mockReturnValue([
        {
          id: '1',
          name: 'Malformed Session',
          // Missing messages field
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      ]);

      // Should not crash the app
      expect(() => render(<App />)).not.toThrow();
      
      // Should show session with 0 messages when messages field is missing
      expect(screen.getByText('Malformed Session')).toBeInTheDocument();
      expect(screen.getByText('0 missatges')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('should maintain proper layout structure', () => {
      render(<App />);
      
      // Check main container structure
      const mainContainer = document.querySelector('.h-screen.flex');
      expect(mainContainer).toBeInTheDocument();
      
      // Check sidebar container
      const sidebarContainer = document.querySelector('.transition-all.duration-300');
      expect(sidebarContainer).toBeInTheDocument();
      
      // Check main content area
      const mainContent = document.querySelector('.flex-1.flex.flex-col');
      expect(mainContent).toBeInTheDocument();
    });

    it('should handle sidebar toggle functionality', async () => {
      const user = userEvent.setup();
      render(<App />);

      // Test mobile-like behavior (sidebar collapsed by default)
      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      expect(sidebarContainer).toHaveClass('w-0');

      // Verify hamburger menu works
      const toggleButton = screen.getByRole('button', { name: /toggle menu/i });
      await user.click(toggleButton);
      expect(sidebarContainer).toHaveClass('w-80');
    });
  });

  describe('Integration with Assistant-UI', () => {
    it('should render AssistantRuntimeProvider with runtime', () => {
      render(<App />);
      
      // The app should render without errors, indicating proper provider setup
      expect(screen.getByText('Agent de Softcatalà')).toBeInTheDocument();
    });

    it('should render Thread and Composer components when session is selected', () => {
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
      
      // Should render the mocked Thread and Composer components
      expect(screen.getByTestId('thread')).toBeInTheDocument();
      expect(screen.getByTestId('composer')).toBeInTheDocument();
    });
  });
});