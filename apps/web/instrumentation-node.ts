/**
 * apps/web/instrumentation-node.ts — Server-side OpenTelemetry setup.
 *
 * Phase 7 (cj-style 91번째 wire) — Observability Stack 강화 territory.
 * PRD §F23.4 + AD-34 (d) sub-decision.
 *
 * **RSC boundary:** SERVER-ONLY (CR 1-1 RSC boundary verbatim). This
 * module is dynamically imported from instrumentation.ts ONLY when
 * `typeof window === 'undefined'` (server runtime). Importing browser
 * OpenTelemetry packages here will crash Node.js.
 *
 * Bootstrap order (matches Phase 4 Sentry conditional init pattern):
 * 1. Read OTEL_SDK_DISABLED env var (default false).
 * 2. If disabled, no-op fallback (mirrors Sentry conditional init).
 * 3. Otherwise, register OpenTelemetry NodeSDK + OTLP HTTP exporter.
 * 4. W3C Trace Context propagator is the default in opentelemetry-api.
 */
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import {
  BatchSpanProcessor,
  TraceIdRatioBasedSampler,
  AlwaysOnSampler,
} from '@opentelemetry/sdk-trace-base';

const OTEL_SDK_DISABLED: boolean =
  process.env.OTEL_SDK_DISABLED === 'true' || false;

if (!OTEL_SDK_DISABLED) {
  const samplerRatio = parseFloat(
    process.env.OTEL_TRACES_SAMPLER_ARG ?? '0.1',
  );
  const sampler =
    samplerRatio >= 1.0
      ? new AlwaysOnSampler()
      : new TraceIdRatioBasedSampler(samplerRatio);

  const sdk = new NodeSDK({
    resource: new Resource({
      'service.name': 'costmgr-web-server',
      'service.version': process.env.APP_VERSION ?? 'phase-7',
    }),
    spanProcessors: [
      new BatchSpanProcessor(
        new OTLPTraceExporter({
          url:
            process.env.OTEL_EXPORTER_OTLP_ENDPOINT ??
            'http://localhost:4318/v1/traces',
        }),
      ),
    ],
    sampler,
  });

  sdk.start();

  // Graceful shutdown — flush spans on process exit.
  const shutdown = async (): Promise<void> => {
    try {
      await sdk.shutdown();
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('instrumentation-node: shutdown error', err);
    }
  };

  process.once('SIGTERM', shutdown);
  process.once('SIGINT', shutdown);
}

export {};
