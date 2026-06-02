import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  TrendingUp, 
  TrendingDown,
  Wallet, 
  ArrowDownToLine, 
  ArrowUpFromLine, 
  Repeat, 
  Activity, 
  DollarSign,
  BarChart3,
  Send,
  Eye,
  EyeOff
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import { GNOVA } from '@/constants/testIds';

const Dashboard = () => {
  const { user, apiCall } = useAuth();
  const [balances, setBalances] = useState([]);
  const [totalValue, setTotalValue] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hideBalance, setHideBalance] = useState(false);
  
  useEffect(() => {
    fetchData();
  }, []);
  
  const fetchData = async () => {
    try {
      const [walletsRes, txRes] = await Promise.all([
        apiCall('GET', '/wallets'),
        apiCall('GET', '/transactions?limit=5')
      ]);
      setBalances(walletsRes.data.balances || []);
      setTotalValue(walletsRes.data.total_value_irr || 0);
      setTransactions(txRes.data.transactions || []);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const formatNumber = (num, decimals = 0) => {
    if (hideBalance) return '••••••';
    return Number(num).toLocaleString('fa-IR', { maximumFractionDigits: decimals });
  };
  
  const getAssetColor = (code) => {
    const colors = {
      'CREDIT': '#0B192C',
      'IRR': '#0B192C',
      'USDT': '#26A17B',
      'BTC': '#F7931A'
    };
    return colors[code] || '#64748B';
  };
  
  const quickActions = [
    { icon: ArrowDownToLine, label: 'واریز', path: '/deposit', color: 'bg-gnova-accent/10 text-gnova-accent' },
    { icon: ArrowUpFromLine, label: 'برداشت', path: '/withdraw', color: 'bg-gnova-danger/10 text-gnova-danger' },
    { icon: Repeat, label: 'تبدیل', path: '/convert', color: 'bg-blue-500/10 text-blue-600' },
    { icon: BarChart3, label: 'تحلیل', path: '/analytics', color: 'bg-purple-500/10 text-purple-600' },
  ];
  
  return (
    <div className="min-h-screen bg-gnova-background">
      <Sidebar />
      
      <main className="mr-64 p-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8 animate-fade-in">
            <p className="text-overline text-xs uppercase tracking-[0.2em] font-bold text-gnova-text-secondary mb-2">
              داشبورد
            </p>
            <h1 className="font-heading text-3xl lg:text-4xl font-bold text-gnova-text-primary" style={{ fontFamily: 'Vazirmatn, sans-serif' }}>
              سلام {user?.username || 'کاربر'} 👋
            </h1>
            <p className="text-gnova-text-secondary mt-2">
              مرور سریعی از وضعیت حساب شما
            </p>
          </div>
          
          {/* Total Balance Card */}
          <div className="gnova-card bg-gradient-to-br from-gnova-primary to-gnova-primary-hover text-white mb-6 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-64 h-64 bg-gnova-accent/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
            <div className="relative z-10 flex items-start justify-between">
              <div>
                <p className="text-sm text-white/70 mb-2">کل موجودی (به ریال)</p>
                <div className="flex items-center gap-4">
                  <h2 data-testid={GNOVA.walletTotalValue} className="font-mono-num text-4xl lg:text-5xl font-bold">
                    {formatNumber(totalValue)}
                  </h2>
                  <button 
                    onClick={() => setHideBalance(!hideBalance)}
                    className="p-2 hover:bg-white/10 rounded-md transition-colors"
                    data-testid="gnova-toggle-balance-visibility"
                  >
                    {hideBalance ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                  </button>
                </div>
                <p className="text-sm text-white/60 mt-1">IRR</p>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gnova-accent/20 text-white rounded-full text-sm">
                <TrendingUp className="w-4 h-4" />
                <span className="font-mono-num">+2.4%</span>
              </div>
            </div>
          </div>
          
          {/* Quick Actions */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {quickActions.map((action, idx) => {
              const Icon = action.icon;
              return (
                <Link 
                  key={idx} 
                  to={action.path}
                  data-testid={`gnova-quick-${action.label}`}
                  className="gnova-card gnova-card-hover flex flex-col items-center text-center p-6 group"
                >
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-3 ${action.color} group-hover:scale-110 transition-transform`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="font-medium text-gnova-text-primary">{action.label}</span>
                </Link>
              );
            })}
          </div>
          
          {/* Balances Grid */}
          <div className="mb-8">
            <h3 className="font-heading text-xl font-semibold text-gnova-text-primary mb-4">
              دارایی‌های شما
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="gnova-card animate-pulse h-32 bg-gnova-background"></div>
                ))
              ) : balances.length === 0 ? (
                <div className="col-span-full gnova-card text-center py-12 text-gnova-text-secondary">
                  هنوز دارایی ندارید. برای شروع <Link to="/deposit" className="text-gnova-accent font-medium">واریز کنید</Link>.
                </div>
              ) : (
                balances.map((balance, idx) => (
                  <div 
                    key={idx}
                    data-testid={GNOVA.walletAssetCard}
                    className="gnova-card gnova-card-hover animate-slide-up"
                    style={{ animationDelay: `${idx * 100}ms` }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-8 h-8 rounded-full flex items-center justify-center"
                          style={{ backgroundColor: `${getAssetColor(balance.asset_code)}15` }}
                        >
                          <DollarSign className="w-4 h-4" style={{ color: getAssetColor(balance.asset_code) }} />
                        </div>
                        <span className="text-sm font-semibold text-gnova-text-primary">{balance.asset_code}</span>
                      </div>
                    </div>
                    <p className="text-xs text-gnova-text-secondary mb-1">{balance.asset_name}</p>
                    <p className="font-mono-num text-2xl font-bold text-gnova-text-primary">
                      {formatNumber(balance.balance_display, balance.decimal_precision)}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
          
          {/* Recent Transactions */}
          <div className="gnova-card">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-heading text-xl font-semibold text-gnova-text-primary">
                آخرین تراکنش‌ها
              </h3>
              <Link to="/history" className="text-sm text-gnova-accent hover:text-gnova-accent-hover transition-colors">
                مشاهده همه
              </Link>
            </div>
            
            {transactions.length === 0 ? (
              <div className="text-center py-12 text-gnova-text-secondary">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>هنوز تراکنشی ندارید</p>
              </div>
            ) : (
              <div className="space-y-3">
                {transactions.map((tx, idx) => {
                  const typeMap = {
                    deposit: { label: 'واریز', icon: ArrowDownToLine, color: 'text-gnova-success' },
                    deposit_confirmed: { label: 'واریز', icon: ArrowDownToLine, color: 'text-gnova-success' },
                    withdraw: { label: 'برداشت', icon: ArrowUpFromLine, color: 'text-gnova-danger' },
                    reserve: { label: 'برداشت در انتظار', icon: ArrowUpFromLine, color: 'text-gnova-warning' },
                    conversion_credit: { label: 'تبدیل (دریافت)', icon: Repeat, color: 'text-blue-600' },
                    conversion_debit: { label: 'تبدیل (پرداخت)', icon: Repeat, color: 'text-blue-600' },
                  };
                  
                  const info = typeMap[tx.type] || { label: tx.type, icon: Activity, color: 'text-gnova-text-secondary' };
                  const Icon = info.icon;
                  const statusClass = tx.status === 'settled' ? 'status-success' : 
                                       tx.status === 'processing' ? 'status-pending' : 'status-failed';
                  
                  return (
                    <div 
                      key={idx}
                      className="flex items-center justify-between p-3 hover:bg-gnova-background rounded-md transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gnova-background rounded-full flex items-center justify-center">
                          <Icon className={`w-5 h-5 ${info.color}`} />
                        </div>
                        <div>
                          <p className="font-medium text-gnova-text-primary text-sm">{info.label}</p>
                          <p className="text-xs text-gnova-text-secondary font-mono-num">
                            {new Date(tx.created_at).toLocaleDateString('fa-IR')}
                          </p>
                        </div>
                      </div>
                      <div className="text-left">
                        <p className="font-mono-num font-semibold text-gnova-text-primary">
                          {formatNumber(tx.amount_from_minor)}
                        </p>
                        <span className={`status-badge ${statusClass}`}>
                          {tx.status === 'settled' ? 'تکمیل' : tx.status === 'processing' ? 'در حال انجام' : 'ناموفق'}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
          
          {/* Telegram Bot Promo */}
          <div className="mt-6 gnova-card bg-gradient-to-br from-gnova-accent/5 to-blue-500/5 border-gnova-accent/20">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gnova-accent rounded-lg flex items-center justify-center">
                <Send className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gnova-text-primary">دسترسی سریع از تلگرام</h4>
                <p className="text-sm text-gnova-text-secondary">
                  از بات تلگرام GNOVA برای مدیریت آسان دارایی‌ها استفاده کنید
                </p>
              </div>
              <a 
                href="https://t.me/KKM_GNOVA_bot" 
                target="_blank" 
                rel="noopener noreferrer"
                className="gnova-button-accent text-sm whitespace-nowrap"
              >
                باز کردن بات
              </a>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
