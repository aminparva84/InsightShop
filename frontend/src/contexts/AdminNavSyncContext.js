import React, { createContext, useContext, useState, useCallback } from 'react';

const AdminNavSyncContext = createContext(null);

/**
 * Keeps navbar menu and admin sidebar mutually exclusive:
 * - When navbar menu opens, admin sidebar closes.
 * - When admin sidebar opens, navbar menu closes.
 */
export function AdminNavSyncProvider({ children }) {
  const [navbarMenuOpen, setNavbarMenuOpenState] = useState(false);
  const [adminSidebarOpen, setAdminSidebarOpenState] = useState(false);

  const setNavbarMenuOpen = useCallback((open) => {
    setNavbarMenuOpenState(open);
    if (open) setAdminSidebarOpenState(false);
  }, []);

  const setAdminSidebarOpen = useCallback((open) => {
    setAdminSidebarOpenState(open);
    if (open) setNavbarMenuOpenState(false);
  }, []);

  const value = {
    navbarMenuOpen,
    setNavbarMenuOpen,
    adminSidebarOpen,
    setAdminSidebarOpen,
  };

  return (
    <AdminNavSyncContext.Provider value={value}>
      {children}
    </AdminNavSyncContext.Provider>
  );
}

export function useAdminNavSync() {
  const ctx = useContext(AdminNavSyncContext);
  if (!ctx) {
    throw new Error('useAdminNavSync must be used within AdminNavSyncProvider');
  }
  return ctx;
}
