import { NextRequest, NextResponse } from "next/server";

const TENANT_ID     = process.env.POWERBI_TENANT_ID!;
const CLIENT_ID     = process.env.POWERBI_CLIENT_ID!;
const CLIENT_SECRET = process.env.POWERBI_CLIENT_SECRET!;
const WORKSPACE_ID  = process.env.POWERBI_WORKSPACE_ID!;

const REPORT_IDS: Record<string, string> = {
  action_queue: process.env.POWERBI_REPORT_ID_ACTION_QUEUE!,
  ceo:          process.env.POWERBI_REPORT_ID_CEO!,
  cfo:          process.env.POWERBI_REPORT_ID_CFO!,
  cro:          process.env.POWERBI_REPORT_ID_CRO!,
  coo:          process.env.POWERBI_REPORT_ID_COO!,
  pl:           process.env.POWERBI_REPORT_ID_ACTION_QUEUE!, // same report, different page
};

async function getAzureADToken(): Promise<string> {
  const url  = `https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token`;
  const body = new URLSearchParams({
    grant_type:    "client_credentials",
    client_id:     CLIENT_ID,
    client_secret: CLIENT_SECRET,
    scope:         "https://analysis.windows.net/powerbi/api/.default",
  });
  const res  = await fetch(url, { method: "POST", body });
  const data = await res.json();
  if (!data.access_token) throw new Error("AAD token fetch failed");
  return data.access_token;
}

async function getEmbedToken(
  aadToken: string,
  reportId: string
): Promise<{ token: string; expiry: string; embedUrl: string }> {
  const reportRes = await fetch(
    `https://api.powerbi.com/v1.0/myorg/groups/${WORKSPACE_ID}/reports/${reportId}`,
    { headers: { Authorization: `Bearer ${aadToken}` } }
  );
  const reportData = await reportRes.json();
  const embedUrl   = reportData.embedUrl;

  const tokenRes = await fetch(
    `https://api.powerbi.com/v1.0/myorg/groups/${WORKSPACE_ID}/reports/${reportId}/GenerateToken`,
    {
      method:  "POST",
      headers: { Authorization: `Bearer ${aadToken}`, "Content-Type": "application/json" },
      body: JSON.stringify({ accessLevel: "View" }),
    }
  );
  const tokenData = await tokenRes.json();
  return { token: tokenData.token, expiry: tokenData.expiration, embedUrl };
}

export async function GET(req: NextRequest) {
  const persona  = req.nextUrl.searchParams.get("persona") ?? "action_queue";
  const reportId = REPORT_IDS[persona];

  if (!reportId) {
    return NextResponse.json({ error: "Unknown persona" }, { status: 400 });
  }

  try {
    const aadToken = await getAzureADToken();
    const { token, expiry, embedUrl } = await getEmbedToken(aadToken, reportId);
    return NextResponse.json(
      { token, expiry, embedUrl, reportId },
      { headers: { "Cache-Control": "private, max-age=3300" } }
    );
  } catch (err) {
    console.error("Embed token error:", err);
    return NextResponse.json({ error: "Token generation failed" }, { status: 500 });
  }
}
