import '@testing-library/jest-dom/vitest';

// jsdom не реализует scrollIntoView, мокируем чтобы избежать ошибок.
Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
  value: () => {},
  writable: true,
});
