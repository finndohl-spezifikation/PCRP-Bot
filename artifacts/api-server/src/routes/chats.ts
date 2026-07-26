import { Router } from "express";
import {
  db,
  chatsTable,
  chatParticipantsTable,
  usersTable,
  messagesTable,
  messageReadsTable,
} from "@workspace/db";
import { eq, and, inArray, desc, sql } from "drizzle-orm";
import { CreateChatBody } from "@workspace/api-zod";

const router = Router();

// Helper: get current user from cookie
function getCurrentUserId(req: Parameters<typeof router.get>[1] extends (req: infer R, ...rest: unknown[]) => unknown ? R : never): string | null {
  return (req.signedCookies?.userId as string | undefined) ?? null;
}

// GET /api/chats — list chats for current user
router.get("/chats", async (req, res) => {
  const userId = (req as any).signedCookies?.userId as string | undefined;

  // Return all chats if no user (demo mode)
  let chatIds: string[];
  if (userId) {
    const participations = await db
      .select({ chatId: chatParticipantsTable.chatId })
      .from(chatParticipantsTable)
      .where(eq(chatParticipantsTable.userId, userId));
    chatIds = participations.map((p) => p.chatId);
  } else {
    const allChats = await db.select({ id: chatsTable.id }).from(chatsTable);
    chatIds = allChats.map((c) => c.id);
  }

  if (chatIds.length === 0) {
    res.json([]);
    return;
  }

  const chats = await db
    .select()
    .from(chatsTable)
    .where(inArray(chatsTable.id, chatIds))
    .orderBy(desc(chatsTable.createdAt));

  const results = await Promise.all(
    chats.map(async (chat) => {
      // Get participants
      const parts = await db
        .select({ userId: chatParticipantsTable.userId })
        .from(chatParticipantsTable)
        .where(eq(chatParticipantsTable.chatId, chat.id));
      const partUserIds = parts.map((p) => p.userId);
      const participants =
        partUserIds.length > 0
          ? await db
              .select()
              .from(usersTable)
              .where(inArray(usersTable.id, partUserIds))
          : [];

      // Get last message
      const [lastMsg] = await db
        .select()
        .from(messagesTable)
        .where(eq(messagesTable.chatId, chat.id))
        .orderBy(desc(messagesTable.createdAt))
        .limit(1);

      let lastMessage = null;
      if (lastMsg) {
        const sender = participants.find((p) => p.id === lastMsg.senderId);
        const reads = await db
          .select({ userId: messageReadsTable.userId })
          .from(messageReadsTable)
          .where(eq(messageReadsTable.messageId, lastMsg.id));
        lastMessage = {
          id: lastMsg.id,
          chatId: lastMsg.chatId,
          senderId: lastMsg.senderId,
          senderName: sender?.name ?? "Unknown",
          senderColor: sender?.color ?? "#888",
          content: lastMsg.content,
          readBy: reads.map((r) => r.userId),
          createdAt: lastMsg.createdAt.toISOString(),
        };
      }

      // Unread count
      let unreadCount = 0;
      if (userId) {
        const allMessages = await db
          .select({ id: messagesTable.id })
          .from(messagesTable)
          .where(eq(messagesTable.chatId, chat.id));
        for (const msg of allMessages) {
          const [read] = await db
            .select()
            .from(messageReadsTable)
            .where(
              and(
                eq(messageReadsTable.messageId, msg.id),
                eq(messageReadsTable.userId, userId),
              ),
            );
          if (!read) unreadCount++;
        }
      }

      return {
        id: chat.id,
        name: chat.name,
        isGroup: chat.isGroup,
        participants: participants.map((p) => ({
          id: p.id,
          name: p.name,
          color: p.color,
          lastSeen: p.lastSeen.toISOString(),
          createdAt: p.createdAt.toISOString(),
        })),
        lastMessage,
        unreadCount,
        createdAt: chat.createdAt.toISOString(),
      };
    }),
  );

  res.json(results);
});

