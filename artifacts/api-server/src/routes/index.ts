import { Router, type IRouter } from "express";
import healthRouter from "./health";
import sessionRouter from "./session";
import usersRouter from "./users";
import chatsRouter from "./chats";
import messagesRouter from "./messages";
import statsRouter from "./stats";

const router: IRouter = Router();

router.use(healthRouter);
router.use(sessionRouter);
router.use(usersRouter);
router.use(chatsRouter);
router.use(messagesRouter);
router.use(statsRouter);

export default router;
