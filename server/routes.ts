import type { Express, Request, Response } from "express";
import { createServer, type Server } from "http";

const FLASK_API_URL = process.env.FLASK_API_URL || "http://localhost:8080";
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY;

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  app.post("/api/chat", async (req: Request, res: Response) => {
    try {
      const { message, session_id, conversation_history } = req.body;
      
      const response = await fetch(`${FLASK_API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(INTERNAL_API_KEY && { "X-Internal-Api-Key": INTERNAL_API_KEY }),
        },
        body: JSON.stringify({
          message,
          session_id,
          conversation_history,
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Flask API error:", errorText);
        return res.status(response.status).json({ error: "Chat API error" });
      }
      
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Error proxying to Flask:", error);
      res.status(500).json({ 
        error: "Failed to connect to chat service",
        response: "I apologize, but the chat service is currently unavailable. Please try again in a moment."
      });
    }
  });

  app.post("/api/chat/stream", async (req: Request, res: Response) => {
    try {
      const { message, session_id, conversation_history } = req.body;
      
      const response = await fetch(`${FLASK_API_URL}/api/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(INTERNAL_API_KEY && { "X-Internal-Api-Key": INTERNAL_API_KEY }),
        },
        body: JSON.stringify({
          message,
          session_id,
          conversation_history,
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Flask API stream error:", errorText);
        return res.status(response.status).json({ error: "Chat stream API error" });
      }
      
      res.setHeader("Content-Type", "text/event-stream");
      res.setHeader("Cache-Control", "no-cache");
      res.setHeader("Connection", "keep-alive");
      
      if (response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          res.write(decoder.decode(value, { stream: true }));
        }
      }
      
      res.end();
    } catch (error) {
      console.error("Error proxying stream to Flask:", error);
      res.status(500).json({ error: "Failed to connect to chat service" });
    }
  });

  app.post("/api/chat/reset", async (req: Request, res: Response) => {
    try {
      const { session_id } = req.body;
      
      const response = await fetch(`${FLASK_API_URL}/api/chat/reset`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(INTERNAL_API_KEY && { "X-Internal-Api-Key": INTERNAL_API_KEY }),
        },
        body: JSON.stringify({ session_id }),
      });
      
      if (!response.ok) {
        return res.status(response.status).json({ error: "Reset API error" });
      }
      
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error("Error proxying reset to Flask:", error);
      res.status(500).json({ error: "Failed to reset conversation" });
    }
  });

  app.get("/api/health", async (_req: Request, res: Response) => {
    try {
      const response = await fetch(`${FLASK_API_URL}/health`);
      const data = await response.json();
      res.json({
        express: "healthy",
        flask: data,
      });
    } catch (error) {
      res.json({
        express: "healthy",
        flask: { status: "unreachable" },
      });
    }
  });

  return httpServer;
}
