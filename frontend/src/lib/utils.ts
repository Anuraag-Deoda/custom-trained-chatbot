import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num);
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}

export function getScoreColor(score: number): string {
  if (score >= 7) return 'text-green-600';
  if (score >= 4) return 'text-yellow-600';
  return 'text-red-600';
}

export function getScoreBgColor(score: number): string {
  if (score >= 7) return 'bg-green-100';
  if (score >= 4) return 'bg-yellow-100';
  return 'bg-red-100';
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

export function debounce<T extends (...args: Parameters<T>) => void>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export const ELEMENT_TYPE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  Skill: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  Ability: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  Knowledge: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  Task: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
};

export const ELEMENT_TYPE_ICONS: Record<string, string> = {
  Skill: 'Wrench',
  Ability: 'Zap',
  Knowledge: 'BookOpen',
  Task: 'CheckSquare',
};
