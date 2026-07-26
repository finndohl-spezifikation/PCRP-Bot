import { Router } from "express";
import {
  db,
  messagesTable,
  messageReadsTable,
  usersTable,
  chatParticipantsTable,
} from "@workspace/db";
import { eq, asc, and, inArray } from "drizzle-orm";
import { SendMessageBody } from "@workspace/api-zod";

const router = Router();

// GET /api/chats/:chatId/messages
router.get("/chats/:chatId/messages", async (req, res) => {
  const { chatId } = req.params;

  const msgs = await db
    .select()
    .from(messagesTable)
    .where(eq(messagesTable.chatId, chatId))
    .orderBy(asc(messagesTable.createdAt))
    .limit(200);

  const senderIds = [...new Set(msgs.map((m) => m.senderId))];
  const senders =
    senderIds.length > 0
      ? await db
          .select()
          .from(usersTable)
          .where(inArray(usersTable.id, senderIds))
      : [];
  const senderMap = new Map(senders.map((s) => [s.id, s]));

  const result = await Promise.all(
    msgs.map(async (msg) => {
      const sender = senderMap.get(msg.senderId);
      const reads = await db
        .select({ userId: messageReadsTable.userId })
        .from(messageReadsTable)
        .where(eq(messageReadsTable.messageId, msg.id));
      return {
        id: msg.id,
        chatId: msg.chatId,
        senderId: msg.senderId,
        senderName: sender?.name ?? "Unknown",
        senderColor: sender?.color ?? "#888",
        content: msg.content,
        readBy: reads.map((r) => r.userId),
        createdAt: msg.createdAt.toISOString(),
      };
    }),
  );

  res.json(result);
});

// POST /api/chats/:chatId/messages — send a message
router.post("/chats/:chatId/messages", async (req, res) => {
  const { chatId } = req.params;
  const parsed = SendMessageBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid request" });
    return;
  }
  const { content, senderId } = parsed.data;

  const msgId = crypto.randomUUID();
  await db.insert(messagesTable).values({
    id: msgId,
    chatId,
    senderId,
    content: content.trim(),
  });

  // Auto-mark as read by sender
  await db
    .insert(messageReadsTable)
    .values({ messageId: msgId, userId: senderId })
    .onConflictDoNothing();

  const [sender] = await db
    .select()
    .from(usersTable)
    .where(eq(usersTable.id, senderId));

  res.status(201).json({
    id: msgId,
    chatId,
    senderId,
    senderName: sender?.name ?? "Unknown",
    senderColor: sender?.color ?? "#888",
    content: content.trim(),
    readBy: [senderId],
    createdAt: new Date().toISOString(),
  });
});

// POST /api/chats/:chatId/read — mark all messages in chat as read
router.post("/chats/:chatId/read", async (req, res) => {
  const { chatId } = req.params;
  const userId = (req as any).signedCookies?.userId as string | undefined;
  if (!userId) {
    res.json({ updated: 0 });
    return;
  }

  const msgs = await db
    .select({ id: messagesTable.id })
    .from(messagesTable)
    .where(eq(messagesTable.chatId, chatId));

  let updated = 0;
  for (const msg of msgs) {
    const result = await db
      .insert(messageReadsTable)
      .values({ messageId: msg.id, userId })
      .onConflictDoNothing();
    if ((result as any).rowCount > 0) updated++;
  }

  res.json({ updated });
});

export default router;
