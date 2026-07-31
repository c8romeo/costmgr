/**
 * apps/web/lib/types.ts — Cross-component type re-exports.
 *
 * L2: This file is the **canonical location for product/catalog types**
 * shared between multiple components. The defining module remains
 * `lib/api-client.ts` (the wire types are coupled to the request
 * builder helpers in that file). New cross-component product types
 * (e.g. filters, sort orders) should land here rather than being
 * inline-defined inside a component file.
 *
 * Usage:
 *   import type { ProductType, ProductResponse } from "@/lib/types";
 *
 * Why a barrel instead of moving types: `api-client.ts` carries
 * non-type exports (e.g. `createProduct`, `fetchProducts`) that
 * already live alongside the types. Splitting the types into their
 * own file would either duplicate the imports or require moving the
 * API call helpers — both of which are out of scope for this patch.
 *
 * Existing call sites may continue to import directly from
 * `@/lib/api-client`; this barrel exists for new code and for the
 * components that want a stable, single-purpose import path.
 */

export type {
  ProductType,
  ProductResponse,
  ProductCreateRequest,
  ProductUpdateRequest,
  ProductListResponse,
  ProductListQuery,
} from "./api-client";
