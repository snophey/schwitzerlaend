import { redirect } from "react-router";
import { getSession, commitSession } from "./sessions.server";

export async function sessionLoader({ request }: { request: Request }) {
  const cookieHeader = request.headers.get("Cookie");
  const session = await getSession(cookieHeader);

  if (!session.get("userId")) {
    // no user session yet --> create one
    const newUserId = crypto.randomUUID();

    console.log("Creating new session for userId:", newUserId);
    session.set("userId", newUserId);
    session.set("createdAt", new Date().toISOString());

    return redirect(request.url, {
      headers: {
        "Set-Cookie": await commitSession(session),
      },
    });
  }

  // session exists: optionally return session data to component
  return { userId: session.get("userId") };
}
