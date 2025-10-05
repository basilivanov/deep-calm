import '@testing-library/jest-dom/vitest';

// jsdom не реализует scrollIntoView, мокируем чтобы избежать ошибок.
Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
  value: () => {},
  writable: true,
});

// Recharts / other components используют ResizeObserver.
class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
window.ResizeObserver = ResizeObserver;
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
global.ResizeObserver = ResizeObserver;
