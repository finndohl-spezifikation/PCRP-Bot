import { Router } from "express";
import { db, usersTable, chatsTable, messagesTable } from "@workspace/db";
import { sql } from "drizzle-orm";

const router = Router();

router.get("/stats", async (_req, res) => {
  const [[{ count: totalMessages }], [{ count: totalUsers }], [{ count: totalChats }]] =
    await Promise.all([
      db.select({ count: sql<number>`count(*)::int` }).from(messagesTable),
      db.select({ count: sql<number>`count(*)::int` }).from(usersTable),
      db.select({ count: sql<number>`count(*)::int` }).from(chatsTable),
    ]);

  res.json({ totalMessages, totalUsers, totalChats });
});

export default router;
