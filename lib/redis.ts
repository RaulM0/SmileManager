import { Redis } from "@upstash/redis";

// Server-only client. Never import this module into frontend/src.
if (typeof window !== "undefined") {
  throw new Error("The Redis client is only available on the server.");
}

export const redis = Redis.fromEnv();
