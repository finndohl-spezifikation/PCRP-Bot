import path from "path";
import express, { type Express } from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import pinoHttp from "pino-http";
import router from "./routes";
import { logger } from "./lib/logger";

const app: Express = express();

// Trust Railway / Render / Fly reverse-proxy so that req.secure works
// and Set-Cookie: Secure cookies are correctly set over HTTPS.
app.set("trust proxy", 1);

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return { id: req.id, method: req.method, url: req.url?.split("?")[0] };
      },
      res(res) {
        return { statusCode: res.statusCode };
      },
    },
  }),
);

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser(process.env.SESSION_SECRET ?? "pcrp-whatsapp-secret"));

// API routes
app.use("/api", router);

// ── Production: serve the built Vite frontend ─────────────────────────────
if (process.env.NODE_ENV === "production") {
  const STATIC_DIR =
    process.env.STATIC_DIR ??
    path.resolve(process.cwd(), "artifacts/whatsapp/dist/public");

  app.use(express.static(STATIC_DIR));

  // SPA fallback — send index.html for every non-API route
  app.get("*", (_req, res) => {
    res.sendFile(path.join(STATIC_DIR, "index.html"));
  });
}

export default app;
