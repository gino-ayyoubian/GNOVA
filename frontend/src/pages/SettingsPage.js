import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Settings as SettingsIcon, 
  Shield, 
  User, 
  Bell, 
  Globe, 
  Lock,
  CheckCircle2,
  AlertCircle,
  Key,
  Smartphone
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import { GNOVA } from '@/constants/testIds';

const SettingsPage = () => {
  const { user, apiCall, refetch } = useAuth();
  const [activeTab, setActiveTab] = useState('account');
  const [kycSubmission, setKycSubmission] = useState(null);
  const [kycForm, setKycForm] = useState({
    full_name: '',
    national_id: '',
    birth_date: '',
    address: '',
    phone: ''
  });
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  
  useEffect(() => {
    fetchKYCStatus();
  }, []);
  
  const fetchKYCStatus = async () => {
    try {
      const response = await apiCall('GET', '/kyc/status');
      setKycSubmission(response.data.submission);
    } catch (error) {
      console.error('Failed to fetch KYC status:', error);
    }
  };
  
  const submitKYC = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      await apiCall('POST', '/kyc/submit', kycForm);
      setMessage({ type: 'success', text: 'درخواست KYC با موفقیت ارسال شد. در حال بررسی...' });
      await fetchKYCStatus();
      await refetch();
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'خطا در ارسال' });
    } finally {
      setLoading(false);
    }
  };
  
  const autoApproveKYC = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      await apiCall('POST', '/kyc/auto-approve');
      setMessage({ type: 'success', text: 'KYC تایید شد! اکنون می‌توانید برداشت کنید.' });
      await fetchKYCStatus();
      await refetch();
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'خطا' });
    } finally {
      setLoading(false);
    }
  };
  
  const requestOTP = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      const response = await apiCall('POST', '/otp/request', { purpose: 'sensitive_operation' });
      if (response.data.sent_via_telegram) {
        setOtpSent(true);
        setMessage({ type: 'success', text: 'کد به تلگرام شما ارسال شد. لطفاً وارد کنید.' });
      } else {
        setMessage({ type: 'error', text: 'لطفاً ابتدا بات تلگرام GNOVA را start کنید' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'خطا در ارسال کد' });
    } finally {
      setLoading(false);
    }
  };
  
  const verifyOTP = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      await apiCall('POST', '/otp/verify', { code: otpCode, purpose: 'sensitive_operation' });
      setMessage({ type: 'success', text: 'کد تایید شد! تایید دو مرحله‌ای فعال است.' });
      setOtpSent(false);
      setOtpCode('');
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'کد اشتباه است' });
    } finally {
      setLoading(false);
    }
  };
  
  const tabs = [
    { id: 'account', label: 'حساب', icon: User },
    { id: 'kyc', label: 'احراز هویت', icon: Shield },
    { id: 'security', label: 'امنیت', icon: Lock },
    { id: 'notifications', label: 'اعلان‌ها', icon: Bell },
  ];
  
  return (
    <div className="min-h-screen bg-gnova-background">
      <Sidebar />
      <main className="mr-64 p-8">
        <div className="max-w-5xl mx-auto">
          <div className="mb-8 animate-fade-in">
            <p className="text-overline text-xs uppercase tracking-[0.2em] font-bold text-gnova-text-secondary mb-2">
              تنظیمات
            </p>
            <h1 className="font-heading text-3xl font-bold text-gnova-text-primary flex items-center gap-3" style={{ fontFamily: 'Vazirmatn, sans-serif' }}>
              <SettingsIcon className="w-8 h-8 text-gnova-primary" />
              تنظیمات حساب
            </h1>
            <p className="text-gnova-text-secondary mt-2">مدیریت حساب، امنیت و KYC</p>
          </div>
          
          {/* Tabs */}
          <div className="gnova-card mb-6 p-2 flex gap-2 overflow-x-auto">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => { setActiveTab(tab.id); setMessage({ type: '', text: '' }); }}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-all whitespace-nowrap ${
                    activeTab === tab.id 
                      ? 'bg-gnova-primary text-white' 
                      : 'text-gnova-text-secondary hover:bg-gnova-background'
                  }`}
                  data-testid={`settings-tab-${tab.id}`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
          
          {message.text && (
            <div className={`mb-4 p-4 rounded-md flex items-start gap-2 ${
              message.type === 'success' 
                ? 'bg-gnova-success/10 text-gnova-success' 
                : 'bg-gnova-danger/10 text-gnova-danger'
            }`}>
              {message.type === 'success' ? <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" /> : <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />}
              <span>{message.text}</span>
            </div>
          )}
          
          {/* Account Tab */}
          {activeTab === 'account' && (
            <div className="gnova-card animate-fade-in">
              <h2 className="font-heading text-xl font-semibold mb-6">اطلاعات حساب</h2>
              <div className="space-y-4">
                <div className="flex justify-between py-3 border-b border-gnova-border">
                  <span className="text-gnova-text-secondary">شناسه کاربری</span>
                  <code className="font-mono-num text-sm">{user?.user_id?.substring(0, 16)}...</code>
                </div>
                <div className="flex justify-between py-3 border-b border-gnova-border">
                  <span className="text-gnova-text-secondary">نام کاربری</span>
                  <span className="font-medium">{user?.username || '-'}</span>
                </div>
                <div className="flex justify-between py-3 border-b border-gnova-border">
                  <span className="text-gnova-text-secondary">Telegram ID</span>
                  <span className="font-mono-num">{user?.telegram_id || '-'}</span>
                </div>
                <div className="flex justify-between py-3 border-b border-gnova-border">
                  <span className="text-gnova-text-secondary">وضعیت KYC</span>
                  <span className={`status-badge ${user?.kyc_status === 'approved' ? 'status-success' : 'status-pending'}`}>
                    {user?.kyc_status === 'approved' ? 'تایید شده' : user?.kyc_status === 'submitted' ? 'در حال بررسی' : 'در انتظار'}
                  </span>
                </div>
                <div className="flex justify-between py-3 border-b border-gnova-border">
                  <span className="text-gnova-text-secondary">سطح ریسک</span>
                  <span className="font-medium">{user?.risk_level || 'low'}</span>
                </div>
                <div className="flex justify-between py-3">
                  <span className="text-gnova-text-secondary">تاریخ عضویت</span>
                  <span className="font-mono-num text-sm">{user?.created_at ? new Date(user.created_at).toLocaleDateString('fa-IR') : '-'}</span>
                </div>
              </div>
            </div>
          )}
          
          {/* KYC Tab */}
          {activeTab === 'kyc' && (
            <div className="gnova-card animate-fade-in">
              <h2 className="font-heading text-xl font-semibold mb-2">احراز هویت (KYC)</h2>
              <p className="text-gnova-text-secondary mb-6">برای فعال‌سازی برداشت، احراز هویت الزامی است</p>
              
              {user?.kyc_status === 'approved' ? (
                <div className="text-center py-12">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gnova-success/10 rounded-full mb-4">
                    <CheckCircle2 className="w-8 h-8 text-gnova-success" />
                  </div>
                  <h3 className="font-heading text-xl font-semibold text-gnova-success mb-2">
                    KYC تایید شده
                  </h3>
                  <p className="text-gnova-text-secondary">حساب شما کاملاً فعال است</p>
                </div>
              ) : kycSubmission?.status === 'pending' ? (
                <div className="text-center py-8">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gnova-warning/10 rounded-full mb-4">
                    <AlertCircle className="w-8 h-8 text-gnova-warning" />
                  </div>
                  <h3 className="font-heading text-xl font-semibold mb-2">در حال بررسی</h3>
                  <p className="text-gnova-text-secondary mb-6">درخواست شما در حال بررسی است</p>
                  <button onClick={autoApproveKYC} disabled={loading} className="gnova-button-accent" data-testid="kyc-auto-approve">
                    {loading ? 'در حال تایید...' : '🚀 تایید سریع (DEMO)'}
                  </button>
                  <p className="text-xs text-gnova-text-secondary mt-3">
                    در محیط واقعی، بازبینی توسط ادمین انجام می‌شود
                  </p>
                </div>
              ) : (
                <form onSubmit={submitKYC} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">نام و نام خانوادگی</label>
                    <input 
                      type="text" 
                      value={kycForm.full_name}
                      onChange={(e) => setKycForm({...kycForm, full_name: e.target.value})}
                      className="gnova-input"
                      data-testid="kyc-fullname"
                      required
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">کد ملی</label>
                      <input 
                        type="text" 
                        value={kycForm.national_id}
                        onChange={(e) => setKycForm({...kycForm, national_id: e.target.value})}
                        className="gnova-input font-mono-num"
                        data-testid="kyc-national-id"
                        placeholder="0123456789"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">تاریخ تولد</label>
                      <input 
                        type="text" 
                        value={kycForm.birth_date}
                        onChange={(e) => setKycForm({...kycForm, birth_date: e.target.value})}
                        className="gnova-input font-mono-num"
                        data-testid="kyc-birthdate"
                        placeholder="1370/01/01"
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">شماره موبایل</label>
                    <input 
                      type="text" 
                      value={kycForm.phone}
                      onChange={(e) => setKycForm({...kycForm, phone: e.target.value})}
                      className="gnova-input font-mono-num"
                      data-testid="kyc-phone"
                      placeholder="09123456789"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">آدرس</label>
                    <textarea 
                      value={kycForm.address}
                      onChange={(e) => setKycForm({...kycForm, address: e.target.value})}
                      className="gnova-input"
                      data-testid="kyc-address"
                      rows={3}
                      required
                    />
                  </div>
                  <button type="submit" disabled={loading} className="gnova-button-primary w-full" data-testid="kyc-submit">
                    {loading ? 'در حال ارسال...' : 'ارسال درخواست KYC'}
                  </button>
                </form>
              )}
            </div>
          )}
          
          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-4 animate-fade-in">
              <div className="gnova-card">
                <h2 className="font-heading text-xl font-semibold mb-2 flex items-center gap-2">
                  <Smartphone className="w-5 h-5" />
                  تایید دو مرحله‌ای (2FA) از طریق تلگرام
                </h2>
                <p className="text-gnova-text-secondary mb-6">
                  با فعال‌سازی این قابلیت، برای عملیات حساس کد تایید به تلگرام شما ارسال می‌شود
                </p>
                
                {!otpSent ? (
                  <button onClick={requestOTP} disabled={loading} className="gnova-button-primary" data-testid="request-otp">
                    {loading ? 'در حال ارسال...' : 'دریافت کد تست از تلگرام'}
                  </button>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">کد 6 رقمی</label>
                      <input 
                        type="text"
                        value={otpCode}
                        onChange={(e) => setOtpCode(e.target.value)}
                        className="gnova-input font-mono-num text-center text-2xl tracking-widest"
                        placeholder="000000"
                        maxLength={6}
                        data-testid="otp-code"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button onClick={verifyOTP} disabled={loading || otpCode.length !== 6} className="gnova-button-accent flex-1" data-testid="verify-otp">
                        تایید کد
                      </button>
                      <button onClick={() => { setOtpSent(false); setOtpCode(''); }} className="px-4 py-3 border border-gnova-border rounded-md">
                        انصراف
                      </button>
                    </div>
                  </div>
                )}
                
                <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
                  <p className="text-sm text-blue-800">
                    💡 ابتدا باید بات <a href="https://t.me/KKM_GNOVA_bot" target="_blank" rel="noopener noreferrer" className="font-bold underline">@KKM_GNOVA_bot</a> را در تلگرام start کنید.
                  </p>
                </div>
              </div>
              
              <div className="gnova-card">
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <Key className="w-5 h-5" />
                  محدودیت‌های امنیتی
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-gnova-text-secondary">حداکثر برداشت روزانه</span><span className="font-mono-num font-semibold">50,000,000 ریال</span></div>
                  <div className="flex justify-between"><span className="text-gnova-text-secondary">حداکثر تبدیل روزانه</span><span className="font-mono-num font-semibold">نامحدود</span></div>
                </div>
              </div>
            </div>
          )}
          
          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="gnova-card animate-fade-in">
              <h2 className="font-heading text-xl font-semibold mb-6">تنظیمات اعلان</h2>
              <div className="space-y-3">
                {[
                  { label: 'اعلان تراکنش‌ها', desc: 'اطلاع از واریز و برداشت' },
                  { label: 'هشدارهای نرخ', desc: 'تغییرات قیمت رمزارز' },
                  { label: 'اخبار GNOVA', desc: 'به‌روزرسانی‌ها و قابلیت‌های جدید' },
                  { label: 'اعلان امنیتی', desc: 'ورود غیرمعمول و تغییرات حساب' }
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between py-3 border-b border-gnova-border last:border-0">
                    <div>
                      <p className="font-medium text-sm">{item.label}</p>
                      <p className="text-xs text-gnova-text-secondary">{item.desc}</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-5 h-5 accent-gnova-accent" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default SettingsPage;
