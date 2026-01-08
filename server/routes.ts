import type { Express, Request, Response } from "express";
import { createServer, type Server } from "http";
import path from "path";
import fs from "fs";
import {
  listCalendars,
  findAnnaCalendar,
  getUpcomingEvents,
  searchEvents,
  getEventByTitle,
  addEventToCalendar,
  formatEventForChat,
  formatEventsListForChat,
  type EventInfo
} from "./calendar-service";
import {
  syncAllEvents,
  startScheduledSync,
  handleCalendarWebhook,
  getEventsFromDatabase,
  getEventFromDatabaseByTitle
} from "./calendar-sync-service";

const FLASK_API_URL = process.env.FLASK_API_URL || "http://localhost:8080";
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY;

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  // Serve widget.js explicitly BEFORE Vite catches it
  // This is required because Vite's catch-all returns index.html for all requests
  app.get("/widget.js", (req: Request, res: Response) => {
    const widgetPath = path.resolve(process.cwd(), "public", "widget.js");
    if (fs.existsSync(widgetPath)) {
      res.setHeader("Content-Type", "application/javascript");
      res.setHeader("Cache-Control", "no-cache, no-store, must-revalidate");
      res.sendFile(widgetPath);
    } else {
      res.status(404).send("Widget not found");
    }
  });
  
  // Serve anna-logo.png for the widget avatar
  app.get("/anna-logo.png", (req: Request, res: Response) => {
    const logoPath = path.resolve(process.cwd(), "public", "anna-logo.png");
    if (fs.existsSync(logoPath)) {
      res.setHeader("Cache-Control", "public, max-age=86400");
      res.sendFile(logoPath);
    } else {
      res.status(404).send("Logo not found");
    }
  });
  
  // Serve test scenarios JSON for the GUI test runner
  app.get("/tests/comprehensive_test_scenarios.json", (req: Request, res: Response) => {
    const testPath = path.resolve(process.cwd(), "tests", "comprehensive_test_scenarios.json");
    if (fs.existsSync(testPath)) {
      res.setHeader("Content-Type", "application/json");
      res.setHeader("Cache-Control", "no-cache");
      res.sendFile(testPath);
    } else {
      res.status(404).json({ error: "Test scenarios not found" });
    }
  });
  
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

  // ============ GOOGLE CALENDAR ENDPOINTS ============

  // List all calendars (for debugging/finding Anna's calendar)
  app.get("/api/calendars", async (_req: Request, res: Response) => {
    try {
      const calendars = await listCalendars();
      res.json({ calendars });
    } catch (error: any) {
      console.error("Error listing calendars:", error);
      res.status(500).json({ error: error.message || "Failed to list calendars" });
    }
  });

  // Find Anna's calendar
  app.get("/api/calendars/anna", async (_req: Request, res: Response) => {
    try {
      const annaCalendar = await findAnnaCalendar();
      if (annaCalendar) {
        res.json({ calendar: annaCalendar });
      } else {
        res.status(404).json({ error: "Anna's calendar not found" });
      }
    } catch (error: any) {
      console.error("Error finding Anna's calendar:", error);
      res.status(500).json({ error: error.message || "Failed to find calendar" });
    }
  });

  // Get upcoming events
  app.get("/api/events", async (req: Request, res: Response) => {
    try {
      const limit = parseInt(req.query.limit as string) || 20;
      const events = await getUpcomingEvents(limit);
      res.json({ events });
    } catch (error: any) {
      console.error("Error fetching events:", error);
      res.status(500).json({ error: error.message || "Failed to fetch events" });
    }
  });

  // Search events
  app.get("/api/events/search", async (req: Request, res: Response) => {
    try {
      const query = req.query.q as string;
      if (!query) {
        return res.status(400).json({ error: "Query parameter 'q' is required" });
      }
      const events = await searchEvents(query);
      res.json({ events });
    } catch (error: any) {
      console.error("Error searching events:", error);
      res.status(500).json({ error: error.message || "Failed to search events" });
    }
  });

  // Get event by title
  app.get("/api/events/by-title/:title", async (req: Request, res: Response) => {
    try {
      const title = decodeURIComponent(req.params.title);
      const event = await getEventByTitle(title);
      if (event) {
        res.json({ event, formatted: formatEventForChat(event) });
      } else {
        res.status(404).json({ error: "Event not found" });
      }
    } catch (error: any) {
      console.error("Error fetching event:", error);
      res.status(500).json({ error: error.message || "Failed to fetch event" });
    }
  });

  // Add event to calendar (booking feature)
  app.post("/api/events/book", async (req: Request, res: Response) => {
    try {
      const { title, description, start, end, location, calendarId } = req.body;
      
      if (!title || !start || !end) {
        return res.status(400).json({ error: "title, start, and end are required" });
      }
      
      const result = await addEventToCalendar(
        { title, description, start, end, location },
        calendarId || 'primary'
      );
      
      if (result.success) {
        res.json({ success: true, eventLink: result.eventLink });
      } else {
        res.status(500).json({ error: result.error });
      }
    } catch (error: any) {
      console.error("Error booking event:", error);
      res.status(500).json({ error: error.message || "Failed to book event" });
    }
  });

  // Get formatted events list for chatbot
  app.get("/api/events/formatted", async (req: Request, res: Response) => {
    try {
      const limit = parseInt(req.query.limit as string) || 10;
      const events = await getUpcomingEvents(limit);
      res.json({ 
        events,
        formatted: formatEventsListForChat(events)
      });
    } catch (error: any) {
      console.error("Error fetching formatted events:", error);
      res.status(500).json({ error: error.message || "Failed to fetch events" });
    }
  });

  // ============ CALENDAR SYNC ENDPOINTS ============

  // Get events from PostgreSQL database (synced from Google Calendar)
  app.get("/api/events/db", async (req: Request, res: Response) => {
    try {
      const includeInactive = req.query.includeInactive === 'true';
      const events = await getEventsFromDatabase(includeInactive);
      res.json({ events, count: events.length });
    } catch (error: any) {
      console.error("Error fetching events from database:", error);
      res.status(500).json({ error: error.message || "Failed to fetch events from database" });
    }
  });

  // Get specific event from database by title
  app.get("/api/events/db/by-title/:title", async (req: Request, res: Response) => {
    try {
      const title = decodeURIComponent(req.params.title);
      const event = await getEventFromDatabaseByTitle(title);
      if (event) {
        res.json({ event });
      } else {
        res.status(404).json({ error: "Event not found in database" });
      }
    } catch (error: any) {
      console.error("Error fetching event from database:", error);
      res.status(500).json({ error: error.message || "Failed to fetch event" });
    }
  });

  // Manual sync trigger
  app.post("/api/calendar/sync", async (_req: Request, res: Response) => {
    try {
      console.log("Manual calendar sync triggered");
      const result = await syncAllEvents();
      res.json({ 
        success: true, 
        message: `Sync complete: ${result.synced} events synced, ${result.errors} errors`,
        ...result
      });
    } catch (error: any) {
      console.error("Error during manual sync:", error);
      res.status(500).json({ error: error.message || "Sync failed" });
    }
  });

  // Google Calendar webhook endpoint
  // This receives push notifications when calendar changes
  app.post("/api/calendar/webhook", async (req: Request, res: Response) => {
    try {
      const channelId = req.headers['x-goog-channel-id'] as string;
      const resourceId = req.headers['x-goog-resource-id'] as string;
      const resourceState = req.headers['x-goog-resource-state'] as string;

      console.log(`Webhook received: state=${resourceState}, channel=${channelId}`);

      if (resourceState && channelId) {
        await handleCalendarWebhook(channelId, resourceId, resourceState);
      }

      // Google requires a 200 response
      res.status(200).send('OK');
    } catch (error: any) {
      console.error("Error handling webhook:", error);
      // Still return 200 to prevent Google from retrying
      res.status(200).send('OK');
    }
  });

  // Start the scheduled sync
  startScheduledSync();

  return httpServer;
}
