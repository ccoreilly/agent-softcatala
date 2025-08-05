// Setup file for Jest tests
import '@testing-library/jest-dom';

// Mock the crypto.randomUUID if it's not available in the test environment
if (!global.crypto) {
  global.crypto = {
    randomUUID: () => Math.random().toString(36).substr(2, 9)
  } as any;
}

// Mock the assistant-ui runtime for testing
jest.mock('@assistant-ui/react', () => ({
  AssistantRuntimeProvider: ({ children }: { children: any }) => children,
  useLocalRuntime: () => ({
    // Mock runtime methods
  }),
  Thread: () => {
    const React = require('react');
    return React.createElement('div', { 'data-testid': 'thread' }, 'Thread Component');
  },
  Composer: () => {
    const React = require('react');
    return React.createElement('div', { 'data-testid': 'composer' }, 'Composer Component');
  },
}));