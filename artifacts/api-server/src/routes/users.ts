import { Router } from "express";
import { db, usersTable } from "@workspace/db";
import { eq } from "drizzle-orm";

const router = Router();

// GET /api/users — list all users
router.get("/users", async (_req, res) => {
  const users = await db.select().from(usersTable).orderBy(usersTable.name);
  res.json(
    users.map((u) => ({
      id: u.id,
      name: u.name,
      color: u.color,
      lastSeen: u.lastSeen.toISOString(),
      createdAt: u.createdAt.toISOString(),
    })),
  );
});

// GET /api/users/:userId — get single user
router.get("/users/:userId", async (req, res) => {
  const { userId } = req.params;
  const [user] = await db
    .select()
    .from(usersTable)
    .where(eq(usersTable.id, userId));
  if (!user) {
    res.status(404).json({ error: "User not found" });
    return;
  }
  res.json({
    id: user.id,
    name: user.name,
    color: user.color,
    lastSeen: user.lastSeen.toISOString(),
    createdAt: user.createdAt.toISOString(),
  });
});

export default router;
