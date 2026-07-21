import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { BookMarked } from "lucide-react";
import { useDevLogin, useMe } from "@/api/hooks";
import { api } from "@/api/client";
import { ThemeToggle } from "@/components/ThemeToggle";

export function Login() {
  const { data: me } = useMe();
  const devLogin = useDevLogin();
  const navigate = useNavigate();

  useEffect(() => {
    if (me) navigate("/", { replace: true });
  }, [me, navigate]);

  return (
    <div className="relative flex min-h-screen items-center justify-center px-4">
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md animate-fade-in text-center">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent text-accent-ink">
          <BookMarked size={26} />
        </div>
        <h1 className="mb-3 font-serif text-4xl font-semibold tracking-tight">
          Anthology
        </h1>
        <p className="mx-auto mb-10 max-w-sm text-lg leading-relaxed text-muted">
          Your reading, owned. Bring your Pocket or Instapaper archive home -
          clean text, tags, highlights, and full-text search, forever yours.
        </p>

        <div className="card space-y-3 p-6 text-left">
          <button
            className="btn-primary w-full justify-center"
            onClick={() => {
              window.location.href = `${api.defaults.baseURL}/auth/google/login`;
            }}
          >
            Continue with Google
          </button>

          <div className="flex items-center gap-3 py-1 text-xs text-muted">
            <span className="h-px flex-1 bg-border" />
            or
            <span className="h-px flex-1 bg-border" />
          </div>

          <button
            className="btn-outline w-full justify-center"
            disabled={devLogin.isPending}
            onClick={() => devLogin.mutate()}
          >
            {devLogin.isPending ? "Signing in…" : "Try the demo (dev login)"}
          </button>
          <p className="pt-1 text-center text-xs text-muted">
            The demo login is available in development so you can explore without
            Google credentials.
          </p>
        </div>
      </div>
    </div>
  );
}
