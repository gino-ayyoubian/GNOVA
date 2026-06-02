import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Wallet, 
  ArrowDownToLine, 
  ArrowUpFromLine, 
  Repeat, 
  History, 
  BellRing, 
  BarChart3, 
  Settings, 
  LogOut,
  Sparkles,
  Send
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { GNOVA } from '@/constants/testIds';

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  
  const menuItems = [
    { path: '/dashboard', label: 'داشبورد', icon: LayoutDashboard, testId: GNOVA.navDashboard },
    { path: '/wallet', label: 'کیف پول', icon: Wallet, testId: GNOVA.navWallet },
    { path: '/deposit', label: 'واریز', icon: ArrowDownToLine },
    { path: '/withdraw', label: 'برداشت', icon: ArrowUpFromLine },
    { path: '/convert', label: 'تبدیل ارز', icon: Repeat },
    { path: '/history', label: 'تاریخچه', icon: History, testId: GNOVA.navHistory },
    { path: '/analytics', label: 'تحلیل', icon: BarChart3 },
    { path: '/alerts', label: 'هشدارها', icon: BellRing },
    { path: '/settings', label: 'تنظیمات', icon: Settings, testId: GNOVA.navSettings },
  ];
  
  const handleLogout = () => {
    logout();
    navigate('/');
  };
  
  return (
    <aside className="fixed right-0 top-0 h-screen w-64 bg-white border-l border-gnova-border flex flex-col z-40">
      {/* Logo */}
      <Link to="/dashboard" data-testid={GNOVA.navLogo} className="p-6 border-b border-gnova-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gnova-primary rounded-lg flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-heading font-bold text-xl text-gnova-text-primary">GNOVA</h1>
            <p className="text-xs text-gnova-text-secondary">Fintech Platform</p>
          </div>
        </div>
      </Link>
      
      {/* User Info */}
      {user && (
        <div className="p-4 border-b border-gnova-border bg-gnova-background/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gnova-accent/10 rounded-full flex items-center justify-center">
              <span className="text-gnova-accent font-bold text-sm">
                {user.username?.[0]?.toUpperCase() || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gnova-text-primary truncate">
                {user.username || 'کاربر'}
              </p>
              <p className="text-xs text-gnova-text-secondary truncate font-mono-num">
                {user.user_id?.substring(0, 8)}...
              </p>
            </div>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <span className={`status-badge ${user.kyc_status === 'approved' ? 'status-success' : 'status-pending'}`}>
              KYC: {user.kyc_status === 'approved' ? 'تایید شده' : 'در انتظار'}
            </span>
          </div>
        </div>
      )}
      
      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              data-testid={item.testId}
              className={`flex items-center gap-3 px-4 py-3 rounded-md text-sm font-medium transition-all duration-200 ${
                isActive 
                  ? 'bg-gnova-primary text-white' 
                  : 'text-gnova-text-secondary hover:bg-gnova-background hover:text-gnova-text-primary'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      
      {/* Telegram Bot */}
      <div className="p-4 border-t border-gnova-border">
        <a 
          href="https://t.me/KKM_GNOVA_bot" 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center gap-3 px-4 py-3 bg-gnova-accent/10 text-gnova-accent rounded-md text-sm font-medium hover:bg-gnova-accent/20 transition-all"
          data-testid="gnova-telegram-bot-link"
        >
          <Send className="w-5 h-5" />
          <span>بات تلگرام</span>
        </a>
      </div>
      
      {/* Logout */}
      <div className="p-4 border-t border-gnova-border">
        <button 
          onClick={handleLogout}
          data-testid="gnova-logout-btn"
          className="w-full flex items-center gap-3 px-4 py-3 text-gnova-danger hover:bg-gnova-danger/10 rounded-md text-sm font-medium transition-all"
        >
          <LogOut className="w-5 h-5" />
          <span>خروج</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
