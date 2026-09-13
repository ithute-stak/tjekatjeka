import { NextRequest, NextResponse } from "next/server";

export function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const access = request.cookies.get("tjekatjeka_access")?.value;
  const refresh = request.cookies.get("tjekatjeka_refresh")?.value;

  if (pathname === "/") {
    if (access) return NextResponse.redirect(new URL("/dashboard", request.url));
    return NextResponse.next();
  }

  if (access) return NextResponse.next();
  if (refresh) {
    const refreshUrl = new URL("/api/auth/refresh", request.url);
    refreshUrl.searchParams.set("return", `${pathname}${request.nextUrl.search}`);
    return NextResponse.redirect(refreshUrl, 307);
  }

  const loginUrl = new URL("/", request.url);
  loginUrl.searchParams.set("auth_error", "session_expired");
  return NextResponse.redirect(loginUrl, 307);
}

export const config = {
  matcher: ["/((?!api/|_next/|favicon.ico|robots.txt).*)"],
};
