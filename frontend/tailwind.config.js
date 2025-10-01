/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // DeepCalm Brand Colors
        'dc-bg': '#F7F5F2',        // Бежевый фон
        'dc-primary': '#6B4E3D',   // Коричневый основной
        'dc-ink': '#262626',       // Текст
        'dc-accent': '#A67C52',    // Акцентный (кнопки)
        'dc-success': '#10B981',   // Зелёный (успех)
        'dc-warning': '#F59E0B',   // Жёлтый (предупреждение)
        'dc-error': '#EF4444',     // Красный (ошибка)

        // Дополнительные оттенки для UI
        'dc-primary-light': '#8A6B5A',
        'dc-primary-dark': '#4A3529',
        'dc-accent-light': '#C9A07B',
        'dc-bg-secondary': '#FFFFFF',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
