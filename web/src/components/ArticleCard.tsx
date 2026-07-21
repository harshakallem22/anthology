import { Link } from "react-router-dom";
import { Archive, ArchiveRestore, Clock, Star } from "lucide-react";
import type { Article } from "@/lib/types";
import { useUpdateArticle } from "@/api/hooks";
import { cn, domainOf, faviconOf, readingLabel } from "@/lib/utils";

export function ArticleCard({ article }: { article: Article }) {
  const update = useUpdateArticle();

  const toggleFavorite = (e: React.MouseEvent) => {
    e.preventDefault();
    update.mutate({ id: article.id, is_favorite: !article.is_favorite });
  };
  const toggleArchive = (e: React.MouseEvent) => {
    e.preventDefault();
    update.mutate({ id: article.id, is_archived: !article.is_archived });
  };

  return (
    <Link
      to={`/read/${article.id}`}
      className="card group flex flex-col overflow-hidden hover:-translate-y-0.5 hover:shadow-card-hover"
    >
      {article.lead_image_url ? (
        <div className="aspect-[16/9] overflow-hidden bg-surface-2">
          <img
            src={article.lead_image_url}
            alt=""
            loading="lazy"
            className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]"
            onError={(e) => (e.currentTarget.style.display = "none")}
          />
        </div>
      ) : (
        <div className="flex aspect-[16/9] items-center justify-center bg-gradient-to-br from-surface-2 to-surface">
          <span className="font-serif text-4xl text-border">A</span>
        </div>
      )}

      <div className="flex flex-1 flex-col p-5">
        <div className="mb-2 flex items-center gap-2 text-xs text-muted">
          <img src={faviconOf(article.url)} alt="" className="h-3.5 w-3.5 rounded-sm" />
          <span className="truncate">{domainOf(article.url)}</span>
          {article.reading_minutes ? (
            <>
              <span aria-hidden>·</span>
              <span className="inline-flex items-center gap-1 whitespace-nowrap">
                <Clock size={12} /> {readingLabel(article.reading_minutes)}
              </span>
            </>
          ) : null}
        </div>

        <h3 className="mb-2 font-serif text-lg font-semibold leading-snug text-ink line-clamp-2">
          {article.title || domainOf(article.url)}
        </h3>

        {article.excerpt && (
          <p className="mb-4 text-sm leading-relaxed text-muted line-clamp-3">
            {article.excerpt}
          </p>
        )}

        <div className="mt-auto flex items-center justify-between gap-2 pt-2">
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {article.tags.slice(0, 3).map((t) => (
              <span key={t.id} className="chip">
                {t.name}
              </span>
            ))}
            {article.extraction_status === "failed" && (
              <span className="chip border-accent/30 text-accent">extraction failed</span>
            )}
            {article.extraction_status === "pending" && (
              <span className="chip">extracting…</span>
            )}
          </div>

          <div className="flex shrink-0 items-center gap-1">
            <button
              onClick={toggleFavorite}
              aria-label={article.is_favorite ? "Unfavorite" : "Favorite"}
              className="btn-ghost h-8 w-8 !px-0"
            >
              <Star
                size={16}
                className={cn(article.is_favorite && "fill-accent text-accent")}
              />
            </button>
            <button
              onClick={toggleArchive}
              aria-label={article.is_archived ? "Unarchive" : "Archive"}
              className="btn-ghost h-8 w-8 !px-0"
            >
              {article.is_archived ? (
                <ArchiveRestore size={16} />
              ) : (
                <Archive size={16} />
              )}
            </button>
          </div>
        </div>
      </div>
    </Link>
  );
}
