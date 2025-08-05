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

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockStorage.getSessions.mockReturnValue([]);
    mockStorage.saveSessions.mockImplementation(() => {});
  });

  describe('Initial Rendering', () => {
    it('renders the main application components', () => {
      render(<App />);
      
      expect(screen.getByText('Agent de Softcatalà')).toBeInTheDocument();
      expect(screen.getByText('Benvingut a l\'Agent de Softcatalà')).toBeInTheDocument();
      expect(screen.getByText('Iniciar Nova Conversa')).toBeInTheDocument();
    });

    it('starts with sidebar collapsed by default', () => {
      render(<App />);
      
      // The sidebar should be collapsed initially
      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      expect(sidebarContainer).toHaveClass('w-0');
    });

    it('loads sessions from storage on mount', () => {
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
      
      expect(mockStorage.getSessions).toHaveBeenCalled();
      expect(screen.getByText('Test Session')).toBeInTheDocument();
    });
  });

  describe('Sidebar Toggle Functionality', () => {
    it('toggles sidebar when hamburger button is clicked', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      const toggleButton = screen.getByRole('button', { name: /menu/i });
      
      // Initially collapsed (w-0)
      const sidebarContainer = document.querySelector('.sidebar')?.parentElement;
      expect(sidebarContainer).toHaveClass('w-0');
      
      // Click to expand
      await user.click(toggleButton);
      
      // Should now be expanded (w-80)
      expect(sidebarContainer).toHaveClass('w-80');
    });

    it('shows correct title in header when no session is selected', () => {
      render(<App />);
      
      expect(screen.getByText('Agent de Softcatalà')).toBeInTheDocument();
    });

    it('shows session name in header when session is selected', () => {
      const mockSessions = [
        {
          id: '1',
          name: 'My Test Session',
          messages: [],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      ];
      mockStorage.getSessions.mockReturnValue(mockSessions);
      
      render(<App />);
      
      expect(screen.getByText('My Test Session')).toBeInTheDocument();
    });
  });

  describe('Session Management', () => {
    it('creates new session when "Iniciar Nova Conversa" button is clicked', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      const newConversationButton = screen.getByText('Iniciar Nova Conversa');
      await user.click(newConversationButton);
      
      // Should save the new session to storage
      expect(mockStorage.saveSessions).toHaveBeenCalled();
      
      // Should have a new session with name "Nova Conversa"
      const savedSessions = mockStorage.saveSessions.mock.calls[0][0];
      expect(savedSessions).toHaveLength(1);
      expect(savedSessions[0].name).toBe('Nova Conversa');
    });

    it('creates new session from sidebar new conversation button', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      // First expand the sidebar
      const toggleButton = screen.getByRole('button', { name: /menu/i });
      await user.click(toggleButton);
      
      // Then click the new conversation button in sidebar
      const newConversationButton = screen.getByText('+ Nova Conversa');
      await user.click(newConversationButton);
      
      expect(mockStorage.saveSessions).toHaveBeenCalled();
    });

    it('selects first session automatically when sessions are loaded', () => {
      const mockSessions = [
        {
          id: '1',
          name: 'First Session',
          messages: [{ id: '1', content: 'Hello', role: 'user', timestamp: '2023-01-01T00:00:00Z' }],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        },
        {
          id: '2',
          name: 'Second Session',
          messages: [],
          createdAt: '2023-01-02T00:00:00Z',
          updatedAt: '2023-01-02T00:00:00Z'
        }
      ];
      mockStorage.getSessions.mockReturnValue(mockSessions);
      
      render(<App />);
      
      // Should show the first session's name in header
      expect(screen.getByText('First Session')).toBeInTheDocument();
      // Should show message count
      expect(screen.getByText('1 missatges')).toBeInTheDocument();
    });

    it('handles session deletion correctly', async () => {
      const user = userEvent.setup();
      const mockSessions = [
        {
          id: '1',
          name: 'Session 1',
          messages: [],
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
      
      // Expand sidebar
      const toggleButton = screen.getByRole('button', { name: /menu/i });
      await user.click(toggleButton);
      
      // Mock window.confirm for deletion
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
      
      // Hover over first session and click delete
      const sessionItem = screen.getByText('Session 1').closest('.session-item')!;
      await user.hover(sessionItem);
      
      const deleteButton = screen.getByTitle('Eliminar sessió');
      await user.click(deleteButton);
      
      // Should save updated sessions
      expect(mockStorage.saveSessions).toHaveBeenCalled();
      
      confirmSpy.mockRestore();
    });

    it('handles session renaming correctly', async () => {
      const user = userEvent.setup();
      const mockSessions = [
        {
          id: '1',
          name: 'Original Name',
          messages: [],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      ];
      mockStorage.getSessions.mockReturnValue(mockSessions);
      
      render(<App />);
      
      // Expand sidebar
      const toggleButton = screen.getByRole('button', { name: /menu/i });
      await user.click(toggleButton);
      
      // Hover over session and click edit
      const sessionItem = screen.getByText('Original Name').closest('.session-item')!;
      await user.hover(sessionItem);
      
      const editButton = screen.getByTitle('Canviar nom de la sessió');
      await user.click(editButton);
      
      // Change the name
      const input = screen.getByDisplayValue('Original Name');
      await user.clear(input);
      await user.type(input, 'New Name');
      await user.keyboard('{Enter}');
      
      // Should save the session with updated name
      expect(mockStorage.saveSessions).toHaveBeenCalled();
      const savedSessions = mockStorage.saveSessions.mock.calls[0][0];
      expect(savedSessions[0].name).toBe('New Name');
    });
  });

  describe('Empty State', () => {
    it('shows welcome screen when no sessions exist', () => {
      render(<App />);
      
      expect(screen.getByText('Benvingut a l\'Agent de Softcatalà')).toBeInTheDocument();
      expect(screen.getByText('Inicia una nova conversa per començar a parlar amb l\'Agent de Softcatalà.')).toBeInTheDocument();
    });

    it('shows chat interface when session is selected', () => {
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
      
      // Should show the Thread and Composer components (mocked)
      expect(screen.getByTestId('thread')).toBeInTheDocument();
      expect(screen.getByTestId('composer')).toBeInTheDocument();
    });
  });

  describe('Session Storage', () => {
    it('saves sessions whenever they change', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      // Create a new session
      const newConversationButton = screen.getByText('Iniciar Nova Conversa');
      await user.click(newConversationButton);
      
      // Should call saveSessions
      expect(mockStorage.saveSessions).toHaveBeenCalled();
    });

    it('loads sessions from storage on component mount', () => {
      const mockSessions = [
        {
          id: '1',
          name: 'Stored Session',
          messages: [],
          createdAt: '2023-01-01T00:00:00Z',
          updatedAt: '2023-01-01T00:00:00Z'
        }
      ];
      mockStorage.getSessions.mockReturnValue(mockSessions);
      
      render(<App />);
      
      expect(mockStorage.getSessions).toHaveBeenCalled();
      expect(screen.getByText('Stored Session')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('maintains proper layout structure', () => {
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
  });

  describe('Integration with Assistant-UI', () => {
    it('renders AssistantRuntimeProvider with runtime', () => {
      render(<App />);
      
      // The app should render without errors, indicating proper provider setup
      expect(screen.getByText('Agent de Softcatalà')).toBeInTheDocument();
    });

    it('renders Thread and Composer components when session is selected', () => {
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