// Calendar Sync Service - Syncs Google Calendar events to PostgreSQL
// Supports both webhooks (real-time) and scheduled sync (backup)

import { db } from './db';
import { calendarEvents } from '@shared/schema';
import { eq, lt, and, sql } from 'drizzle-orm';
import { getUpcomingEvents, EventInfo } from './calendar-service';

// Parse URLs from calendar description
// Expected format in description:
// ---URLS---
// EVENT_PAGE: https://www.annakitney.com/event/phoenixrising/
// CHECKOUT: https://www.annakitneyportal.com/offers/xxx/checkout
// CHECKOUT_6MONTH: https://www.annakitneyportal.com/offers/yyy/checkout
// CHECKOUT_12MONTH: https://www.annakitneyportal.com/offers/zzz/checkout
// PROGRAM_PAGE: https://www.annakitney.com/soulalign-manifestation-mastery/
// ---END_URLS---

interface ParsedUrls {
  eventPageUrl: string | null;
  checkoutUrl: string | null;
  checkoutUrl6Month: string | null;
  checkoutUrl12Month: string | null;
  programPageUrl: string | null;
}

export function parseUrlsFromDescription(description: string): ParsedUrls {
  const result: ParsedUrls = {
    eventPageUrl: null,
    checkoutUrl: null,
    checkoutUrl6Month: null,
    checkoutUrl12Month: null,
    programPageUrl: null
  };

  if (!description) return result;

  // Try to find the URLS section
  const urlsSectionMatch = description.match(/---URLS---[\s\S]*?---END_URLS---/i);
  const searchText = urlsSectionMatch ? urlsSectionMatch[0] : description;

  // Parse each URL type
  const eventPageMatch = searchText.match(/EVENT_PAGE:\s*(https?:\/\/[^\s\n]+)/i);
  if (eventPageMatch) result.eventPageUrl = eventPageMatch[1].trim();

  const checkoutMatch = searchText.match(/(?:^|\n)CHECKOUT:\s*(https?:\/\/[^\s\n]+)/i);
  if (checkoutMatch) result.checkoutUrl = checkoutMatch[1].trim();

  const checkout6Match = searchText.match(/CHECKOUT_6MONTH:\s*(https?:\/\/[^\s\n]+)/i);
  if (checkout6Match) result.checkoutUrl6Month = checkout6Match[1].trim();

  const checkout12Match = searchText.match(/CHECKOUT_12MONTH:\s*(https?:\/\/[^\s\n]+)/i);
  if (checkout12Match) result.checkoutUrl12Month = checkout12Match[1].trim();

  const programMatch = searchText.match(/PROGRAM_PAGE:\s*(https?:\/\/[^\s\n]+)/i);
  if (programMatch) result.programPageUrl = programMatch[1].trim();

  return result;
}

// Clean HTML from description for storage
function cleanDescription(html: string): string {
  if (!html) return '';
  
  // Remove the URLS section from visible description
  let cleaned = html.replace(/---URLS---[\s\S]*?---END_URLS---/gi, '');
  
  // Convert common HTML to readable text
  cleaned = cleaned
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<\/div>/gi, '\n')
    .replace(/<li>/gi, '• ')
    .replace(/<\/li>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\n{3,}/g, '\n\n')
    .trim();
  
  return cleaned;
}

// Sync a single event to the database
// IMPORTANT: Preserves manually set URLs in database if no URL is found in Calendar description
export async function syncEventToDatabase(event: EventInfo): Promise<void> {
  const parsedUrls = parseUrlsFromDescription(event.description);
  const cleanedDescription = cleanDescription(event.description);

  // Check for existing record to preserve manually set URLs
  const existing = await db.select()
    .from(calendarEvents)
    .where(eq(calendarEvents.googleEventId, event.id))
    .limit(1);

  const existingRecord = existing[0];

  // Build event data, preserving existing URLs if no new URL is provided
  const eventData = {
    googleEventId: event.id,
    title: event.title,
    startDate: event.start ? new Date(event.start) : null,
    endDate: event.end ? new Date(event.end) : null,
    timezone: event.startTimeZone || 'UTC',
    location: event.location,
    description: cleanedDescription,
    // Preserve existing URLs if no URL found in Calendar description
    eventPageUrl: parsedUrls.eventPageUrl || existingRecord?.eventPageUrl || event.eventPageUrl || null,
    checkoutUrl: parsedUrls.checkoutUrl || existingRecord?.checkoutUrl || null,
    checkoutUrl6Month: parsedUrls.checkoutUrl6Month || existingRecord?.checkoutUrl6Month || null,
    checkoutUrl12Month: parsedUrls.checkoutUrl12Month || existingRecord?.checkoutUrl12Month || null,
    programPageUrl: parsedUrls.programPageUrl || existingRecord?.programPageUrl || null,
    isActive: true,
    lastSynced: new Date()
  };

  // Upsert: insert or update if exists
  if (existingRecord) {
    await db.update(calendarEvents)
      .set(eventData)
      .where(eq(calendarEvents.googleEventId, event.id));
    console.log(`Updated event: ${event.title} (preserved URLs: ${!parsedUrls.eventPageUrl && existingRecord.eventPageUrl ? 'yes' : 'no'})`);
  } else {
    await db.insert(calendarEvents).values(eventData);
    console.log(`Inserted new event: ${event.title}`);
  }
}

