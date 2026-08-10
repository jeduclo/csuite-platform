"use client";

import { useEffect, useRef, useState } from "react";

declare global {
  interface Window {
    powerbi: any;
  }
}

interface EmbedData {
  token:    string;
  embedUrl: string;
  reportId: string;
}

interface Props {
  persona:   string;
  pageName?: string;
}

export default function PowerBIEmbed({ persona, pageName }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const reportRef    = useRef<any>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function embed() {
      setLoading(true);
      setError(null);

      try {
        const res  = await fetch(`/api/embed-token?persona=${persona}`);
        if (!res.ok) throw new Error("Token fetch failed");
        const data: EmbedData = await res.json();

        if (cancelled || !containerRef.current) return;

        if (reportRef.current) {
          window.powerbi.reset(containerRef.current);
        }

        const config: any = {
          type:        "report",
          id:          data.reportId,
          embedUrl:    data.embedUrl,
          accessToken: data.token,
          tokenType:   1,
          settings: {
            navContentPaneEnabled: false,
            filterPaneEnabled:     false,
            background:            2,
          },
        };

        if (pageName) config.pageName = pageName;

        reportRef.current = window.powerbi.embed(containerRef.current, config);
        reportRef.current.on("loaded", () => setLoading(false));
        reportRef.current.on("error",  (e: any) => {
          console.error("Power BI embed error:", e.detail);
          setError("Report failed to load. Please refresh.");
          setLoading(false);
        });
      } catch (err: any) {
        if (!cancelled) {
          setError(err.message ?? "Embed error");
          setLoading(false);
        }
      }
    }

    embed();
    return () => { cancelled = true; };
  }, [persona, pageName]);

  return (
    <div className="relative w-full" style={{ height: "85vh" }}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-100 rounded-lg">
          <div className="text-slate-500 text-sm animate-pulse">Loading report…</div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 rounded-lg">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}
      <div
        ref={containerRef}
        className="w-full h-full rounded-lg border border-slate-200 overflow-hidden"
        style={{ visibility: loading ? "hidden" : "visible" }}
      />
    </div>
  );
}
