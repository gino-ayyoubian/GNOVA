import React, { useState, useEffect } from 'react';
import { Repeat, ArrowDown, AlertCircle, Lock, RefreshCw } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import { GNOVA } from '@/constants/testIds';

const ConvertPage = () => {
  const { apiCall } = useAuth();
  const [fromAsset, setFromAsset] = useState('IRR');
  const [toAsset, setToAsset] = useState('USDT');
  const [amount, setAmount] = useState('');
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [timeLeft, setTimeLeft] = useState(0);
  
  const assets = [
    { code: 'IRR', name: 'ریال', color: '#0B192C', precision: 0 },
    { code: 'CREDIT', name: 'اعتبار ریالی', color: '#0B192C', precision: 0 },
    { code: 'USDT', name: 'تتر', color: '#26A17B', precision: 6 },
    { code: 'BTC', name: 'بیت‌کوین', color: '#F7931A', precision: 8 },
  ];
  
  useEffect(() => {
    if (quote && quote.expires_at) {
      const interval = setInterval(() => {
        const remaining = Math.max(0, Math.floor((new Date(quote.expires_at) - new Date()) / 1000));
        setTimeLeft(remaining);
        if (remaining === 0) {
          setQuote(null);
          clearInterval(interval);
        }
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [quote]);
  
  const getQuote = async () => {
    setError('');
    setSuccess('');
    if (!amount || parseFloat(amount) <= 0) {
      setError('لطفاً مبلغ معتبر وارد کنید');
      return;
    }
    
    setLoading(true);
    try {
      const fromInfo = assets.find(a => a.code === fromAsset);
      const amountMinor = Math.floor(parseFloat(amount) * Math.pow(10, fromInfo.precision));
      
      const response = await apiCall('POST', '/convert/quote', {
        from_asset: fromAsset,
        to_asset: toAsset,
        amount_minor: amountMinor
      });
      setQuote(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'خطا در دریافت نرخ');
    } finally {
      setLoading(false);
    }
  };
  
  const confirmConversion = async () => {
    if (!quote) return;
    setLoading(true);
    setError('');
    try {
      await apiCall('POST', '/conversions/confirm', { quote_id: quote.quote_id });
      setSuccess('تبدیل با موفقیت انجام شد!');
      setQuote(null);
      setAmount('');
    } catch (err) {
      setError(err.response?.data?.detail || 'خطا در انجام تبدیل');
    } finally {
      setLoading(false);
    }
  };
  
  const swapAssets = () => {
    const temp = fromAsset;
    setFromAsset(toAsset);
    setToAsset(temp);
    setQuote(null);
  };
  
  const formatAmount = (amount, precision) => {
    if (!amount) return '0';
    return (amount / Math.pow(10, precision)).toLocaleString('fa-IR', { maximumFractionDigits: precision });
  };
  
  const toAssetInfo = assets.find(a => a.code === toAsset);
  
  return (
    <div className="min-h-screen bg-gnova-background">
      <Sidebar />
      <main className="mr-64 p-8">
        <div className="max-w-2xl mx-auto">
          <div className="mb-8 animate-fade-in">
            <p className="text-overline text-xs uppercase tracking-[0.2em] font-bold text-gnova-text-secondary mb-2">
              عملیات مالی
            </p>
            <h1 className="font-heading text-3xl font-bold text-gnova-text-primary flex items-center gap-3">
              <Repeat className="w-8 h-8 text-blue-600" />
              تبدیل دارایی
            </h1>
            <p className="text-gnova-text-secondary mt-2">
              تبدیل ارز و رمزارز با نرخ قفل‌شده
            </p>
          </div>
          
          <div className="gnova-card">
            {/* From */}
            <div className="mb-2">
              <label className="block text-sm font-medium text-gnova-text-secondary mb-2">از</label>
              <div className="bg-gnova-background rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <select
                    value={fromAsset}
                    onChange={(e) => { setFromAsset(e.target.value); setQuote(null); }}
                    data-testid={GNOVA.convertFrom}
                    className="bg-transparent font-bold text-gnova-text-primary focus:outline-none cursor-pointer"
                  >
                    {assets.filter(a => a.code !== toAsset).map(a => (
                      <option key={a.code} value={a.code}>{a.name} ({a.code})</option>
                    ))}
                  </select>
                </div>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => { setAmount(e.target.value); setQuote(null); }}
                  data-testid={GNOVA.convertAmount}
                  className="w-full bg-transparent text-2xl font-mono-num font-bold focus:outline-none"
                  placeholder="0.00"
                  step="any"
                />
              </div>
            </div>
            
            {/* Swap Button */}
            <div className="flex justify-center my-3">
              <button
                onClick={swapAssets}
                className="w-10 h-10 bg-white border border-gnova-border rounded-full flex items-center justify-center hover:border-gnova-primary hover:bg-gnova-primary/5 transition-all"
                data-testid="gnova-swap-assets"
              >
                <ArrowDown className="w-5 h-5 text-gnova-text-secondary" />
              </button>
            </div>
            
            {/* To */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gnova-text-secondary mb-2">به</label>
              <div className="bg-gnova-background rounded-lg p-4">
                <select
                  value={toAsset}
                  onChange={(e) => { setToAsset(e.target.value); setQuote(null); }}
                  data-testid={GNOVA.convertTo}
                  className="bg-transparent font-bold text-gnova-text-primary focus:outline-none cursor-pointer mb-2"
                >
                  {assets.filter(a => a.code !== fromAsset).map(a => (
                    <option key={a.code} value={a.code}>{a.name} ({a.code})</option>
                  ))}
                </select>
                <div className="text-2xl font-mono-num font-bold text-gnova-text-primary">
                  {quote ? formatAmount(quote.amount_to, toAssetInfo.precision) : '0.00'}
                </div>
              </div>
            </div>
            
            {/* Quote Info */}
            {quote && (
              <div className="bg-gnova-accent/5 border border-gnova-accent/20 rounded-lg p-4 mb-6 animate-fade-in">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2 text-sm font-medium text-gnova-accent">
                    <Lock className="w-4 h-4" />
                    نرخ قفل شد
                  </div>
                  <div className="font-mono-num text-sm text-gnova-warning">
                    {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
                  </div>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gnova-text-secondary">نرخ تبدیل</span>
                    <span className="font-mono-num">{quote.rate.toLocaleString('fa-IR', { maximumFractionDigits: 8 })}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gnova-text-secondary">کارمزد</span>
                    <span className="font-mono-num">{(quote.fee || 0).toLocaleString('fa-IR')}</span>
                  </div>
                </div>
              </div>
            )}
            
            {error && (
              <div className="flex items-start gap-2 p-3 bg-gnova-danger/10 text-gnova-danger rounded-md text-sm mb-4">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}
            
            {success && (
              <div className="flex items-start gap-2 p-3 bg-gnova-success/10 text-gnova-success rounded-md text-sm mb-4">
                <span>{success}</span>
              </div>
            )}
            
            {!quote ? (
              <button
                onClick={getQuote}
                disabled={loading || !amount}
                data-testid={GNOVA.convertQuote}
                className="gnova-button-primary w-full flex items-center justify-center gap-2"
              >
                {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : null}
                {loading ? 'در حال محاسبه...' : 'دریافت نرخ'}
              </button>
            ) : (
              <button
                onClick={confirmConversion}
                disabled={loading || timeLeft === 0}
                data-testid={GNOVA.convertConfirm}
                className="gnova-button-accent w-full"
              >
                {loading ? 'در حال انجام...' : 'تایید تبدیل'}
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default ConvertPage;
