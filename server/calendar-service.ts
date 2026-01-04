// Google Calendar Service for Anna Kitney Events
// Uses Replit's Google Calendar integration (connection:conn_google-calendar_01KE458JJP4H7SCZAKZBXQCPAT)

import { google } from 'googleapis';

// Get fresh access token on each request - never cache tokens in module scope
async function getAccessToken(): Promise<string> {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) {
    throw new Error('Calendar service unavailable');
  }

  if (!hostname) {
    throw new Error('Calendar service unavailable');
  }

  const response = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=google-calendar',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  );

  if (!response.ok) {
    throw new Error('Calendar service unavailable');
  }

  const data = await response.json();
  const connectionData = data.items?.[0];
  
  // Extract only the access token, don't store the entire response
  const accessToken = connectionData?.settings?.access_token || 
                      connectionData?.settings?.oauth?.credentials?.access_token;

  if (!accessToken) {
    throw new Error('Google Calendar not connected');
  }
  
  return accessToken;
}

// WARNING: Never cache this client.
// Access tokens expire, so a new client must be created each time.
async function getCalendarClient() {
  const accessToken = await getAccessToken();

  const oauth2Client = new google.auth.OAuth2();
  oauth2Client.setCredentials({
    access_token: accessToken
  });

  return google.calendar({ version: 'v3', auth: oauth2Client });
}

export interface CalendarInfo {
  id: string;
  summary: string;
  description?: string;
  primary?: boolean;
}

export interface EventInfo {
  id: string;
  title: string;
  description: string;
  start: string;
  end: string;
  location: string;
  htmlLink: string;
  slug: string;
  eventPageUrl: string;
  calendarId: string;
}

// Generate URL-friendly slug from event title
function generateSlug(title: string): string {
  return title
    .toLowerCase()
    .replace(/[®™©]/g, '')
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim()
    .replace(/^-|-$/g, '');
}

// List all calendars accessible to the connected account
export async function listCalendars(): Promise<CalendarInfo[]> {
  const calendar = await getCalendarClient();
  
  const response = await calendar.calendarList.list();
  
  return (response.data.items || []).map(cal => ({
    id: cal.id || '',
    summary: cal.summary || '',
    description: cal.description || '',
    primary: cal.primary || false
  }));
}

// Find Anna's calendar by name pattern
export async function findAnnaCalendar(): Promise<CalendarInfo | null> {
  const calendars = await listCalendars();
  
  // Look for calendars containing "Anna" or "Kitney" in the name
  const annaCalendar = calendars.find(cal => 
    cal.summary.toLowerCase().includes('anna') || 
    cal.summary.toLowerCase().includes('kitney') ||
    cal.summary.toLowerCase().includes('events')
  );
  
  return annaCalendar || null;
}

// Fetch events from a specific calendar
export async function getEvents(calendarId: string, maxResults: number = 20): Promise<EventInfo[]> {
  const calendar = await getCalendarClient();
  
  const now = new Date().toISOString();
  
  const response = await calendar.events.list({
    calendarId,
    timeMin: now,
    maxResults,
    singleEvents: true,
    orderBy: 'startTime'
  });
  
  return (response.data.items || []).map(event => {
    const title = event.summary || 'Untitled Event';
    const slug = generateSlug(title);
    
    return {
      id: event.id || '',
      title,
      description: event.description || '',
      start: event.start?.dateTime || event.start?.date || '',
      end: event.end?.dateTime || event.end?.date || '',
      location: event.location || 'Online',
      htmlLink: event.htmlLink || '',
      slug,
      eventPageUrl: `https://www.annakitney.com/event/${slug}/`,
      calendarId
    };
  });
}

// Anna Kitney Coaching calendar ID (synced to user's Google Calendar)
const ANNA_CALENDAR_ID = "cms370prol01ksuq304erj1gmdug1v4m@import.calendar.google.com";

