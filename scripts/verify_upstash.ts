import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

async function main() {
  // Match Django's precedence: explicit environment > .env.local > .env.
  for (const name of ["../.env.local", "../.env"]) {
    const path = resolve(process.cwd(), name.replace("../", ""));
    if (existsSync(path)) process.loadEnvFile(path);
  }

  if (
    !process.env.UPSTASH_REDIS_REST_URL ||
    !process.env.UPSTASH_REDIS_REST_TOKEN
  ) {
    console.error(
      "Upstash credentials are missing; configure the private .env file.",
    );
    process.exit(1);
  }

  const { redis } = await import("../lib/redis.ts");
  const key = `smilemanager:verification:${randomUUID()}`;
  try {
    assert.equal(await redis.ping(), "PONG");
    await redis.set(key, { synthetic: true }, { ex: 60 });
    assert.deepEqual(await redis.get(key), { synthetic: true });
    console.log("PASS: Upstash REST PING and expiring JSON write/read.");
  } catch {
    console.error(
      "Upstash verification failed; credentials and remote errors withheld.",
    );
    process.exitCode = 1;
  } finally {
    await redis.del(key).catch(() => {
      console.error(
        "Temporary key cleanup failed; it expires after 60 seconds.",
      );
      process.exitCode = 1;
    });
  }
}

void main();
