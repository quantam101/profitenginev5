import { mkdir, readFile, appendFile } from 'node:fs/promises';
import { dirname } from 'node:path';

const eventFile = process.env.TRAFFIC_EVENTS_FILE ?? '.data/traffic-events.jsonl';

export async function saveTrafficEvent(record: Record<string, string>) {
  await mkdir(dirname(eventFile), { recursive: true });
  await appendFile(eventFile, `${JSON.stringify(record)}\n`, 'utf8');
}

export async function getRecentTrafficEvents(limit = 20) {
  try {
    const text = await readFile(eventFile, 'utf8');
    const lines = text.trim().split('\n').filter(Boolean).slice(-limit);
    return lines
      .map((line) => {
        try {
          return JSON.parse(line) as Record<string, string>;
        } catch {
          return null;
        }
      })
      .filter((event): event is Record<string, string> => event !== null);
  } catch {
    return [];
  }
}
