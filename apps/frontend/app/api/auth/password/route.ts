import { NextRequest, NextResponse } from "next/server";
import { authIssuer, clientId, publicUrl, setSessionCookies, type TokenResponse } from "@/lib/auth-config";

type ErrorPayload = { detail?: string };

function redirectWithError(code: string): NextResponse {
  const response = NextResponse.redirect(new URL(`/?auth_error=${encodeURIComponent(code)}`, publicUrl()), 303);
  response.headers.set("Cache-Control", "no-store");
  return response;
}

export async function POST(request: NextRequest) {
  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return redirectWithError("missing_credentials");
  }

  const identifier = String(form.get("identifier") ?? "").trim();
  const password = String(form.get("password") ?? "");
  const mfaCode = String(form.get("mfa_code") ?? "").trim();
  if (!identifier || !password || identifier.length > 320 || password.length > 128) {
    return redirectWithError("missing_credentials");
  }

  let authResponse: Response;
  try {
    authResponse = await fetch(`${authIssuer()}/v1/auth/login`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "user-agent": request.headers.get("user-agent") ?? "Tjekatjeka Holdings",
      },
      body: JSON.stringify({
        identifier,
        password,
        client_id: clientId(),
        ...(mfaCode ? { mfa_code: mfaCode } : {}),
      }),
      cache: "no-store",
    });
  } catch {
    return redirectWithError("auth_unavailable");
  }

  if (!authResponse.ok) {
    let detail = "";
    try {
      detail = ((await authResponse.json()) as ErrorPayload).detail ?? "";
    } catch {
      // Keep the generic error when central Auth does not return JSON.
    }
    if (authResponse.status === 429) return redirectWithError("too_many_attempts");
    if (authResponse.status === 401 && detail.toLowerCase().includes("mfa")) return redirectWithError("mfa_required");
    if (authResponse.status === 401) return redirectWithError("invalid_credentials");
    if (authResponse.status === 400 && detail.toLowerCase().includes("client")) return redirectWithError("client_unavailable");
    return redirectWithError("auth_unavailable");
  }

  let tokens: TokenResponse;
  try {
    tokens = (await authResponse.json()) as TokenResponse;
  } catch {
    return redirectWithError("auth_response_invalid");
  }
  if (!tokens.access_token || !tokens.refresh_token) return redirectWithError("auth_response_invalid");

  const response = NextResponse.redirect(new URL("/dashboard", publicUrl()), 303);
  setSessionCookies(response, tokens);
  return response;
}
