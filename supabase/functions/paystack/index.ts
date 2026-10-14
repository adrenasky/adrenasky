// Adrenasky payments through Paystack.
//   POST /paystack/init     (signed-in user)  -> starts a checkout at the server-side price
//   POST /paystack/verify   (signed-in user)  -> confirms a checkout with Paystack and unlocks access
//   POST /paystack/webhook  (Paystack only)   -> same unlock, signed by Paystack, in case the browser closes early
// Needs the secret PAYSTACK_SECRET_KEY (sk_test_... or sk_live_...), set in Supabase > Edge Functions > Secrets.
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const SECRET = (Deno.env.get("PAYSTACK_SECRET_KEY") ?? "").trim();
const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
const ORIGINS = ["https://adrenasky.com", "https://www.adrenasky.com", "https://adrenasky.vercel.app"];

function cors(req: Request) {
  const o = req.headers.get("origin") ?? "";
  return {
    "Access-Control-Allow-Origin": ORIGINS.includes(o) ? o : ORIGINS[0],
    "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info, x-device-id",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}
const json = (req: Request, body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors(req), "Content-Type": "application/json" } });

async function paystack(path: string, init: RequestInit = {}) {
  const r = await fetch("https://api.paystack.co" + path, {
    ...init,
    headers: { Authorization: `Bearer ${SECRET}`, "Content-Type": "application/json", ...(init.headers ?? {}) },
  });
  return await r.json();
}

async function signedInUser(req: Request) {
  const token = (req.headers.get("authorization") ?? "").replace(/^Bearer\s+/i, "");
  if (!token) return null;
  const { data } = await admin.auth.getUser(token);
  return data.user ?? null;
}

async function verifyAndGrant(reference: string) {
  const v = await paystack(`/transaction/verify/${encodeURIComponent(reference)}`);
  if (!v.status || !v.data) return { ok: false, result: "not_found" };
  if (v.data.status !== "success" || v.data.currency !== "KES") return { ok: false, result: v.data.status };
  const { data, error } = await admin.rpc("grant_payment", {
    p_ref: reference, p_amount_kobo: v.data.amount, p_channel: v.data.channel ?? null,
  });
  if (error) return { ok: false, result: "db_error" };
  return { ok: data === "granted" || data === "already", result: data };
}

async function hmacSha512(key: string, body: string) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(key), { name: "HMAC", hash: "SHA-512" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(body));
  return Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors(req) });
  if (req.method !== "POST") return json(req, { error: "method" }, 405);
  if (!SECRET) return json(req, { error: "Payments aren't set up yet." }, 503);
  const path = new URL(req.url).pathname;

  // Paystack's server calls this; it is checked by signature, not by login.
  if (path.endsWith("/webhook")) {
    const body = await req.text();
    const sig = req.headers.get("x-paystack-signature") ?? "";
    if (sig !== (await hmacSha512(SECRET, body))) return new Response("bad signature", { status: 401 });
    const ev = JSON.parse(body);
    if (ev.event === "charge.success" && ev.data?.reference) await verifyAndGrant(ev.data.reference);
    return new Response("ok");
  }

  const user = await signedInUser(req);
  if (!user) return json(req, { error: "Please log in again." }, 401);
  const input = await req.json().catch(() => ({}));

  if (path.endsWith("/init")) {
    const plan = input.plan === "all" ? "all" : "subject";
    const subject = plan === "subject" ? String(input.subject_id ?? "") : null;
    const { data: price } = await admin.from("prices").select("amount_kes,days,label,is_active").eq("plan", plan).single();
    if (!price || !price.is_active) return json(req, { error: "This plan isn't available." }, 400);
    if (plan === "subject") {
      const { data: s } = await admin.from("subjects").select("id,status").eq("id", subject).single();
      if (!s || s.status !== "live") return json(req, { error: "Choose a live subject." }, 400);
    }
    const reference = `ADR-${Date.now()}-${crypto.randomUUID().slice(0, 8)}`;
    const { error } = await admin.from("payments").insert({
      reference, user_id: user.id, plan, subject_id: subject, amount_kes: price.amount_kes, days: price.days,
    });
    if (error) return json(req, { error: "Couldn't start the payment." }, 500);
    const t = await paystack("/transaction/initialize", {
      method: "POST",
      body: JSON.stringify({
        email: user.email, amount: price.amount_kes * 100, currency: "KES", reference,
        channels: ["mobile_money", "card"],
        metadata: { user_id: user.id, plan, subject_id: subject, custom_fields: [{ display_name: "Plan", variable_name: "plan", value: price.label }] },
      }),
    });
    if (!t.status) {
      console.log("paystack initialize rejected:", JSON.stringify({ message: t.message, code: t.code, key: SECRET.slice(0, 8) }));
      await admin.from("payments").update({ status: "init_failed" }).eq("reference", reference);
      return json(req, { error: t.message ?? "Paystack didn't accept the payment." }, 502);
    }
    return json(req, { reference, access_code: t.data.access_code, authorization_url: t.data.authorization_url });
  }

  if (path.endsWith("/verify")) {
    const reference = String(input.reference ?? "");
    const { data: p } = await admin.from("payments").select("user_id").eq("reference", reference).single();
    if (!p || p.user_id !== user.id) return json(req, { error: "Payment not found." }, 404);
    const r = await verifyAndGrant(reference);
    return json(req, r, r.ok ? 200 : 402);
  }

  return json(req, { error: "not found" }, 404);
});