// Get all upcoming events from Anna's calendar
export async function getUpcomingEvents(maxResults: number = 20): Promise<EventInfo[]> {
  try {
    // Fetch directly from Anna's calendar
    const events = await getEvents(ANNA_CALENDAR_ID, maxResults);
    return events;
  } catch (error) {
    console.error("Error fetching Anna's events:", error);
    
    // Fallback: search all calendars excluding holiday calendars
    const calendars = await listCalendars();
    const allEvents: EventInfo[] = [];
    
    for (const cal of calendars) {
      // Skip holiday and primary calendars
      if (cal.id.includes('holiday@group') || cal.primary) continue;
      
      try {
        const events = await getEvents(cal.id, maxResults);
        allEvents.push(...events);
      } catch (error) {
        console.error(`Error fetching events from calendar ${cal.summary}:`, error);
      }
    }
    
    // Sort by start date and limit
    return allEvents
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
      .slice(0, maxResults);
  }
}

// Search events by query
export async function searchEvents(query: string): Promise<EventInfo[]> {
  const events = await getUpcomingEvents(50);
  const queryLower = query.toLowerCase();
  
  return events.filter(event => 
    event.title.toLowerCase().includes(queryLower) ||
    event.description.toLowerCase().includes(queryLower) ||
    event.location.toLowerCase().includes(queryLower)
  );
}

// Get event by title (fuzzy match)
export async function getEventByTitle(title: string): Promise<EventInfo | null> {
  const events = await getUpcomingEvents(50);
  const titleLower = title.toLowerCase();
  
  // Exact match first
  let found = events.find(e => e.title.toLowerCase() === titleLower);
  if (found) return found;
  
  // Partial match
  found = events.find(e => e.title.toLowerCase().includes(titleLower) || titleLower.includes(e.title.toLowerCase()));
  return found || null;
}

// Add event to the connected calendar (for booking functionality)
export async function addEventToCalendar(
  eventDetails: {
    title: string;
    description: string;
    start: string;
    end: string;
    location?: string;
  },
  calendarId: string = 'primary'
): Promise<{ success: boolean; eventLink?: string; error?: string }> {
  try {
    const calendar = await getCalendarClient();
    
    const event = {
      summary: eventDetails.title,
      description: eventDetails.description,
      start: {
        dateTime: eventDetails.start,
        timeZone: 'Australia/Sydney' // Anna Kitney is based in Australia
      },
      end: {
        dateTime: eventDetails.end,
        timeZone: 'Australia/Sydney'
      },
      location: eventDetails.location || 'Online'
    };
    
    const response = await calendar.events.insert({
      calendarId,
      requestBody: event
    });
    
    return {
      success: true,
      eventLink: response.data.htmlLink || undefined
    };
  } catch (error: any) {
    console.error('Error adding event to calendar:', error);
    return {
      success: false,
      error: error.message || 'Failed to add event to calendar'
    };
  }
}

// Format event for chatbot response
export function formatEventForChat(event: EventInfo): string {
  const startDate = new Date(event.start);
  const endDate = new Date(event.end);
  
  const dateOptions: Intl.DateTimeFormatOptions = { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short'
  };
  
  const startFormatted = startDate.toLocaleDateString('en-AU', dateOptions);
  const endFormatted = endDate.toLocaleDateString('en-AU', dateOptions);
  
  let response = `**${event.title}**\n\n`;
  response += `**When:** ${startFormatted}`;
  
  // Check if multi-day event
  if (startDate.toDateString() !== endDate.toDateString()) {
    response += ` to ${endFormatted}`;
  }
  response += '\n\n';
  
  response += `**Where:** ${event.location}\n\n`;
  
  if (event.description) {
    // Truncate long descriptions for chat
    const shortDesc = event.description.length > 500 
      ? event.description.substring(0, 500) + '...' 
      : event.description;
    response += `**About:** ${shortDesc}\n\n`;
  }
  
  return response;
}

// Format multiple events as a list
export function formatEventsListForChat(events: EventInfo[]): string {
  if (events.length === 0) {
    return "I don't see any upcoming events at the moment. Please check back soon or visit the events page for the latest updates!";
  }
  
  let response = "Here are the upcoming events:\n\n";
  
  events.forEach((event, index) => {
    const startDate = new Date(event.start);
    const dateStr = startDate.toLocaleDateString('en-AU', { 
      weekday: 'short',
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
    
    response += `${index + 1}. **${event.title}** - ${dateStr} (${event.location})\n`;
  });
  
  response += "\nWould you like more details about any of these events?";
  
  return response;
}
