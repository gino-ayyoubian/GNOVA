import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Sparkles, Send, ArrowLeft, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { GNOVA } from '@/constants/testIds';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [telegramId, setTelegramId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    if (!telegramId || isNaN(parseInt(telegramId))) {
      setError('لطفاً Telegram ID معتبر وارد کنید');
      setLoading(false);
      return;
    }
    
    const result = await login(telegramId);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error || 'خطا در ورود');
    }
    setLoading(false);
  };
  
  return (
    <div className="min-h-screen bg-gnova-background flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Back Link */}
        <Link to="/" className="inline-flex items-center gap-2 text-gnova-text-secondary hover:text-gnova-text-primary mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4 rotate-180" />
          <span>بازگشت به صفحه اصلی</span>
        </Link>
        
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gnova-primary rounded-2xl mb-6">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="font-heading font-bold text-3xl text-gnova-text-primary mb-2">
            ورود به GNOVA
          </h1>
          <p className="text-gnova-text-secondary">
            با Telegram ID خود وارد شوید
          </p>
        </div>
        
        {/* Form */}
        <div className="gnova-card">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gnova-text-primary mb-2">
                Telegram ID
              </label>
              <input
                type="text"
                value={telegramId}
                onChange={(e) => setTelegramId(e.target.value)}
                data-testid={GNOVA.loginTelegramId}
                className="gnova-input font-mono-num"
                placeholder="123456789"
                disabled={loading}
              />
              <p className="text-xs text-gnova-text-secondary mt-2">
                برای دریافت Telegram ID، در تلگرام به @userinfobot پیام دهید
              </p>
            </div>
            
            {error && (
              <div className="flex items-start gap-2 p-3 bg-gnova-danger/10 text-gnova-danger rounded-md text-sm">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}
            
            <button
              type="submit"
              disabled={loading}
              data-testid={GNOVA.loginSubmit}
              className="gnova-button-primary w-full flex items-center justify-center gap-2"
            >
              {loading ? 'در حال ورود...' : 'ورود / ثبت نام'}
            </button>
          </form>
          
          <div className="my-6 flex items-center gap-4">
            <div className="flex-1 h-px bg-gnova-border"></div>
            <span className="text-xs text-gnova-text-secondary">یا</span>
            <div className="flex-1 h-px bg-gnova-border"></div>
          </div>
          
          <a 
            href="https://t.me/KKM_GNOVA_bot" 
            target="_blank" 
            rel="noopener noreferrer"
            className="w-full gnova-button-accent flex items-center justify-center gap-2"
            data-testid="gnova-login-telegram-btn"
          >
            <Send className="w-5 h-5" />
            <span>شروع با تلگرام</span>
          </a>
        </div>
        
        <p className="text-center text-xs text-gnova-text-secondary mt-8">
          با ورود به GNOVA، شما با شرایط استفاده و حریم خصوصی موافقت می‌کنید.
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
