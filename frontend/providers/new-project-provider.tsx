"use client";

import React, { createContext, useCallback, useContext, useState } from "react";

interface NewProjectContextValue {
  isOpen: boolean;
  openNewProject: () => void;
  closeNewProject: () => void;
}

const NewProjectContext = createContext<NewProjectContextValue | null>(null);

export function NewProjectProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  const openNewProject = useCallback(() => setIsOpen(true), []);
  const closeNewProject = useCallback(() => setIsOpen(false), []);

  return (
    <NewProjectContext.Provider value={{ isOpen, openNewProject, closeNewProject }}>
      {children}
    </NewProjectContext.Provider>
  );
}

export function useNewProject(): NewProjectContextValue {
  const ctx = useContext(NewProjectContext);
  if (!ctx) {
    throw new Error("useNewProject must be used within a NewProjectProvider");
  }
  return ctx;
}
