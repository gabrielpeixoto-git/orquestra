# Design System - Orquestra Control Center

## Overview

Design system para o dashboard web do Orquestra, focado em observabilidade e controle de sagas distribuídas.

## Tech Stack

- **CSS Framework**: Tailwind CSS (via django-tailwind-cli)
- **Interactive**: HTMX 2.x + Alpine.js 3
- **Charts**: Chart.js 4
- **Icons**: Heroicons (SVG inline)
- **Dark Mode**: Sistema base (prefers-color-scheme)

## Color Palette

### Primary Colors

```css
/* Light Mode */
--color-primary-50: #eff6ff;
--color-primary-100: #dbeafe;
--color-primary-200: #bfdbfe;
--color-primary-300: #93c5fd;
--color-primary-400: #60a5fa;
--color-primary-500: #3b82f6;
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;
--color-primary-800: #1e40af;
--color-primary-900: #1e3a8a;

/* Dark Mode */
--color-primary-50: #0c1929;
--color-primary-100: #0f2a4a;
--color-primary-200: #153a66;
--color-primary-300: #1b4a83;
--color-primary-400: #215a9f;
--color-primary-500: #2563eb;
--color-primary-600: #3b82f6;
--color-primary-700: #60a5fa;
--color-primary-800: #93c5fd;
--color-primary-900: #bfdbfe;
```

### Status Colors

```css
/* Order Status */
--status-pending: #f59e0b;    /* amber-500 */
--status-confirmed: #10b981;  /* emerald-500 */
--status-cancelled: #ef4444;  /* red-500 */
--status-failed: #ef4444;     /* red-500 */

/* Stock Reservation */
--reservation-active: #3b82f6; /* blue-500 */
--reservation-released: #6b7280; /* gray-500 */
--reservation-confirmed: #10b981; /* emerald-500 */

/* Payment */
--payment-success: #10b981;    /* emerald-500 */
--payment-failed: #ef4444;    /* red-500 */
--payment-pending: #f59e0b;    /* amber-500 */
```

### Semantic Colors

```css
/* Light Mode */
--color-bg-primary: #ffffff;
--color-bg-secondary: #f3f4f6;
--color-bg-tertiary: #e5e7eb;
--color-text-primary: #111827;
--color-text-secondary: #6b7280;
--color-border: #e5e7eb;
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
--color-info: #3b82f6;

/* Dark Mode */
--color-bg-primary: #0f172a;
--color-bg-secondary: #1e293b;
--color-bg-tertiary: #334155;
--color-text-primary: #f9fafb;
--color-text-secondary: #9ca3af;
--color-border: #334155;
--color-success: #34d399;
--color-warning: #fbbf24;
--color-error: #f87171;
--color-info: #60a5fa;
```

## Typography

### Font Scale

```css
--font-family-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
--font-family-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;

--text-xs: 0.75rem;   /* 12px */
--text-sm: 0.875rem;  /* 14px */
--text-base: 1rem;    /* 16px */
--text-lg: 1.125rem;  /* 18px */
--text-xl: 1.25rem;   /* 20px */
--text-2xl: 1.5rem;   /* 24px */
--text-3xl: 1.875rem; /* 30px */
--text-4xl: 2.25rem;  /* 36px */
```

### Font Weights

```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

## Spacing

```css
--spacing-1: 0.25rem;  /* 4px */
--spacing-2: 0.5rem;   /* 8px */
--spacing-3: 0.75rem;  /* 12px */
--spacing-4: 1rem;     /* 16px */
--spacing-5: 1.25rem;  /* 20px */
--spacing-6: 1.5rem;   /* 24px */
--spacing-8: 2rem;     /* 32px */
--spacing-10: 2.5rem; /* 40px */
--spacing-12: 3rem;   /* 48px */
--spacing-16: 4rem;   /* 64px */
```

## Border Radius

```css
--radius-sm: 0.25rem;  /* 4px */
--radius-md: 0.375rem; /* 6px */
--radius-lg: 0.5rem;   /* 8px */
--radius-xl: 0.75rem;  /* 12px */
--radius-2xl: 1rem;    /* 16px */
--radius-full: 9999px;
```

## Shadows

```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
```

## Components

### Button

```html
<!-- Primary -->
<button class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
  Action
</button>

<!-- Secondary -->
<button class="px-4 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 transition-colors dark:bg-gray-700 dark:text-white dark:hover:bg-gray-600">
  Cancel
</button>

<!-- Danger -->
<button class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
  Delete
</button>
```

### Card

```html
<div class="bg-white rounded-lg shadow-md p-6 dark:bg-gray-800">
  <h3 class="text-lg font-semibold mb-2">Card Title</h3>
  <p class="text-gray-600 dark:text-gray-400">Card content</p>
</div>
```

### Badge

```html
<!-- Status Badge -->
<span class="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
  PENDING
</span>

<!-- Info Badge -->
<span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
  INFO
</span>
```

### Table

```html
<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
  <thead class="bg-gray-50 dark:bg-gray-800">
    <tr>
      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400">
        Header
      </th>
    </tr>
  </thead>
  <tbody class="bg-white divide-y divide-gray-200 dark:bg-gray-900 dark:divide-gray-700">
    <tr>
      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
        Data
      </td>
    </tr>
  </tbody>
</table>
```

### Timeline

```html
<div class="relative">
  <div class="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700"></div>
  <div class="relative pl-10 pb-8">
    <div class="absolute left-2 w-4 h-4 rounded-full bg-primary-500"></div>
    <div class="text-sm font-medium">Event Title</div>
    <div class="text-xs text-gray-500 dark:text-gray-400">Timestamp</div>
  </div>
</div>
```

## Layout

### Container

```html
<div class="container mx-auto px-4 sm:px-6 lg:px-8">
  <!-- Content -->
</div>
```

### Grid

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <!-- Cards -->
</div>
```

### Sidebar Layout

```html
<div class="flex h-screen bg-gray-100 dark:bg-gray-900">
  <!-- Sidebar -->
  <aside class="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
    <!-- Navigation -->
  </aside>

  <!-- Main Content -->
  <main class="flex-1 overflow-y-auto">
    <!-- Content -->
  </main>
</div>
```

## Responsive Breakpoints

```css
--breakpoint-sm: 640px;
--breakpoint-md: 768px;
--breakpoint-lg: 1024px;
--breakpoint-xl: 1280px;
--breakpoint-2xl: 1536px;
```

## Animation

```css
/* Fade In */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide In */
@keyframes slideIn {
  from { transform: translateY(-10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Pulse */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

## Accessibility

- Contrast ratio ≥ 4.5:1 for normal text
- Contrast ratio ≥ 3:1 for large text
- Focus visible on all interactive elements
- Keyboard navigation support
- ARIA labels for screen readers
