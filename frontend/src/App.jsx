import { useEffect, useState } from "react";
import { clearToken, fetchMe, getToken } from "./api";
import DraftList from "./DraftList";
import LoginForm from "./LoginForm";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(() => Boolean(getToken()));

  // On page load: if a token is stored, confirm it is still valid.
  useEffect(() => {
    if (!getToken()) return undefined;
    let active = true;
    fetchMe()
      .then((u) => {
        if (active) setUser(u);
      })
      .catch(() => clearToken())
      .finally(() => {
        if (active) setChecking(false);
      });
    return () => {
      active = false;
    };
  }, []);

  // The API helper fires this event when the server says the token expired.
  useEffect(() => {
    const onLogout = () => setUser(null);
    window.addEventListener("leadflow:logout", onLogout);
    return () => window.removeEventListener("leadflow:logout", onLogout);
  }, []);

  function logout() {
    clearToken();
    setUser(null);
  }

  if (checking) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-500">
        Loading...
      </div>
    );
  }

  if (!user) {
    return <LoginForm onLoggedIn={setUser} />;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white shadow-sm">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <h1 className="text-xl font-semibold text-slate-800">LeadFlow</h1>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-slate-600">{user.full_name}</span>
            <button
              onClick={logout}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-slate-700 hover:bg-slate-100"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <h2 className="mb-4 text-lg font-medium text-slate-700">Email drafts</h2>
        <DraftList />
      </main>
    </div>
  );
}
