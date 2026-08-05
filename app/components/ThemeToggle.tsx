'use client';

import { useTheme } from './ThemeProvider';
import styles from './ThemeToggle.module.css';

export default function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useTheme();
  return (
    <button
      type="button"
      className={className ? `${styles.toggle} ${className}` : styles.toggle}
      onClick={toggle}
      aria-label={`Theme: ${theme}; click to cycle`}
      title={`Theme: ${theme}`}
    >
      {theme === 'dark' && '◐'}
      {theme === 'light' && '☀'}
      {theme === 'high-contrast' && '⚡'}
      <span className={styles.label}>{theme.replace('-', ' ')}</span>
    </button>
  );
}
