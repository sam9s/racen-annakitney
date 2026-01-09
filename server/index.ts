import express, { type Request, Response, NextFunction } from "express";
import { registerRoutes } from "./routes";
import { serveStatic } from "./static";
import { createServer } from "http";
import { spawn } from "child_process";

const app = express();
const httpServer = createServer(app);

function startFlaskServer() {
  const flask = spawn("python3", ["webhook_server.py"], {
    cwd: process.cwd(),
    stdio: ["ignore", "pipe", "pipe"],
    detached: false,
  });

  flask.stdout?.on("data", (data) => {
    const output = data.toString().trim();
    if (output) {
      console.log(`[flask] ${output}`);
    }
  });

  flask.stderr?.on("data", (data) => {
    const output = data.toString().trim();
    if (output) {
      console.error(`[flask] ${output}`);
    }
  });

  flask.on("close", (code) => {
    console.log(`[flask] Flask server exited with code ${code}`);
    setTimeout(() => {
      console.log("[flask] Restarting Flask server...");
      startFlaskServer();
    }, 2000);
  });

  flask.on("error", (err) => {
    console.error(`[flask] Failed to start Flask server: ${err}`);
  });

  return flask;
}

startFlaskServer();

declare module "http" {
  interface IncomingMessage {
    rawBody: unknown;
  }
}

// Enable CORS for all origins (iframe embedding support)
// This is safe because the chatbot is public-facing and doesn't require authentication
app.use((req, res, next) => {
  const origin = req.headers.origin;
  
  // Allow all origins for iframe embedding
  res.setHeader("Access-Control-Allow-Origin", origin || "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With");
  res.setHeader("Access-Control-Allow-Credentials", "true");
  
  // Handle preflight requests
  if (req.method === "OPTIONS") {
    return res.sendStatus(200);
  }
  next();
});

app.use(
  express.json({
    verify: (req, _res, buf) => {
      req.rawBody = buf;
    },
  }),
);

app.use(express.urlencoded({ extended: false }));

export function log(message: string, source = "express") {
  const formattedTime = new Date().toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });

  console.log(`${formattedTime} [${source}] ${message}`);
}

app.use((req, res, next) => {
  const start = Date.now();
  const path = req.path;
  let capturedJsonResponse: Record<string, any> | undefined = undefined;

  const originalResJson = res.json;
  res.json = function (bodyJson, ...args) {
    capturedJsonResponse = bodyJson;
    return originalResJson.apply(res, [bodyJson, ...args]);
  };

  res.on("finish", () => {
    const duration = Date.now() - start;
    if (path.startsWith("/api")) {
      let logLine = `${req.method} ${path} ${res.statusCode} in ${duration}ms`;
      if (capturedJsonResponse) {
        logLine += ` :: ${JSON.stringify(capturedJsonResponse)}`;
      }

      log(logLine);
    }
  });

  next();
});

(async () => {
  await registerRoutes(httpServer, app);

  app.use((err: any, _req: Request, res: Response, _next: NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";

    res.status(status).json({ message });
    throw err;
  });

  // importantly only setup vite in development and after
  // setting up all the other routes so the catch-all route
  // doesn't interfere with the other routes
  if (process.env.NODE_ENV === "production") {
    serveStatic(app);
  } else {
    const { setupVite } = await import("./vite");
    await setupVite(httpServer, app);
  }

  // ALWAYS serve the app on the port specified in the environment variable PORT
  // Other ports are firewalled. Default to 5000 if not specified.
  // this serves both the API and the client.
  // It is the only port that is not firewalled.
  const port = parseInt(process.env.PORT || "5000", 10);
  httpServer.listen(
    {
      port,
      host: "0.0.0.0",
      reusePort: true,
    },
    () => {
      log(`serving on port ${port}`);
    },
  );
})();
