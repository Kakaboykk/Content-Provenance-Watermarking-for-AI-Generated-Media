import { Outlet, Link, useLocation } from 'react-router-dom';
import { ShieldCheck, ImagePlus, Lock, CheckCircle, Clock } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { path: '/', label: 'Dashboard', icon: ShieldCheck },
  { path: '/generate', label: 'Generate', icon: ImagePlus },
  { path: '/protect', label: 'Protect', icon: Lock },
  { path: '/verify', label: 'Verify', icon: CheckCircle },
  { path: '/history', label: 'History', icon: Clock },
];

export default function Layout() {
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-border bg-card/50 backdrop-blur-md hidden md:flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-border">
          <ShieldCheck className="w-8 h-8 text-primary mr-3" />
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-light to-primary">
            Provenance
          </h1>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={clsx(
                  'flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative',
                  isActive
                    ? 'text-white bg-primary/10'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
                )}
              >
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full shadow-[0_0_8px_rgba(99,102,241,0.8)]" />
                )}
                <item.icon
                  className={clsx(
                    'mr-3 h-5 w-5',
                    isActive ? 'text-primary' : 'text-zinc-500 group-hover:text-zinc-300'
                  )}
                />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Mobile Header */}
        <header className="h-16 border-b border-border bg-card/50 backdrop-blur-md flex items-center px-4 md:hidden">
          <ShieldCheck className="w-6 h-6 text-primary mr-2" />
          <h1 className="text-lg font-bold text-white">Provenance</h1>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-4 md:p-8">
          <div className="max-w-6xl mx-auto h-full">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}
