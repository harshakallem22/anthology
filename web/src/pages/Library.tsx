import { useState } from "react";
import { Link } from "react-router-dom";
import { BookMarked, Upload } from "lucide-react";
import { useArticles, useTags, type ArticleFilters } from "@/api/hooks";
import { ArticleCard } from "@/components/ArticleCard";
import { CardSkeleton } from "@/components/Skeleton";
import { EmptyState } from "@/components/EmptyState";
import { cn } from "@/lib/utils";

type View = "all" | "favorites" | "archived";

export function Library() {
  const [view, setView] = useState<View>("all");
  const [activeTag, setActiveTag] = useState<string | null>(null);

  const filters: ArticleFilters = {
    archived: view === "archived",
    favorite: view === "favorites" || undefined,
    tag: activeTag ?? undefined,
  };
  const { data: articles, isLoading } = useArticles(filters);
  const { data: tags } = useTags();

  const views: { key: View; label: string }[] = [
    { key: "all", label: "Library" },
    { key: "favorites", label: "Favorites" },
    { key: "archived", label: "Archived" },
  ];

  return (
    <div>
      <div className="mb-8 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="font-serif text-3xl font-semibold tracking-tight">
            {view === "archived"
              ? "Archived"
              : view === "favorites"
                ? "Favorites"
                : "Your library"}
          </h1>
          <p className="mt-1 text-muted">
            {articles ? `${articles.length} article${articles.length === 1 ? "" : "s"}` : " "}
            {activeTag ? ` tagged “${activeTag}”` : ""}
          </p>
        </div>

        <div className="inline-flex rounded-lg border border-border bg-surface p-1">
          {views.map((v) => (
            <button
              key={v.key}
              onClick={() => setView(v.key)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                view === v.key
                  ? "bg-accent text-accent-ink"
                  : "text-muted hover:text-ink",
              )}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>

      {tags && tags.length > 0 && (
        <div className="mb-8 flex flex-wrap gap-2">
          <button
            onClick={() => setActiveTag(null)}
            className={cn("chip", !activeTag && "chip-active")}
          >
            All tags
          </button>
          {tags.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTag(activeTag === t.name ? null : t.name)}
              className={cn("chip", activeTag === t.name && "chip-active")}
            >
              {t.name}
            </button>
          ))}
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : articles && articles.length > 0 ? (
        <div className="grid animate-fade-in grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((a) => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<BookMarked size={28} />}
          title={
            view === "all" && !activeTag ? "Your library is empty" : "Nothing here yet"
          }
          description={
            view === "all" && !activeTag
              ? "Import your Pocket or Instapaper export to bring years of saved reading into a home you own."
              : "Try a different filter, or import more of your archive."
          }
          action={
            <Link to="/import" className="btn-primary">
              <Upload size={18} /> Import your archive
            </Link>
          }
        />
      )}
    </div>
  );
}
