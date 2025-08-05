import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Sidebar } from '../Sidebar';
import { ChatSession } from '../../types';

// Mock date-fns to have consistent test results
jest.mock('date-fns', () => ({
  formatDistanceToNow: () => '2 hours ago'
}));

const mockSessions: ChatSession[] = [
  {
    id: '1',
    name: 'Session 1',
    messages: [{ id: '1', content: 'Hello', role: 'user', timestamp: '2023-01-01T00:00:00Z' }],
    createdAt: '2023-01-01T00:00:00Z',
    updatedAt: '2023-01-01T02:00:00Z'
  },
  {
    id: '2',
    name: 'Session 2',
    messages: [],
    createdAt: '2023-01-02T00:00:00Z',
    updatedAt: '2023-01-02T00:00:00Z'
  }
];

const defaultProps = {
  sessions: mockSessions,
  currentSessionId: '1',
  onSelectSession: jest.fn(),
  onNewSession: jest.fn(),
  onDeleteSession: jest.fn(),
  onRenameSession: jest.fn(),
  isCollapsed: false,
  onToggleCollapse: jest.fn()
};

describe('Sidebar Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders sidebar with sessions when not collapsed', () => {
      render(<Sidebar {...defaultProps} />);
      
      expect(screen.getByText('Session 1')).toBeInTheDocument();
      expect(screen.getByText('Session 2')).toBeInTheDocument();
      expect(screen.getByText('+ Nova Conversa')).toBeInTheDocument();
    });

    it('shows toggle button when collapsed', () => {
      render(<Sidebar {...defaultProps} isCollapsed={true} />);
      
      expect(screen.getByTitle('Expandir barra lateral')).toBeInTheDocument();
      expect(screen.queryByText('+ Nova Conversa')).not.toBeInTheDocument();
    });

    it('shows empty state when no sessions exist', () => {
      render(<Sidebar {...defaultProps} sessions={[]} />);
      
      expect(screen.getByText('No hi ha sessions de conversa encara')).toBeInTheDocument();
      expect(screen.getByText('Inicia una nova conversa!')).toBeInTheDocument();
    });
  });

  describe('Session Selection', () => {
    it('highlights the current session', () => {
      render(<Sidebar {...defaultProps} />);
      
      const activeSession = screen.getByText('Session 1').closest('.session-item');
      expect(activeSession).toHaveClass('active');
    });

    it('calls onSelectSession when a session is clicked', async () => {
      const user = userEvent.setup();
      render(<Sidebar {...defaultProps} />);
      
      await user.click(screen.getByText('Session 2'));
      
      expect(defaultProps.onSelectSession).toHaveBeenCalledWith('2');
    });
  });

  describe('New Session Creation', () => {
    it('calls onNewSession when new conversation button is clicked', async () => {
      const user = userEvent.setup();
      render(<Sidebar {...defaultProps} />);
      
      await user.click(screen.getByText('+ Nova Conversa'));
      
      expect(defaultProps.onNewSession).toHaveBeenCalled();
    });

    it('does not show new conversation button when collapsed', () => {
      render(<Sidebar {...defaultProps} isCollapsed={true} />);
      
      expect(screen.queryByText('+ Nova Conversa')).not.toBeInTheDocument();
    });
  });

  describe('Session Management', () => {
    it('shows session metadata including message count and last updated', () => {
      render(<Sidebar {...defaultProps} />);
      
      expect(screen.getByText('1 missatges')).toBeInTheDocument();
      expect(screen.getByText('0 missatges')).toBeInTheDocument();
      expect(screen.getAllByText('2 hours ago')).toHaveLength(2);
    });
  });

  describe('Session Renaming', () => {
    it('enters rename mode when edit button is clicked', async () => {
      const user = userEvent.setup();
      render(<Sidebar {...defaultProps} />);
      
      const sessionItem = screen.getByText('Session 1').closest('.session-item')!;
      await user.hover(sessionItem);
      
      const editButton = within(sessionItem).getByTitle('Canviar nom de la sessió');
      await user.click(editButton);
      
      expect(screen.getByDisplayValue('Session 1')).toBeInTheDocument();
    });

    it('saves new name when Enter is pressed', async () => {
      const user = userEvent.setup();
      render(<Sidebar {...defaultProps} />);
      
      const sessionItem = screen.getByText('Session 1').closest('.session-item')!;
      await user.hover(sessionItem);
      
      const editButton = within(sessionItem).getByTitle('Canviar nom de la sessió');
      await user.click(editButton);
      
      const input = screen.getByDisplayValue('Session 1');
      await user.clear(input);
      await user.type(input, 'New Session Name');
      await user.keyboard('{Enter}');
      
      expect(defaultProps.onRenameSession).toHaveBeenCalledWith('1', 'New Session Name');
    });

    it('cancels rename when Escape is pressed', async () => {
      const user = userEvent.setup();
      render(<Sidebar {...defaultProps} />);
      
      const sessionItem = screen.getByText('Session 1').closest('.session-item')!;
      await user.hover(sessionItem);
      
      const editButton = within(sessionItem).getByTitle('Canviar nom de la sessió');
      await user.click(editButton);
      
      const input = screen.getByDisplayValue('Session 1');
      await user.clear(input);
      await user.type(input, 'New Name');
      await user.keyboard('{Escape}');
      
      expect(defaultProps.onRenameSession).not.toHaveBeenCalled();
      expect(screen.getByText('Session 1')).toBeInTheDocument();
    });

    it('saves name when input loses focus', async () => {
      const user = userEvent.setup();
      render(<Sidebar {...defaultProps} />);
      
      const sessionItem = screen.getByText('Session 1').closest('.session-item')!;
      await user.hover(sessionItem);
      
      const editButton = within(sessionItem).getByTitle('Canviar nom de la sessió');
      await user.click(editButton);
      
      const input = screen.getByDisplayValue('Session 1');
      await user.clear(input);
      await user.type(input, 'Renamed Session');
      
      // Click outside to blur
      await user.click(document.body);
      
      expect(defaultProps.onRenameSession).toHaveBeenCalledWith('1', 'Renamed Session');
    });
  });

  describe('Session Deletion', () => {
    it('shows confirmation dialog when delete button is clicked', async () => {
      const user = userEvent.setup();
      // Mock window.confirm
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
      
      render(<Sidebar {...defaultProps} />);
      
      const sessionItem = screen.getByText('Session 1').closest('.session-item')!;
      await user.hover(sessionItem);
      
      const deleteButton = within(sessionItem).getByTitle('Eliminar sessió');
      await user.click(deleteButton);
      
      expect(confirmSpy).toHaveBeenCalledWith('Estàs segur que vols eliminar "Session 1"?');
      expect(defaultProps.onDeleteSession).toHaveBeenCalledWith('1');
      
      confirmSpy.mockRestore();
    });

    it('does not delete session when confirmation is cancelled', async () => {
      const user = userEvent.setup();
      // Mock window.confirm to return false
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);
      
      render(<Sidebar {...defaultProps} />);
      
      const sessionItem = screen.getByText('Session 1').closest('.session-item')!;
      await user.hover(sessionItem);
      
      const deleteButton = within(sessionItem).getByTitle('Eliminar sessió');
      await user.click(deleteButton);
      
      expect(confirmSpy).toHaveBeenCalled();
      expect(defaultProps.onDeleteSession).not.toHaveBeenCalled();
      
      confirmSpy.mockRestore();
    });
  });

  describe('Collapse/Expand Functionality', () => {
    it('calls onToggleCollapse when toggle button is clicked', async () => {
      const user = userEvent.setup();
      render(<Sidebar {...defaultProps} />);
      
      const toggleButton = screen.getByTitle('Contraure barra lateral');
      await user.click(toggleButton);
      
      expect(defaultProps.onToggleCollapse).toHaveBeenCalled();
    });

    it('shows correct toggle button text based on collapsed state', () => {
      const { rerender } = render(<Sidebar {...defaultProps} isCollapsed={false} />);
      
      expect(screen.getByText('←')).toBeInTheDocument();
      
      rerender(<Sidebar {...defaultProps} isCollapsed={true} />);
      
      expect(screen.getByText('→')).toBeInTheDocument();
    });
  });

  describe('Event Propagation', () => {
    it('prevents session selection when clicking on action buttons', async () => {
      const user = userEvent.setup();
      
      render(<Sidebar {...defaultProps} />);
      
      const sessionItem = screen.getByText('Session 1').closest('.session-item')!;
      await user.hover(sessionItem);
      
      const editButton = within(sessionItem).getByTitle('Canviar nom de la sessió');
      await user.click(editButton);
      
      // Session should not be selected when clicking action buttons
      expect(defaultProps.onSelectSession).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and titles', () => {
      render(<Sidebar {...defaultProps} />);
      
      expect(screen.getByTitle('Contraure barra lateral')).toBeInTheDocument();
      
      // Check that action buttons exist (even if multiple)
      const editButtons = screen.getAllByTitle('Canviar nom de la sessió');
      const deleteButtons = screen.getAllByTitle('Eliminar sessió');
      
      expect(editButtons.length).toBeGreaterThan(0);
      expect(deleteButtons.length).toBeGreaterThan(0);
    });

    it('handles keyboard navigation properly', async () => {
      const user = userEvent.setup();
      render(<Sidebar {...defaultProps} />);
      
      const sessionItem = screen.getByText('Session 1').closest('.session-item')!;
      await user.hover(sessionItem);
      
      const editButton = within(sessionItem).getByTitle('Canviar nom de la sessió');
      await user.click(editButton);
      
      const input = screen.getByDisplayValue('Session 1');
      expect(input).toHaveFocus();
    });
  });
});