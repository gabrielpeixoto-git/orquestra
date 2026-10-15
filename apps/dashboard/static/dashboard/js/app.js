// Orquestra Dashboard JavaScript

// Theme toggle functionality
function initThemeToggle() {
  const isDark = localStorage.getItem('theme') === 'dark' ||
                 (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);

  const button = document.getElementById('theme-toggle');
  const icon = document.getElementById('theme-icon');
  const text = document.getElementById('theme-text');

  function applyTheme(dark) {
    if (dark) {
      document.documentElement.classList.add('dark');
      if (icon) icon.textContent = '☀️';
      if (text) text.textContent = 'Modo Claro';
    } else {
      document.documentElement.classList.remove('dark');
      if (icon) icon.textContent = '🌙';
      if (text) text.textContent = 'Modo Escuro';
    }
  }

  applyTheme(isDark);

  if (button) {
    button.addEventListener('click', () => {
      const currentDark = document.documentElement.classList.contains('dark');
      const newDark = !currentDark;
      localStorage.setItem('theme', newDark ? 'dark' : 'light');
      applyTheme(newDark);
    });
  }

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
      applyTheme(e.matches);
    }
  });
}

// Global state for Alpine.js
document.addEventListener('alpine:init', () => {
  // Theme toggle component
  Alpine.data('themeToggle', () => ({
    darkMode: localStorage.getItem('theme') === 'dark' ||
               (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches),

    init() {
      this.applyTheme();
      // Listen for system theme changes
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
          this.darkMode = e.matches;
          this.applyTheme();
        }
      });
    },

    toggle() {
      this.darkMode = !this.darkMode;
      localStorage.setItem('theme', this.darkMode ? 'dark' : 'light');
      this.applyTheme();
    },

    applyTheme() {
      if (this.darkMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
  }));

  // Auto-refresh component
  Alpine.data('autoRefresh', (interval = 5000) => ({
    timer: null,
    loading: false,

    init() {
      this.startTimer();
    },

    startTimer() {
      this.timer = setInterval(() => {
        this.refresh();
      }, interval);
    },

    stopTimer() {
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
    },

    async refresh() {
      this.loading = true;
      // Trigger HTMX refresh if present
      const refreshEvent = new CustomEvent('refresh-data');
      window.dispatchEvent(refreshEvent);
      this.loading = false;
    },

    destroy() {
      this.stopTimer();
    }
  }));

  // KPI Card component
  Alpine.data('kpiCard', (value, label, trend = null) => ({
    value,
    label,
    trend,
    trendUp: trend && trend > 0,
    trendDown: trend && trend < 0,
  }));

  // Status filter component
  Alpine.data('statusFilter', (statuses = ['PENDING', 'CONFIRMED', 'CANCELLED', 'FAILED']) => ({
    selectedStatuses: [...statuses],
    isOpen: false,

    toggleStatus(status) {
      if (this.selectedStatuses.includes(status)) {
        this.selectedStatuses = this.selectedStatuses.filter(s => s !== status);
      } else {
        this.selectedStatuses.push(status);
      }
      this.triggerFilter();
    },

    isStatusSelected(status) {
      return this.selectedStatuses.includes(status);
    },

    triggerFilter() {
      const event = new CustomEvent('filter-changed', {
        detail: { statuses: this.selectedStatuses }
      });
      window.dispatchEvent(event);
    }
  }));
});

// Utility functions
function formatCurrency(value) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value);
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleString('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short'
  });
}

function formatRelativeTime(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'agora';
  if (diffMins < 60) return `${diffMins} min atrás`;
  if (diffHours < 24) return `${diffHours}h atrás`;
  if (diffDays < 7) return `${diffDays}d atrás`;
  return formatDate(dateString);
}

// Chart.js configuration
function createChart(ctx, config) {
  return new Chart(ctx, {
    ...config,
    options: {
      ...config.options,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: config.options?.plugins?.legend?.display ?? true,
          labels: {
            color: getComputedStyle(document.documentElement).getPropertyValue('--color-text-primary').trim()
          }
        }
      }
    }
  });
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', () => {
  // Initialize theme toggle
  initThemeToggle();

  // Add smooth scroll behavior
  document.documentElement.style.scrollBehavior = 'smooth';

  // Handle HTMX events
  document.body.addEventListener('htmx:beforeRequest', (evt) => {
    // Show loading state
    evt.target.classList.add('opacity-50');
  });

  document.body.addEventListener('htmx:afterRequest', (evt) => {
    // Remove loading state
    evt.target.classList.remove('opacity-50');
  });

  document.body.addEventListener('htmx:afterSwap', (evt) => {
    // Re-initialize any Alpine components in swapped content
    Alpine.initTree(evt.target);
  });
});
