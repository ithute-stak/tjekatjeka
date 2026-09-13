import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const backend = process.env.TJEKATJEKA_BACKEND_INTERNAL_URL ?? "http://localhost:8204";

type Context = { params: Promise<{ path: string[] }> };

async function forward(request: NextRequest, context: Context) {
  const { path } = await context.params;
  const store = await cookies();
  const token = store.get("tjekatjeka_access")?.value;
  const url = `${backend}/api/v1/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`;
  const hasBody = !["GET", "HEAD"].includes(request.method);
  const body = hasBody ? await request.arrayBuffer() : undefined;

  try {
    const response = await fetch(url, {
      method: request.method,
      cache: "no-store",
      body: body && body.byteLength ? body : undefined,
      headers: {
        Accept: request.headers.get("accept") ?? "*/*",
        ...(body && body.byteLength ? { "Content-Type": request.headers.get("content-type") ?? "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
    const payload = await response.arrayBuffer();
    const headers = new Headers();
    const contentType = response.headers.get("content-type");
    const contentDisposition = response.headers.get("content-disposition");
    if (contentType) headers.set("Content-Type", contentType);
    if (contentDisposition) headers.set("Content-Disposition", contentDisposition);
    return new NextResponse(payload, { status: response.status, headers });
  } catch {
    return NextResponse.json({ detail: "Tjekatjeka backend is unavailable" }, { status: 503 });
  }
}

export async function GET(request: NextRequest, context: Context) {
  return forward(request, context);
}

export async function POST(request: NextRequest, context: Context) {
  return forward(request, context);
}

export async function PATCH(request: NextRequest, context: Context) {
  return forward(request, context);
}
