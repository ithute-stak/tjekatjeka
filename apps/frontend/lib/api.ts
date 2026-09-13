import { cookies } from "next/headers";

const backend = process.env.TJEKATJEKA_BACKEND_INTERNAL_URL ?? "http://localhost:8204";

export async function apiGet<T>(path: string, fallback: T): Promise<T> {
  try {
    const store = await cookies();
    const token = store.get("tjekatjeka_access")?.value;
    const response = await fetch(`${backend}/api/v1/${path}`, {
      cache: "no-store",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!response.ok) return fallback;
    return (await response.json()) as T;
  } catch {
    return fallback;
  }
}

export function money(value: unknown): string {
  const number = typeof value === "number" ? value : Number(value ?? 0);
  return new Intl.NumberFormat("en-LS", {
    style: "currency",
    currency: "LSL",
    maximumFractionDigits: 2,
  }).format(Number.isFinite(number) ? number : 0);
}

export function number(value: unknown, maximumFractionDigits = 2): string {
  const numeric = typeof value === "number" ? value : Number(value ?? 0);
  return new Intl.NumberFormat("en-LS", { maximumFractionDigits }).format(
    Number.isFinite(numeric) ? numeric : 0,
  );
}
