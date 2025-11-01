import { createCookieSessionStorage } from "react-router";

type SessionData = {
  userId: string;
  createdAt: string;
};

type SessionFlashData = {
  error: string;
};

const { getSession, commitSession, destroySession } =
  createCookieSessionStorage<SessionData, SessionFlashData>({
    // a Cookie from `createCookie` or the CookieOptions to create one
    cookie: {
      name: "sweatzerlaend_session",

      // all of these are optional
      httpOnly: true,
      maxAge: 60,
      path: "/",
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      secrets: [process.env.SESSION_SECRET || "1n53cur3!"], // tamper protection
    },
  });

export { getSession, commitSession, destroySession };
