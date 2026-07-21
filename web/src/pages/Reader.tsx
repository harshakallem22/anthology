import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ExternalLink,
  Highlighter,
  Star,
  Trash2,
} from "lucide-react";
import {
  useArticle,
  useCreateHighlight,
  useDeleteHighlight,
  useHighlights,
  useUpdateArticle,
} from "@/api/hooks";
import type { Highlight } from "@/lib/types";
import { Skeleton } from "@/components/Skeleton";
import { TagEditor } from "@/components/TagEditor";
import { cn, domainOf, formatDate, readingLabel } from "@/lib/utils";

/** Wrap the first exact occurrence of each quote in a <mark>. */
function applyHighlights(container: HTMLElement, quotes: string[]) {
  for (const quote of quotes) {
    const q = quote.trim();
    if (!q) continue;
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
    let node: Node | null;
    while ((node = walker.nextNode())) {
      const text = node.nodeValue ?? "";
      const idx = text.indexOf(q);
      if (idx >= 0) {
        const range = document.createRange();
        range.setStart(node, idx);
        range.setEnd(node, idx + q.length);
        const mark = document.createElement("mark");
        mark.className = "hl";
        try {
          range.surroundContents(mark);
        } catch {
          /* empty */
        }
        break;
      }
    }
  }
}

interface ToolbarState {
  x: number;
  y: number;
  quote: string;
}

export function Reader() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: article, isLoading } = useArticle(id);
  const { data: highlights } = useHighlights(id);
  const createHighlight = useCreateHighlight();
  const deleteHighlight = useDeleteHighlight();
  const update = useUpdateArticle();

  const contentRef = useRef<HTMLDivElement>(null);
  const [toolbar, setToolbar] = useState<ToolbarState | null>(null);

  useLayoutEffect(() => {
    const el = contentRef.current;
    if (!el || !article) return;
    el.innerHTML = article.content_html || "";
    if (highlights?.length) {
      applyHighlights(
        el,
        highlights.map((h) => h.quote),
      );
    }
  }, [article, highlights]);

  const onMouseUp = useCallback(() => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !contentRef.current) {
      setToolbar(null);
      return;
    }
    const text = sel.toString().trim();
    const range = sel.getRangeAt(0);
    if (!text || !contentRef.current.contains(range.commonAncestorContainer)) {
      setToolbar(null);
      return;
    }
    const rect = range.getBoundingClientRect();
    setToolbar({
      x: rect.left + rect.width / 2,
      y: rect.top - 8,
      quote: text,
    });
  }, []);

  useEffect(() => {
    const clear = () => setToolbar(null);
    window.addEventListener("scroll", clear, true);
    return () => window.removeEventListener("scroll", clear, true);
  }, []);

  function saveHighlight() {
    if (!toolbar || !id) return;
    createHighlight.mutate({ articleId: id, quote: toolbar.quote });
    setToolbar(null);
    window.getSelection()?.removeAllRanges();
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-reader">
        <Skeleton className="mb-4 h-10 w-3/4" />
        <Skeleton className="mb-8 h-5 w-1/3" />
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="mb-3 h-4 w-full" />
        ))}
      </div>
    );
  }

  if (!article) {
    return (
      <div className="py-24 text-center text-muted">
        Article not found.{" "}
        <Link to="/" className="text-accent underline">
          Back to library
        </Link>
      </div>
    );
  }

  const failed = article.extraction_status === "failed";

  return (
    <div className="animate-fade-in">
      <div className="mb-6 flex items-center justify-between">
        <button className="btn-ghost -ml-2" onClick={() => navigate(-1)}>
          <ArrowLeft size={18} /> Back
        </button>
        <div className="flex items-center gap-1">
          <button
            className="btn-ghost h-9 w-9 !px-0"
            aria-label="Favorite"
            onClick={() =>
              update.mutate({ id: article.id, is_favorite: !article.is_favorite })
            }
          >
            <Star
              size={18}
              className={cn(article.is_favorite && "fill-accent text-accent")}
            />
          </button>
          <a
            className="btn-ghost h-9 w-9 !px-0"
            href={article.url}
            target="_blank"
            rel="noreferrer"
            aria-label="Open original"
          >
            <ExternalLink size={18} />
          </a>
        </div>
      </div>

      <article className="mx-auto max-w-reader">
        <header className="mb-8">
          <div className="mb-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted">
            <span>{domainOf(article.url)}</span>
            {article.byline && (
              <>
                <span aria-hidden>·</span>
                <span>{article.byline}</span>
              </>
            )}
            {article.reading_minutes ? (
              <>
                <span aria-hidden>·</span>
                <span>{readingLabel(article.reading_minutes)}</span>
              </>
            ) : null}
            {article.saved_at && (
              <>
                <span aria-hidden>·</span>
                <span>Saved {formatDate(article.saved_at)}</span>
              </>
            )}
          </div>
          <h1 className="font-serif text-4xl font-semibold leading-tight tracking-tight">
            {article.title || domainOf(article.url)}
          </h1>
          <div className="mt-5">
            <TagEditor article={article} />
          </div>
        </header>

        {failed ? (
          <div className="card border-accent/30 p-6 text-muted">
            <p className="mb-2 font-medium text-ink">
              We couldn't extract this article's text.
            </p>
            <p className="text-sm">
              The link may be dead, paywalled, or timed out during import. You can
              still{" "}
              <a
                href={article.url}
                target="_blank"
                rel="noreferrer"
                className="text-accent underline"
              >
                open the original
              </a>
              .
            </p>
          </div>
        ) : (
          <div
            ref={contentRef}
            onMouseUp={onMouseUp}
            className="prose-reader"
          />
        )}
      </article>

      {highlights && highlights.length > 0 && (
        <HighlightList
          highlights={highlights}
          onDelete={(hid) =>
            id && deleteHighlight.mutate({ id: hid, articleId: id })
          }
        />
      )}

      {toolbar && (
        <div
          className="fixed z-50 -translate-x-1/2 -translate-y-full animate-fade-in"
          style={{ left: toolbar.x, top: toolbar.y }}
        >
          <button
            className="btn-primary shadow-card-hover"
            onMouseDown={(e) => e.preventDefault()}
            onClick={saveHighlight}
          >
            <Highlighter size={16} /> Highlight
          </button>
        </div>
      )}
    </div>
  );
}

function HighlightList({
  highlights,
  onDelete,
}: {
  highlights: Highlight[];
  onDelete: (id: string) => void;
}) {
  return (
    <section className="mx-auto mt-16 max-w-reader border-t border-border pt-8">
      <h2 className="mb-4 flex items-center gap-2 font-serif text-xl font-semibold">
        <Highlighter size={18} className="text-accent" /> Highlights
        <span className="text-sm font-normal text-muted">({highlights.length})</span>
      </h2>
      <ul className="space-y-3">
        {highlights.map((h) => (
          <li
            key={h.id}
            className="group flex items-start justify-between gap-3 rounded-lg border-l-2 border-accent/50 bg-surface px-4 py-3"
          >
            <div>
              <p className="font-serif italic text-ink">“{h.quote}”</p>
              {h.note && <p className="mt-1 text-sm text-muted">{h.note}</p>}
            </div>
            <button
              onClick={() => onDelete(h.id)}
              aria-label="Delete highlight"
              className="btn-ghost h-8 w-8 shrink-0 !px-0 opacity-0 transition group-hover:opacity-100"
            >
              <Trash2 size={15} />
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
