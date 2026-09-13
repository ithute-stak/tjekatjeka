import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { authIssuer, clearSessionCookies, publicUrl } from "@/lib/auth-config";

export async function POST() {
  const store = await cookies();
  const refreshToken = store.get("tjekatjeka_refresh")?.value;
  if (refreshToken) {
    await fetch(`${authIssuer()}/v1/auth/logout`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store",
    }).catch(() => undefined);
  }
  const response = NextResponse.redirect(new URL("/", publicUrl()), 303);
  clearSessionCookies(response);
  return response;
}
