import { sql } from "drizzle-orm";
import { pgTable, text, varchar, serial, timestamp, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

// Calendar Events table for storing synced Google Calendar events
export const calendarEvents = pgTable("calendar_events", {
  id: serial("id").primaryKey(),
  googleEventId: varchar("google_event_id", { length: 255 }).notNull().unique(),
  title: varchar("title", { length: 500 }).notNull(),
  startDate: timestamp("start_date", { withTimezone: true }),
  endDate: timestamp("end_date", { withTimezone: true }),
  timezone: varchar("timezone", { length: 100 }),
  location: text("location"),
  description: text("description"),
  
  // URLs parsed from calendar description (added by Anna's team)
  eventPageUrl: varchar("event_page_url", { length: 500 }),
  checkoutUrl: varchar("checkout_url", { length: 500 }),
  checkoutUrl6Month: varchar("checkout_url_6month", { length: 500 }),
  checkoutUrl12Month: varchar("checkout_url_12month", { length: 500 }),
  programPageUrl: varchar("program_page_url", { length: 500 }),
  
  // Status tracking
  isActive: boolean("is_active").default(true),
  isRecurring: boolean("is_recurring").default(false),
  lastSynced: timestamp("last_synced").default(sql`NOW()`),
  createdAt: timestamp("created_at").default(sql`NOW()`),
});

export const insertCalendarEventSchema = createInsertSchema(calendarEvents).omit({
  id: true,
  createdAt: true,
});

export type InsertCalendarEvent = z.infer<typeof insertCalendarEventSchema>;
export type CalendarEvent = typeof calendarEvents.$inferSelect;
