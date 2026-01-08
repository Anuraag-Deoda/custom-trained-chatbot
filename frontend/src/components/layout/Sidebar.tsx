import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Map,
  Briefcase,
  MessageSquare,
  GitCompare,
  TrendingUp,
  Brain,
} from 'lucide-react';
import { cn } from '../../lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Skill Mapper', href: '/skill-mapper', icon: Map },
  { name: 'Jobs', href: '/jobs', icon: Briefcase },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Compare', href: '/compare', icon: GitCompare },
  { name: 'Career Path', href: '/career-path', icon: TrendingUp },
];

interface SidebarProps {
  className?: string;
}

export default function Sidebar({ className }: SidebarProps) {
  return (
    <aside className={cn('w-64 bg-white border-r border-gray-200 flex flex-col', className)}>
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-gray-900">Competency</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors duration-200',
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )
            }
          >
            <item.icon className="w-5 h-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      {/* Bottom Section */}
      <div className="p-4 border-t border-gray-200">
        <div className="bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl p-4 text-white">
          <h4 className="font-semibold mb-1">Pro Tip</h4>
          <p className="text-sm text-white/80">
            Use the Skill Mapper to find your perfect career match!
          </p>
        </div>
      </div>
    </aside>
  );
}
