export function authIssuer(): string {
  return (process.env.TJEKATJEKA_AUTH_ISSUER ?? "https://auth.ithute.co.ls").replace(/\/$/, "");
}

export function clientId(): string {
  return process.env.TJEKATJEKA_AUTH_CLIENT_ID ?? "tjekatjeka";
}

export function publicUrl(): string {
  return (process.env.TJEKATJEKA_PUBLIC_URL ?? "http://localhost:3204").replace(/\/$/, "");
}

export function cookieSecure(): boolean {
  return (process.env.TJEKATJEKA_COOKIE_SECURE ?? "false").toLowerCase() === "true";
}

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
};

export function setSessionCookies(response: import("next/server").NextResponse, tokens: TokenResponse) {
  const secure = cookieSecure();
  response.cookies.set("tjekatjeka_access", tokens.access_token, {
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/",
    maxAge: Math.max(60, Number(tokens.expires_in) || 600),
  });
  response.cookies.set("tjekatjeka_refresh", tokens.refresh_token, {
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/",
    maxAge: 30 * 24 * 60 * 60,
  });
  response.headers.set("Cache-Control", "no-store");
}

export function clearSessionCookies(response: import("next/server").NextResponse) {
  response.cookies.delete("tjekatjeka_access");
  response.cookies.delete("tjekatjeka_refresh");
  response.headers.set("Cache-Control", "no-store");
}
