// apps/web/mocks/server.ts — MSW setupServer
// Story 0.5 — T4.5 (AC #4)

import { setupServer } from "msw/node";

import { handlers } from "./handlers";

export const server = setupServer(...handlers);
