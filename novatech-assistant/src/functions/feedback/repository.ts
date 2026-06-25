// Feedback persistence boundary — Cenário 3, Ex. 3.2.
//
// The Copilot draft built the Cosmos client INSIDE the handler via a dynamic
// `require('@azure/cosmos')`, which (a) violates AGENTS.md (static imports only)
// and (b) makes the handler impossible to unit-test without a live Cosmos.
// Here the SDK is a static import, behind an interface, with a test seam.

import { CosmosClient, type Container } from "@azure/cosmos";
import { config } from "../../shared/config.js";
import type { FeedbackRecord } from "../../shared/types.js";

export interface FeedbackRepository {
  save(record: FeedbackRecord): Promise<void>;
}

class CosmosFeedbackRepository implements FeedbackRepository {
  private readonly container: Container;

  constructor() {
    const client = new CosmosClient(config.COSMOS_CONNECTION_STRING);
    this.container = client
      .database(config.COSMOS_DATABASE)
      .container(config.COSMOS_FEEDBACK_CONTAINER);
  }

  async save(record: FeedbackRecord): Promise<void> {
    await this.container.items.create(record);
  }
}

let instance: FeedbackRepository | undefined;

/** Default repository (composition root for production). Constructed lazily. */
export function getFeedbackRepository(): FeedbackRepository {
  instance ??= new CosmosFeedbackRepository();
  return instance;
}

/** Test seam: inject a fake repository so the handler is testable without Cosmos. */
export function setFeedbackRepository(repo: FeedbackRepository): void {
  instance = repo;
}
