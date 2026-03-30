import React from 'react';
import { RouterProvider } from 'react-router';
import { router } from './routes';
import { AuthProvider } from './context/AuthContext';
import { appLogger } from './utils/logger';

appLogger.info('NEXORA Frontend starting...');

export default function App() {
  appLogger.info('Rendering App component');
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}