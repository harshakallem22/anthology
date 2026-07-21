import { useState } from "react";
import { Plus, X } from "lucide-react";
import type { Article } from "@/lib/types";
import { useAddTag, useRemoveTag } from "@/api/hooks";

export function TagEditor({ article }: { article: Article }) {
  const [adding, setAdding] = useState(false);
  const [value, setValue] = useState("");
  const addTag = useAddTag();
  const removeTag = useRemoveTag();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const name = value.trim();
    if (name) {
      addTag.mutate({ articleId: article.id, name });
    }
    setValue("");
    setAdding(false);
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {article.tags.map((t) => (
        <span key={t.id} className="chip chip-active gap-1 pr-1">
          {t.name}
          <button
            aria-label={`Remove tag ${t.name}`}
            onClick={() => removeTag.mutate({ articleId: article.id, name: t.name })}
            className="rounded-full p-0.5 hover:bg-accent/20"
          >
            <X size={12} />
          </button>
        </span>
      ))}

      {adding ? (
        <form onSubmit={submit}>
          <input
            autoFocus
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onBlur={() => setAdding(false)}
            placeholder="tag name"
            className="w-28 rounded-full border border-accent/40 bg-surface px-3 py-0.5 text-xs text-ink outline-none focus:ring-2 focus:ring-accent/40"
          />
        </form>
      ) : (
        <button
          onClick={() => setAdding(true)}
          className="chip gap-1 hover:border-accent/40 hover:text-accent"
        >
          <Plus size={12} /> Tag
        </button>
      )}
    </div>
  );
}
