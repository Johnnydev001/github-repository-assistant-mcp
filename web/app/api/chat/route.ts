const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: Request) {
  let userText = "";

  try {
    const body = await req.json();
    const messages: unknown[] = Array.isArray(body.messages) ? body.messages : [];

    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i] as Record<string, unknown>;
      if (m?.role !== "user") continue;
      const c = m.content;
      if (typeof c === "string") {
        userText = c;
      } else if (Array.isArray(c)) {
        userText = c
          .map((p) =>
            typeof p === "object" && p !== null && "text" in p
              ? String((p as { text: unknown }).text)
              : ""
          )
          .join("")
          .trim();
      }
      break;
    }
  } catch {
    // fall through with empty userText
  }

  try {
    const backendRes = await fetch(`${BACKEND}/api/assistant`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        messages: [{ role: "user", content: userText }],
      }),
    });

    const json = await backendRes.json();
    return Response.json(json, { status: backendRes.status });
  } catch (err) {
    return Response.json(
      {
        choices: [
          {
            message: {
              role: "assistant",
              content: `Backend unreachable: ${err}`,
            },
          },
        ],
      },
      { status: 502 }
    );
  }
}
