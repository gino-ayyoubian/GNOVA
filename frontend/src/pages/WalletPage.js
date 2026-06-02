import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Wallet, ArrowDownToLine, ArrowUpFromLine, Repeat, TrendingUp, Eye, EyeOff, RefreshCw } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import { GNOVA } from '@/constants/testIds';

const WalletPage = () => {
  const { apiCall } = useAuth();
  const [balances, setBalances] = useState([]);
  const [totalValue, setTotalValue] = useState(0);
  const [rates, setRates] = useState({});
  const [loading, setLoading] = useState(true);
  const [hideBalance, setHideBalance] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  useEffect(() => {
    fetchData();
  }, []);
  
  const fetchData = async () => {
    try {
      const [walletsRes, ratesRes] = await Promise.all([
        apiCall('GET', '/wallets'),
        apiCall('GET', '/rates')
      ]);
      setBalances(walletsRes.data.balances || []);
      setTotalValue(walletsRes.data.total_value_irr || 0);
      setRates(ratesRes.data.rates || {});
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };
  
  const refresh = async () => {
    setRefreshing(true);
    await fetchData();
  };
  
  const formatNumber = (num, decimals = 0) => {
    if (hideBalance) return '••••••';
    return Number(num).toLocaleString('fa-IR', { maximumFractionDigits: decimals });
  };
  
  const assetIcons = {
    'CREDIT': '💰',
    'IRR': '🇮🇷',
    'USDT': '💵',
    'BTC': '₿'
  };
  
  const assetColors = {
    'CREDIT': '#0B192C',
    'IRR': '#0B192C',
    'USDT': '#26A17B',
    'BTC': '#F7931A'
  };
  
  return (
    <div className="min-h-screen bg-gnova-background">
      <Sidebar />
      <main className="mr-64 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8 animate-fade-in flex items-start justify-between">
            <div>
              <p className="text-overline text-xs uppercase tracking-[0.2em] font-bold text-gnova-text-secondary mb-2">
                دارایی‌ها
              </p>
              <h1 className="font-heading text-3xl font-bold text-gnova-text-primary flex items-center gap-3" style={{ fontFamily: 'Vazirmatn, sans-serif' }}>
                <Wallet className="w-8 h-8 text-gnova-primary" />
                کیف پول من
              </h1>
              <p className="text-gnova-text-secondary mt-2">مدیریت کامل دارایی‌های شما</p>
            </div>
            <button onClick={refresh} disabled={refreshing} className="p-3 hover:bg-white rounded-md transition-colors" data-testid="wallet-refresh">
              <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
          
          {/* Total Balance */}
          <div className="gnova-card bg-gradient-to-br from-gnova-primary to-gnova-primary-hover text-white mb-6 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-64 h-64 bg-gnova-accent/20 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
            <div className="relative z-10 flex items-start justify-between">
              <div>
                <p className="text-sm text-white/70 mb-2">ارزش کل دارایی‌ها (به ریال)</p>
                <div className="flex items-center gap-4">
                  <h2 className="font-mono-num text-4xl lg:text-5xl font-bold">{formatNumber(totalValue)}</h2>
                  <button onClick={() => setHideBalance(!hideBalance)} className="p-2 hover:bg-white/10 rounded-md transition-colors">
                    {hideBalance ? <Eye className="w-5 h-5" /> : <EyeOff className="w-5 h-5" />}
                  </button>
                </div>
                <p className="text-sm text-white/60 mt-1">IRR</p>
              </div>
              <div className="text-left">
                <div className="text-sm text-white/70 mb-2">نرخ‌های لحظه‌ای</div>
                {rates.USDT_IRR && (
                  <div className="text-sm font-mono-num">
                    <div>USDT: <span className="font-bold">{formatNumber(rates.USDT_IRR.rate)} IRR</span></div>
                  </div>
                )}
                {rates.BTC_IRR && (
                  <div className="text-sm font-mono-num mt-1">
                    <div>BTC: <span className="font-bold">{formatNumber(rates.BTC_IRR.rate)} IRR</span></div>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <Link to="/deposit" className="gnova-card gnova-card-hover flex items-center gap-4 p-6 group">
              <div className="w-12 h-12 bg-gnova-success/10 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                <ArrowDownToLine className="w-6 h-6 text-gnova-success" />
              </div>
              <div>
                <h3 className="font-semibold">واریز</h3>
                <p className="text-xs text-gnova-text-secondary">افزایش موجودی</p>
              </div>
            </Link>
            <Link to="/convert" className="gnova-card gnova-card-hover flex items-center gap-4 p-6 group">
              <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                <Repeat className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold">تبدیل</h3>
                <p className="text-xs text-gnova-text-secondary">تعویض ارز</p>
              </div>
            </Link>
            <Link to="/withdraw" className="gnova-card gnova-card-hover flex items-center gap-4 p-6 group">
              <div className="w-12 h-12 bg-gnova-danger/10 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                <ArrowUpFromLine className="w-6 h-6 text-gnova-danger" />
              </div>
              <div>
                <h3 className="font-semibold">برداشت</h3>
                <p className="text-xs text-gnova-text-secondary">انتقال خارجی</p>
              </div>
            </Link>
          </div>
          
          {/* Detailed Assets List */}
          <div className="gnova-card">
            <h3 className="font-heading text-xl font-semibold mb-6">جزئیات دارایی‌ها</h3>
            {loading ? (
              <div className="text-center py-8 text-gnova-text-secondary">در حال بارگیری...</div>
            ) : (
              <div className="space-y-3">
                {balances.map((bal, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 hover:bg-gnova-background rounded-md transition-colors">
                    <div className="flex items-center gap-4">
                      <div 
                        className="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
                        style={{ backgroundColor: `${assetColors[bal.asset_code]}15` }}
                      >
                        <span>{assetIcons[bal.asset_code] || '💎'}</span>
                      </div>
                      <div>
                        <h4 className="font-semibold text-gnova-text-primary">{bal.asset_name}</h4>
                        <p className="text-sm text-gnova-text-secondary">{bal.asset_code}</p>
                      </div>
                    </div>
                    <div className="text-left">
                      <p className="font-mono-num text-xl font-bold text-gnova-text-primary">
                        {formatNumber(bal.balance_display, bal.decimal_precision)}
                      </p>
                      <p className="text-sm text-gnova-text-secondary">{bal.asset_code}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default WalletPage;
