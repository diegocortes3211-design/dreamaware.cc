import { z } from "zod";

// ---- Client → Server
export const Hello = z.object({
  type: z.literal("hello"),
  streamId: z.string(),
  wantWindow: z.number().int().min(1).max(65536),
  resume: z.object({
    lastApplied: z.number().int().nonnegative()
  }).optional()
});
export type Hello = z.infer<typeof Hello>;

export const Credit = z.object({
  type: z.literal("credit"),
  n: z.number().int().min(1).max(65536),
  lastApplied: z.number().int().nonnegative()
});
export type Credit = z.infer<typeof Credit>;

export const Pong = z.object({
  type: z.literal("pong"),
  t: z.number().int()
});
export type Pong = z.infer<typeof Pong>;

export const ClientMsg = z.discriminatedUnion("type", [Hello, Credit, Pong]);
export type ClientMsg = z.infer<typeof ClientMsg>;

// ---- Server → Client
export const Welcome = z.object({
  type: z.literal("welcome"),
  streamId: z.string(),
  maxWindow: z.number().int(),
  features: z.array(z.string())
});
export type Welcome = z.infer<typeof Welcome>;

export const Delta = z.object({
  type: z.literal("delta"),
  tickId: z.number().int().positive(),
  payload: z.object({
    count: z.number().int().nonnegative()
  })
});
export type Delta = z.infer<typeof Delta>;

export const Snapshot = z.object({
  type: z.literal("snapshot"),
  tickId: z.number().int().positive(),
  state: z.object({
    count: z.number().int().nonnegative()
  })
});
export type Snapshot = z.infer<typeof Snapshot>;

export const PleaseAck = z.object({
  type: z.literal("pleaseAck")
});
export type PleaseAck = z.infer<typeof PleaseAck>;

export const Ping = z.object({
  type: z.literal("ping"),
  t: z.number().int()
});
export type Ping = z.infer<typeof Ping>;

export const Bye = z.object({
  type: z.literal("bye"),
  reason: z.string()
});
export type Bye = z.infer<typeof Bye>;

export const ServerMsg = z.discriminatedUnion("type", [
  Welcome,
  Delta,
  Snapshot,
  PleaseAck,
  Ping,
  Bye
]);
export type ServerMsg = z.infer<typeof ServerMsg>;