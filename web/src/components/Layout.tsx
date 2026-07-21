import { ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { BookMarked, Download, LogOut, Search, Upload } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { useLogout, useMe } from "@/api/hooks";
import { api } from "@/api/client";
import { cn } from "@/lib/utils";

function NavItem({ to, icon, label }: { to: string; icon: ReactNode; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          "btn-ghost gap-2 !px-3",
          isActive && "bg-surface-2 text-accent",
        )
      }
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </NavLink>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  const { data: me } = useMe();
  const logout = useLogout();
  const navigate = useNavigate();

  function exportLibrary() {
    window.location.href = `${api.defaults.baseURL}/export`;
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-30 border-b border-border bg-paper/85 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2">
            <BookMarked size={22} className="text-accent" />
            <span className="font-serif text-xl font-semibold tracking-tight">
              Anthology
            </span>
          </Link>

          <nav className="flex items-center gap-1">
            <NavItem to="/" icon={<BookMarked size={18} />} label="Library" />
            <NavItem to="/search" icon={<Search size={18} />} label="Search" />
            <NavItem to="/import" icon={<Upload size={18} />} label="Import" />
            <button className="btn-ghost gap-2 !px-3" onClick={exportLibrary}>
              <Download size={18} />
              <span className="hidden sm:inline">Export</span>
            </button>
            <div className="mx-1 h-6 w-px bg-border" />
            <ThemeToggle />
            {me && (
              <button
                className="btn-ghost h-9 w-9 !px-0"
                aria-label="Sign out"
                onClick={async () => {
                  await logout.mutateAsync();
                  navigate("/login");
                }}
              >
                <LogOut size={18} />
              </button>
            )}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">{children}</main>
    </div>
  );
}