// POST /api/chats — create chat
router.post("/chats", async (req, res) => {
  const parsed = CreateChatBody.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid request" });
    return;
  }
  const { participantIds, name, isGroup } = parsed.data;

  if (!participantIds || participantIds.length === 0) {
    res.status(400).json({ error: "At least one participant required" });
    return;
  }

  // For 1:1 chats, check if one already exists
  if (!isGroup && participantIds.length === 2) {
    const [a, b] = participantIds;
    const existing = await db
      .select({ chatId: chatParticipantsTable.chatId })
      .from(chatParticipantsTable)
      .where(eq(chatParticipantsTable.userId, a));
    const existingIds = existing.map((e) => e.chatId);
    if (existingIds.length > 0) {
      const shared = await db
        .select({ chatId: chatParticipantsTable.chatId })
        .from(chatParticipantsTable)
        .where(
          and(
            inArray(chatParticipantsTable.chatId, existingIds),
            eq(chatParticipantsTable.userId, b),
          ),
        );
      if (shared.length > 0) {
        // Return existing chat
        const [chat] = await db
          .select()
          .from(chatsTable)
          .where(eq(chatsTable.id, shared[0].chatId));
        if (chat) {
          const parts = await db
            .select()
            .from(usersTable)
            .where(inArray(usersTable.id, participantIds));
          res.status(201).json({
            id: chat.id,
            name: chat.name,
            isGroup: chat.isGroup,
            participants: parts.map((p) => ({
              id: p.id,
              name: p.name,
              color: p.color,
              lastSeen: p.lastSeen.toISOString(),
              createdAt: p.createdAt.toISOString(),
            })),
            createdAt: chat.createdAt.toISOString(),
          });
          return;
        }
      }
    }
  }

  // Derive chat name
  let chatName = name ?? "";
  if (!chatName) {
    const users = await db
      .select()
      .from(usersTable)
      .where(inArray(usersTable.id, participantIds));
    chatName = users.map((u) => u.name).join(", ");
  }

  const chatId = crypto.randomUUID();
  await db.insert(chatsTable).values({
    id: chatId,
    name: chatName,
    isGroup: isGroup ?? participantIds.length > 2,
  });

  await db.insert(chatParticipantsTable).values(
    participantIds.map((uid) => ({ chatId, userId: uid })),
  );

  const participants = await db
    .select()
    .from(usersTable)
    .where(inArray(usersTable.id, participantIds));

  res.status(201).json({
    id: chatId,
    name: chatName,
    isGroup: isGroup ?? participantIds.length > 2,
    participants: participants.map((p) => ({
      id: p.id,
      name: p.name,
      color: p.color,
      lastSeen: p.lastSeen.toISOString(),
      createdAt: p.createdAt.toISOString(),
    })),
    createdAt: new Date().toISOString(),
  });
});

// GET /api/chats/:chatId — get single chat
router.get("/chats/:chatId", async (req, res) => {
  const { chatId } = req.params;
  const [chat] = await db
    .select()
    .from(chatsTable)
    .where(eq(chatsTable.id, chatId));
  if (!chat) {
    res.status(404).json({ error: "Chat not found" });
    return;
  }
  const parts = await db
    .select({ userId: chatParticipantsTable.userId })
    .from(chatParticipantsTable)
    .where(eq(chatParticipantsTable.chatId, chatId));
  const partUserIds = parts.map((p) => p.userId);
  const participants =
    partUserIds.length > 0
      ? await db
          .select()
          .from(usersTable)
          .where(inArray(usersTable.id, partUserIds))
      : [];

  res.json({
    id: chat.id,
    name: chat.name,
    isGroup: chat.isGroup,
    participants: participants.map((p) => ({
      id: p.id,
      name: p.name,
      color: p.color,
      lastSeen: p.lastSeen.toISOString(),
      createdAt: p.createdAt.toISOString(),
    })),
    createdAt: chat.createdAt.toISOString(),
  });
});

export default router;
