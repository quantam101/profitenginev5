import type { Db, Collection, MongoClient } from 'mongodb';

export function getClient(): Promise<MongoClient>;
export function getDb(): Promise<Db>;
export function getCollection<T = any>(name: string): Promise<Collection<T>>;
export function closeClient(): Promise<void>;
