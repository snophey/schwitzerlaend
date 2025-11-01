import { createContext, useContext } from "react";

type SessionContextType = {
  userId: string;
  createdAt?: string;
};

export const SessionContext = createContext<SessionContextType | null>(null);

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useSession must be used inside <SessionProvider>");
  }
  return ctx;
}
