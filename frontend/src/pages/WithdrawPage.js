import React, { useState } from 'react';
import { ArrowUpFromLine, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import { GNOVA } from '@/constants/testIds';

const WithdrawPage = () => {
  const { user, apiCall } = useAuth();
  const [asset, setAsset] = useState('CREDIT');
  const [amount, setAmount] = useState('');
  const [destination, setDestination] = useState('');
  const [destinationType, setDestinationType] = useState('card');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(null);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(null);
    
    if (user?.kyc_status !== 'approved') {
      setError('برای برداشت، احراز هویت (KYC) الزامی است');
      return;
    }
    
    const amountNum = parseInt(amount);
    if (!amountNum || amountNum < 50000) {
      setError('حداقل برداشت 50,000 ریال است');
      return;
    }
    
    if (!destination) {
      setError('لطفاً مقصد برداشت را وارد کنید');
      return;
    }
    
    setLoading(true);
    try {
      const response = await apiCall('POST', '/withdrawals', {
        asset,
        amount_minor: amountNum,
        destination,
        destination_type: destinationType
      });
      setSuccess(response.data);
      setAmount('');
      setDestination('');
    } catch (err) {
      setError(err.response?.data?.detail || 'خطا در ایجاد درخواست برداشت');
    } finally {
      setLoading(false);
    }
  };
  
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
              <ArrowUpFromLine className="w-8 h-8 text-gnova-danger" />
              برداشت از حساب
            </h1>
            <p className="text-gnova-text-secondary mt-2">
              برداشت ریالی یا رمزارز با امنیت بالا
            </p>
          </div>
          
          {/* KYC Warning */}
          {user?.kyc_status !== 'approved' && (
            <div className="bg-gnova-warning/10 border border-gnova-warning/30 rounded-md p-4 mb-6 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-gnova-warning flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-gnova-warning mb-1">احراز هویت نیاز است</h4>
                <p className="text-sm text-gnova-text-secondary">
                  برای انجام برداشت، ابتدا باید فرآیند KYC را تکمیل کنید. به <strong>تنظیمات</strong> بروید.
                </p>
              </div>
            </div>
          )}
          
          {success ? (
            <div className="gnova-card text-center animate-fade-in">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gnova-accent/10 rounded-full mb-4">
                <CheckCircle2 className="w-8 h-8 text-gnova-accent" />
              </div>
              <h2 className="font-heading text-2xl font-bold text-gnova-text-primary mb-2">
                درخواست برداشت ثبت شد
              </h2>
              <p className="text-gnova-text-secondary mb-6">{success.message}</p>
              <div className="space-y-3 text-sm bg-gnova-background rounded-md p-4 mb-6 text-right">
                <div className="flex justify-between"><span className="text-gnova-text-secondary">شناسه</span><code className="font-mono-num">{success.withdrawal_id.substring(0,8)}...</code></div>
                <div className="flex justify-between"><span className="text-gnova-text-secondary">مبلغ</span><span className="font-mono-num font-bold">{success.amount.toLocaleString('fa-IR')} ریال</span></div>
                <div className="flex justify-between"><span className="text-gnova-text-secondary">وضعیت</span><span className="status-badge status-pending">{success.status}</span></div>
                <div className="flex justify-between"><span className="text-gnova-text-secondary">زمان تخمینی</span><span>{success.estimated_completion}</span></div>
              </div>
              <button
                onClick={() => setSuccess(null)}
                className="gnova-button-primary"
              >
                درخواست جدید
              </button>
            </div>
          ) : (
            <div className="gnova-card">
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-gnova-text-primary mb-2">نوع دارایی</label>
                  <select
                    value={asset}
                    onChange={(e) => setAsset(e.target.value)}
                    className="gnova-input"
                    data-testid="gnova-withdraw-asset"
                  >
                    <option value="CREDIT">اعتبار ریالی</option>
                    <option value="USDT">تتر (USDT)</option>
                    <option value="BTC">بیت‌کوین (BTC)</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gnova-text-primary mb-2">مبلغ</label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    data-testid={GNOVA.withdrawAmount}
                    className="gnova-input font-mono-num"
                    placeholder="100000"
                    min="50000"
                  />
                  <p className="text-xs text-gnova-text-secondary mt-2">حداقل: 50,000 ریال • کارمزد: 0.5%</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gnova-text-primary mb-2">نوع مقصد</label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { value: 'card', label: 'شماره کارت' },
                      { value: 'iban', label: 'شبا' },
                      { value: 'crypto_address', label: 'آدرس کیف پول' }
                    ].map(opt => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setDestinationType(opt.value)}
                        className={`px-3 py-2 border rounded-md text-sm transition-all ${
                          destinationType === opt.value
                            ? 'border-gnova-primary bg-gnova-primary/5 text-gnova-primary font-medium'
                            : 'border-gnova-border text-gnova-text-secondary hover:border-gnova-primary/50'
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gnova-text-primary mb-2">مقصد</label>
                  <input
                    type="text"
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    data-testid={GNOVA.withdrawDestination}
                    className="gnova-input font-mono-num"
                    placeholder={
                      destinationType === 'card' ? '6037-9977-1234-5678' :
                      destinationType === 'iban' ? 'IR12-3456-7890-1234-5678' :
                      '0x...'
                    }
                  />
                </div>
                
                {error && (
                  <div className="flex items-start gap-2 p-3 bg-gnova-danger/10 text-gnova-danger rounded-md text-sm">
                    <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                    <span>{error}</span>
                  </div>
                )}
                
                <button
                  type="submit"
                  disabled={loading || user?.kyc_status !== 'approved'}
                  data-testid={GNOVA.withdrawSubmit}
                  className="gnova-button-primary w-full"
                >
                  {loading ? 'در حال ثبت...' : 'ثبت درخواست برداشت'}
                </button>
              </form>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default WithdrawPage;
