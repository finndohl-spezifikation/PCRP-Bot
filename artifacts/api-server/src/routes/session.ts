import { Router } from "express";
import { db, usersTable } from "@workspace/db";
import { eq } from "drizzle-orm";
import { CreateSessionBody } from "@workspace/api-zod";

const router = Router();

const AVATAR_COLORS = [
  "#D32F2F", "#C2185B", "#7B1FA2", "#512DA8",
  "#1976D2", "#0288D1", "#00796B", "#388E3C",
  "#F57C00", "#5D4037", "#455A64", "#E91E63",
];

function pickColor(name: string): string {
  let hash = 0;
  for (const c of name) hash = (hash * 31 + c.charCodeAt(0)) & 0xffffffff;
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

// POST /api/session — create or resume session
router.post("/session", async (req, res) => {
  const parsed = CreateSessionBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid request" });
    return;
  }
  const { name } = parsed.data;
  const trimmed = name.trim();

  // Check existing cookie first
  const existingId = req.signedCookies?.userId as string | undefined;
  if (existingId) {
    const [existing] = await db
      .select()
      .from(usersTable)
      .where(eq(usersTable.id, existingId));
    if (existing) {
      // Update lastSeen
      await db
        .update(usersTable)
        .set({ lastSeen: new Date() })
        .where(eq(usersTable.id, existingId));
      res
        .cookie("userId", existing.id, {
          signed: true,
          httpOnly: true,
          maxAge: 30 * 24 * 60 * 60 * 1000,
          sameSite: "lax",
        })
        .json({
          id: existing.id,
          name: existing.name,
          color: existing.color,
          createdAt: existing.createdAt.toISOString(),
        });
      return;
    }
  }

  // Find existing user by name (case-insensitive)
  const [existing] = await db
    .select()
    .from(usersTable)
    .where(eq(usersTable.name, trimmed));

  if (existing) {
    await db
      .update(usersTable)
      .set({ lastSeen: new Date() })
      .where(eq(usersTable.id, existing.id));
    res
      .cookie("userId", existing.id, {
        signed: true,
        httpOnly: true,
        maxAge: 30 * 24 * 60 * 60 * 1000,
        sameSite: "lax",
      })
      .json({
        id: existing.id,
        name: existing.name,
        color: existing.color,
        createdAt: existing.createdAt.toISOString(),
      });
    return;
  }

  // Create new user
  const id = crypto.randomUUID();
  const color = pickColor(trimmed);
  await db.insert(usersTable).values({ id, name: trimmed, color });
  res
    .cookie("userId", id, {
      signed: true,
      httpOnly: true,
      maxAge: 30 * 24 * 60 * 60 * 1000,
      sameSite: "lax",
    })
    .json({
      id,
      name: trimmed,
      color,
      createdAt: new Date().toISOString(),
    });
});

// GET /api/session — return current session user
router.get("/session", async (req, res) => {
  const userId = req.signedCookies?.userId as string | undefined;
  if (!userId) {
    res.status(401).json({ error: "Not authenticated" });
    return;
  }
  const [user] = await db
    .select()
    .from(usersTable)
    .where(eq(usersTable.id, userId));
  if (!user) {
    res.status(401).json({ error: "Not authenticated" });
    return;
  }
  // Touch lastSeen
  await db
    .update(usersTable)
    .set({ lastSeen: new Date() })
    .where(eq(usersTable.id, userId));
  res.json({
    id: user.id,
    name: user.name,
    color: user.color,
    createdAt: user.createdAt.toISOString(),
  });
});

// DELETE /api/session — logout (clear cookie)
router.delete("/session", (req, res) => {
  res.clearCookie("userId").json({ ok: true });
});

export default router;