// Full sync - fetch all events from Google Calendar and sync to database
export async function syncAllEvents(): Promise<{ synced: number; errors: number }> {
  console.log('Starting full calendar sync...');
  
  let synced = 0;
  let errors = 0;

  try {
    const events = await getUpcomingEvents(100);
    console.log(`Fetched ${events.length} events from Google Calendar`);

    for (const event of events) {
      try {
        await syncEventToDatabase(event);
        synced++;
      } catch (error) {
        console.error(`Error syncing event ${event.title}:`, error);
        errors++;
      }
    }

    // Mark old events as inactive
    await markPastEventsInactive();

    console.log(`Sync complete: ${synced} synced, ${errors} errors`);
  } catch (error) {
    console.error('Error during sync:', error);
    throw error;
  }

  return { synced, errors };
}

// Mark events with end_date in the past as inactive
async function markPastEventsInactive(): Promise<void> {
  const now = new Date();
  
  await db.update(calendarEvents)
    .set({ isActive: false })
    .where(
      and(
        lt(calendarEvents.endDate, now),
        eq(calendarEvents.isActive, true)
      )
    );
}

// Get all active events from database
export async function getEventsFromDatabase(includeInactive: boolean = false): Promise<typeof calendarEvents.$inferSelect[]> {
  if (includeInactive) {
    return await db.select().from(calendarEvents).orderBy(calendarEvents.startDate);
  }
  
  return await db.select()
    .from(calendarEvents)
    .where(eq(calendarEvents.isActive, true))
    .orderBy(calendarEvents.startDate);
}

// Get event by Google ID from database
export async function getEventFromDatabaseById(googleEventId: string): Promise<typeof calendarEvents.$inferSelect | null> {
  const results = await db.select()
    .from(calendarEvents)
    .where(eq(calendarEvents.googleEventId, googleEventId))
    .limit(1);
  
  return results[0] || null;
}

// Get event by title from database (fuzzy match)
export async function getEventFromDatabaseByTitle(title: string): Promise<typeof calendarEvents.$inferSelect | null> {
  const events = await getEventsFromDatabase();
  const titleLower = title.toLowerCase();
  
  // Exact match first
  let found = events.find(e => e.title.toLowerCase() === titleLower);
  if (found) return found;
  
  // Partial match
  found = events.find(e => 
    e.title.toLowerCase().includes(titleLower) || 
    titleLower.includes(e.title.toLowerCase())
  );
  
  return found || null;
}

// Scheduled sync interval (in milliseconds)
const SYNC_INTERVAL_MS = 30 * 60 * 1000; // 30 minutes

let syncInterval: NodeJS.Timeout | null = null;

// Start scheduled sync
export function startScheduledSync(): void {
  if (syncInterval) {
    console.log('Scheduled sync already running');
    return;
  }

  console.log(`Starting scheduled sync (every ${SYNC_INTERVAL_MS / 60000} minutes)`);
  
  // Initial sync
  syncAllEvents().catch(err => console.error('Initial sync failed:', err));
  
  // Schedule recurring sync
  syncInterval = setInterval(() => {
    syncAllEvents().catch(err => console.error('Scheduled sync failed:', err));
  }, SYNC_INTERVAL_MS);
}

// Stop scheduled sync
export function stopScheduledSync(): void {
  if (syncInterval) {
    clearInterval(syncInterval);
    syncInterval = null;
    console.log('Scheduled sync stopped');
  }
}

// Webhook handler for Google Calendar push notifications
export async function handleCalendarWebhook(
  channelId: string,
  resourceId: string,
  resourceState: string
): Promise<void> {
  console.log(`Calendar webhook received: ${resourceState} (channel: ${channelId})`);

  if (resourceState === 'sync') {
    // Initial sync confirmation - do a full sync
    console.log('Webhook sync confirmation received, performing full sync...');
    await syncAllEvents();
  } else if (resourceState === 'exists') {
    // Calendar changed - do a full sync
    console.log('Calendar changed, syncing...');
    await syncAllEvents();
  }
}

// Note: Setting up webhook watch channel requires the app to be deployed
// and accessible via HTTPS. This is handled in the routes.
