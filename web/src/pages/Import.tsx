import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, FileText, UploadCloud } from "lucide-react";
import { useCreateImport, useImportStatus } from "@/api/hooks";
import { cn } from "@/lib/utils";

export function Import() {
  const [dragging, setDragging] = useState(false);
  const [importId, setImportId] = useState<string | undefined>();
  const inputRef = useRef<HTMLInputElement>(null);
  const createImport = useCreateImport();

  const { data: job } = useImportStatus(importId, true);
  const done = job?.status === "complete";
  const isPolling = !!importId && !done && job?.status !== "failed";

  async function handleFile(file: File) {
    const res = await createImport.mutateAsync({ file });
    setImportId(res.id);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  const pct =
    job && job.total_count > 0
      ? Math.round((job.processed_count / job.total_count) * 100)
      : job?.status === "processing"
        ? 5
        : 0;

  return (
    <div className="mx-auto max-w-2xl animate-fade-in">
      <div className="mb-8 text-center">
        <h1 className="font-serif text-3xl font-semibold tracking-tight">
          Import your archive
        </h1>
        <p className="mt-2 text-muted">
          Bring your Pocket or Instapaper export home. We'll parse every link,
          extract clean readable text, and add it to your library.
        </p>
      </div>

      {!importId ? (
        <>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            className={cn(
              "flex cursor-pointer flex-col items-center rounded-2xl border-2 border-dashed p-14 text-center transition",
              dragging
                ? "border-accent bg-accent/5"
                : "border-border bg-surface hover:border-accent/50",
            )}
          >
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-accent/10 text-accent">
              <UploadCloud size={26} />
            </div>
            <p className="mb-1 font-medium text-ink">
              {createImport.isPending
                ? "Uploading…"
                : "Drop your export file here, or click to browse"}
            </p>
            <p className="text-sm text-muted">
              Pocket (.html) or Instapaper (.csv) - up to thousands of links
            </p>
            <input
              ref={inputRef}
              type="file"
              accept=".html,.htm,.csv"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFile(file);
              }}
            />
          </div>

          {createImport.isError && (
            <p className="mt-4 text-center text-sm text-accent">
              Upload failed. Check the file format and try again.
            </p>
          )}

          <div className="mt-8 rounded-xl border border-border bg-surface p-5 text-sm text-muted">
            <p className="mb-2 font-medium text-ink">Where do I get an export?</p>
            <ul className="list-disc space-y-1 pl-5">
              <li>
                <strong className="font-medium text-ink">Pocket:</strong> export
                your saves as an HTML file from your account.
              </li>
              <li>
                <strong className="font-medium text-ink">Instapaper:</strong>{" "}
                Settings → Export → Download .CSV file.
              </li>
            </ul>
          </div>
        </>
      ) : (
        <div className="card p-8">
          <div className="mb-6 flex items-center gap-3">
            {done ? (
              <CheckCircle2 className="text-accent" size={28} />
            ) : (
              <FileText className="text-accent" size={28} />
            )}
            <div>
              <p className="font-medium text-ink">
                {done
                  ? "Import complete"
                  : job?.status === "failed"
                    ? "Import failed"
                    : "Importing your library…"}
              </p>
              <p className="text-sm text-muted">
                {job?.filename ?? "Your export"} · {job?.source ?? ""}
              </p>
            </div>
          </div>

          <div className="mb-3 h-2.5 w-full overflow-hidden rounded-full bg-surface-2">
            <div
              className="h-full rounded-full bg-accent transition-all duration-500"
              style={{ width: `${pct}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-sm text-muted">
            <span>
              {job
                ? `${job.processed_count} of ${job.total_count || "…"} articles extracted`
                : "Starting…"}
            </span>
            <span>{pct}%</span>
          </div>

          {isPolling && (
            <p className="mt-4 text-sm text-muted">
              Extraction runs in the background - you can keep browsing while it
              finishes. Failed links are marked and never block the rest.
            </p>
          )}

          {done && (
            <div className="mt-6 flex gap-3">
              <Link to="/" className="btn-primary">
                View your library
              </Link>
              <button
                className="btn-outline"
                onClick={() => setImportId(undefined)}
              >
                Import another file
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
