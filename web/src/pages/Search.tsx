import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Clock, Search as SearchIcon } from "lucide-react";
import { useSearch } from "@/api/hooks";
import { Skeleton } from "@/components/Skeleton";
import { domainOf, faviconOf, readingLabel } from "@/lib/utils";

export function Search() {
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setQuery(input), 220);
    return () => clearTimeout(t);
  }, [input]);

  const { data, isFetching } = useSearch(query);
  const hasQuery = query.trim().length > 0;

  return (
    <div className="mx-auto max-w-3xl animate-fade-in">
      <div className="mb-6">
        <div className="relative">
          <SearchIcon
            size={20}
            className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted"
          />
          <input
            autoFocus
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Search your library…"
            className="w-full rounded-xl border border-border bg-surface py-4 pl-12 pr-4 font-serif text-lg text-ink outline-none transition focus:border-accent/50 focus:ring-2 focus:ring-accent/30"
          />
        </div>
        {hasQuery && data && (
          <p className="mt-3 px-1 text-sm text-muted">
            {data.total} result{data.total === 1 ? "" : "s"} for “{data.query}”
          </p>
        )}
      </div>

      {!hasQuery ? (
        <div className="py-20 text-center text-muted">
          <p className="font-serif text-xl text-ink">Search everything you've saved.</p>
          <p className="mt-2">
            Full-text search ranks across titles and article text, with matching
            passages highlighted.
          </p>
        </div>
      ) : isFetching && !data ? (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-5">
              <Skeleton className="mb-2 h-5 w-2/3" />
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </div>
      ) : data && data.results.length > 0 ? (
        <ul className="space-y-3">
          {data.results.map((hit) => (
            <li key={hit.id}>
              <Link
                to={`/read/${hit.id}`}
                className="card block p-5 hover:-translate-y-0.5 hover:shadow-card-hover"
              >
                <div className="mb-1.5 flex items-center gap-2 text-xs text-muted">
                  <img src={faviconOf(hit.url)} alt="" className="h-3.5 w-3.5 rounded-sm" />
                  <span className="truncate">{domainOf(hit.url)}</span>
                  {hit.reading_minutes ? (
                    <>
                      <span aria-hidden>·</span>
                      <span className="inline-flex items-center gap-1">
                        <Clock size={12} /> {readingLabel(hit.reading_minutes)}
                      </span>
                    </>
                  ) : null}
                </div>
                <h3 className="mb-1.5 font-serif text-lg font-semibold text-ink">
                  {hit.title || domainOf(hit.url)}
                </h3>
                {hit.snippet && (
                  <p
                    className="snippet text-sm leading-relaxed text-muted"
                    dangerouslySetInnerHTML={{ __html: hit.snippet }}
                  />
                )}
                {hit.tags.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {hit.tags.map((t) => (
                      <span key={t} className="chip">
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <div className="py-20 text-center text-muted">
          No results for “{query}”. Try different words.
        </div>
      )}
    </div>
  );
}
