import { cn } from '../../lib/utils';
import type { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'skill' | 'ability' | 'knowledge' | 'task';
  size?: 'sm' | 'md';
  className?: string;
}

export default function Badge({ children, variant = 'default', size = 'md', className }: BadgeProps) {
  const variants = {
    default: 'bg-gray-100 text-gray-700',
    primary: 'bg-primary-100 text-primary-700',
    success: 'bg-green-100 text-green-700',
    warning: 'bg-yellow-100 text-yellow-700',
    danger: 'bg-red-100 text-red-700',
    skill: 'bg-blue-100 text-blue-700',
    ability: 'bg-purple-100 text-purple-700',
    knowledge: 'bg-green-100 text-green-700',
    task: 'bg-orange-100 text-orange-700',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  );
}

export function ElementTypeBadge({ type }: { type: string }) {
  const variantMap: Record<string, BadgeProps['variant']> = {
    Skill: 'skill',
    Ability: 'ability',
    Knowledge: 'knowledge',
    Task: 'task',
  };

  return (
    <Badge variant={variantMap[type] || 'default'} size="sm">
      {type}
    </Badge>
  );
}
