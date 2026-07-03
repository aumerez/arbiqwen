// Fail-closed primitives for the browser preview API boundary.
//
// Methods that would mutate state, launch native behavior, start an external
// authorization flow, execute a third-party call, or run an autonomous task
// are not available in a view-only browser preview. Rather than silently
// succeeding, those methods reject with a typed, inspectable error so callers
// (and tests) can tell the operation was deliberately refused.

export const UNSUPPORTED_BROWSER_DEMO_OPERATION = 'UNSUPPORTED_BROWSER_DEMO_OPERATION' as const;

export class UnsupportedBrowserDemoOperationError extends Error {
  readonly code = UNSUPPORTED_BROWSER_DEMO_OPERATION;
  readonly operation: string;

  constructor(operation: string) {
    super(`Operation "${operation}" is not available in the read-only browser preview.`);
    this.name = 'UnsupportedBrowserDemoOperationError';
    this.operation = operation;
  }
}

/**
 * Build a method that always rejects with {@link UnsupportedBrowserDemoOperationError}.
 * The returned function accepts (and ignores) any arguments so it can stand in
 * for methods of differing arity. It performs no side effects: no network, no
 * native call, no storage, no mutation.
 */
export function unsupported(operation: string): (...args: unknown[]) => Promise<never> {
  return () => Promise.reject(new UnsupportedBrowserDemoOperationError(operation));
}

/** A listener registration that does nothing and returns a no-op unsubscribe. */
export function noopSubscribe(): () => void {
  return () => {};
}
