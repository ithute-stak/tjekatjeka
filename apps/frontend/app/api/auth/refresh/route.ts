import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { authIssuer, clientId, clearSessionCookies, publicUrl, setSessionCookies, type TokenResponse } from "@/lib/auth-config";

async function rotateSession(): Promise<{ ok: true; tokens: TokenResponse } | { ok: false; status: number }> {
  const store = await cookies();
  const refreshToken = store.get("tjekatjeka_refresh")?.value;
  if (!refreshToken) return { ok: false, status: 401 };

  try {
    const response = await fetch(`${authIssuer()}/oauth/token`, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ grant_type: "refresh_token", client_id: clientId(), refresh_token: refreshToken }),
      cache: "no-store",
    });
    if (!response.ok) return { ok: false, status: 401 };
    const tokens = (await response.json()) as TokenResponse;
    if (!tokens.access_token || !tokens.refresh_token) return { ok: false, status: 502 };
    return { ok: true, tokens };
  } catch {
    return { ok: false, status: 503 };
  }
}

export async function POST() {
  const result = await rotateSession();
  if (!result.ok) {
    const response = NextResponse.json({ detail: "session refresh failed" }, { status: result.status });
    if (result.status === 401) clearSessionCookies(response);
    return response;
  }
  const response = NextResponse.json({ status: "refreshed", expires_in: result.tokens.expires_in });
  setSessionCookies(response, result.tokens);
  return response;
}

export async function GET(request: NextRequest) {
  const returnPath = request.nextUrl.searchParams.get("return");
  const safeReturn = returnPath && returnPath.startsWith("/") && !returnPath.startsWith("//") ? returnPath : "/dashboard";
  const result = await rotateSession();
  if (!result.ok) {
    const response = NextResponse.redirect(new URL("/?auth_error=session_expired", publicUrl()), 303);
    clearSessionCookies(response);
    return response;
  }
  const response = NextResponse.redirect(new URL(safeReturn, publicUrl()), 303);
  setSessionCookies(response, result.tokens);
  return response;
}
