import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowDownToLine, CheckCircle2, AlertCircle, CreditCard, Copy } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import { GNOVA } from '@/constants/testIds';

const DepositPage = () => {
  const navigate = useNavigate();
  const { apiCall } = useAuth();
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  
  const quickAmounts = [100000, 500000, 1000000, 5000000, 10000000];
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    
    const amountNum = parseInt(amount);
    if (!amountNum || amountNum < 10000) {
      setError('حداقل مبلغ واریز 10,000 ریال است');
      return;
    }
    
    setLoading(true);
    try {
      const response = await apiCall('POST', '/deposits/initiate', { amount_irr: amountNum });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'خطا در ایجاد درخواست واریز');
    } finally {
      setLoading(false);
    }
  };
  
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };
  
  return (
    <div className="min-h-screen bg-gnova-background">
      <Sidebar />
      <main className="mr-64 p-8">
        <div className="max-w-3xl mx-auto">
          <div className="mb-8 animate-fade-in">
            <p className="text-overline text-xs uppercase tracking-[0.2em] font-bold text-gnova-text-secondary mb-2">
              عملیات مالی
            </p>
            <h1 className="font-heading text-3xl font-bold text-gnova-text-primary flex items-center gap-3">
              <ArrowDownToLine className="w-8 h-8 text-gnova-accent" />
              واریز ریال
            </h1>
            <p className="text-gnova-text-secondary mt-2">
              واریز سریع و امن به حساب GNOVA شما
            </p>
          </div>
          
          {!result ? (
            <div className="gnova-card">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gnova-text-primary mb-2">
                    مبلغ (ریال)
                  </label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    data-testid={GNOVA.depositAmount}
                    className="gnova-input font-mono-num text-lg"
                    placeholder="100,000"
                    min="10000"
                    max="100000000"
                  />
                  <div className="flex justify-between text-xs text-gnova-text-secondary mt-2">
                    <span>حداقل: 10,000 ریال</span>
                    <span>حداکثر: 100,000,000 ریال</span>
                  </div>
                </div>
                
                {/* Quick Amounts */}
                <div>
                  <p className="text-sm font-medium text-gnova-text-primary mb-3">مبالغ پیشنهادی:</p>
                  <div className="flex flex-wrap gap-2">
                    {quickAmounts.map((amt) => (
                      <button
                        key={amt}
                        type="button"
                        onClick={() => setAmount(amt.toString())}
                        className="px-4 py-2 border border-gnova-border rounded-md text-sm font-mono-num hover:border-gnova-primary hover:bg-gnova-primary/5 transition-all"
                        data-testid={`gnova-deposit-quick-${amt}`}
                      >
                        {amt.toLocaleString('fa-IR')}
                      </button>
                    ))}
                  </div>
                </div>
                
                {error && (
                  <div className="flex items-start gap-2 p-3 bg-gnova-danger/10 text-gnova-danger rounded-md text-sm">
                    <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                    <span>{error}</span>
                  </div>
                )}
                
                {/* Info Box */}
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                    <CreditCard className="w-4 h-4" />
                    اطلاعات مهم
                  </h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• واریز معمولاً در کمتر از 5 دقیقه تایید می‌شود</li>
                    <li>• کارمزد واریز: رایگان</li>
                    <li>• مبلغ به اعتبار ریالی (CREDIT) شما اضافه می‌شود</li>
                  </ul>
                </div>
                
                <button
                  type="submit"
                  disabled={loading || !amount}
                  data-testid={GNOVA.depositSubmit}
                  className="gnova-button-primary w-full text-base py-4"
                >
                  {loading ? 'در حال پردازش...' : 'ادامه به درگاه پرداخت'}
                </button>
              </form>
            </div>
          ) : (
            <div className="gnova-card animate-fade-in">
              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gnova-accent/10 rounded-full mb-4">
                  <CheckCircle2 className="w-8 h-8 text-gnova-accent" />
                </div>
                <h2 className="font-heading text-2xl font-bold text-gnova-text-primary mb-2">
                  درخواست واریز ثبت شد
                </h2>
                <p className="text-gnova-text-secondary">
                  شناسه پیگیری: <code className="font-mono-num bg-gnova-background px-2 py-1 rounded">{result.deposit_id.substring(0, 8)}...</code>
                </p>
              </div>
              
              <div className="space-y-4 mb-6">
                <div className="flex justify-between items-center py-3 border-b border-gnova-border">
                  <span className="text-gnova-text-secondary">مبلغ</span>
                  <span className="font-mono-num font-bold text-xl text-gnova-text-primary">
                    {result.amount_irr.toLocaleString('fa-IR')} ریال
                  </span>
                </div>
                <div className="flex justify-between items-center py-3 border-b border-gnova-border">
                  <span className="text-gnova-text-secondary">انقضا</span>
                  <span className="font-mono-num text-sm">
                    {new Date(result.expires_at).toLocaleString('fa-IR')}
                  </span>
                </div>
                <div className="flex justify-between items-center py-3 border-b border-gnova-border">
                  <span className="text-gnova-text-secondary">لینک پرداخت</span>
                  <button 
                    onClick={() => copyToClipboard(result.payment_url)}
                    className="flex items-center gap-1 text-gnova-accent hover:text-gnova-accent-hover text-sm"
                  >
                    <Copy className="w-4 h-4" />
                    کپی
                  </button>
                </div>
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
                <p className="text-sm text-blue-800">
                  {result.instructions || 'برای تکمیل واریز، روی دکمه زیر کلیک کنید'}
                </p>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => navigate('/dashboard')}
                  className="flex-1 px-6 py-3 border border-gnova-border rounded-md text-gnova-text-primary hover:bg-gnova-background transition-colors"
                >
                  بازگشت به داشبورد
                </button>
                <a
                  href={result.payment_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 gnova-button-accent text-center"
                >
                  پرداخت
                </a>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default DepositPage;
