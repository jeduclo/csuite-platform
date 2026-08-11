"use client";

import { useEffect, useRef, useState } from "react";

declare global {
  interface Window { powerbi: any; }
}

interface EmbedData {
  token: string;
  embedUrl: string;
  reportId: string;
}

interface Props {
  persona: string;
  pageName?: string;
}

function waitForPowerBI(timeout = 10000): Promise<any> {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      if (typeof window !== "undefined" && window.powerbi) {
        resolve(window.powerbi);
      } else if (Date.now() - start > timeout) {
        reject(new Error("Power BI library failed to load"));
      } else {
        setTimeout(check, 100);
      }
    };
    check();
  });
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
        const [pbi, res] = await Promise.all([
          waitForPowerBI(),
          fetch(`/api/embed-token?persona=${persona}`)
        ]);

        if (!res.ok) throw new Error("Token fetch failed");
        const data: EmbedData = await res.json();

        if (cancelled || !containerRef.current) return;

        if (reportRef.current) pbi.reset(containerRef.current);

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

        // Only set pageName if provided
        if (pageName) config.pageName = pageName;

        console.log("Embedding with config:", {
          id: config.id,
          embedUrl: config.embedUrl,
          pageName: config.pageName,
          tokenType: config.tokenType,
        });

        reportRef.current = pbi.embed(containerRef.current, config);

        reportRef.current.on("loaded", () => {
          console.log("✅ Report loaded successfully");
          if (!cancelled) setLoading(false);
        });

        reportRef.current.on("error", (e: any) => {
          const detail = JSON.stringify(e.detail, null, 2);
          console.error("❌ Power BI embed error detail:", detail);
          if (!cancelled) {
            setError(detail);
            setLoading(false);
          }
        });

        reportRef.current.on("rendered", () => {
          console.log("✅ Report rendered");
        });

      } catch (err: any) {
        if (!cancelled) {
          console.error("❌ Embed exception:", err);
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
        <div className="absolute inset-0 flex items-start justify-start bg-red-50 rounded-lg p-4 overflow-auto">
          <pre className="text-red-600 text-xs">{error}</pre>
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
