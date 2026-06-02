import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Activity, Calendar, ArrowDownToLine, ArrowUpFromLine, Repeat } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';

const AnalyticsPage = () => {
  const { apiCall } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchAnalytics();
  }, []);
  
  const fetchAnalytics = async () => {
    try {
      const response = await apiCall('GET', '/analytics/summary');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const formatNumber = (num) => Number(num || 0).toLocaleString('fa-IR');
  
  const typeLabels = {
    'deposit': 'واریز',
    'deposit_confirmed': 'واریز',
    'deposit_zarinpal': 'واریز ZarinPal',
    'withdraw': 'برداشت',
    'reserve': 'برداشت در انتظار',
    'conversion_credit': 'تبدیل (دریافت)',
    'conversion_debit': 'تبدیل (پرداخت)',
    'reserve': 'رزرو',
  };
  
  const typeColors = {
    'deposit': 'bg-gnova-success/10 text-gnova-success',
    'deposit_confirmed': 'bg-gnova-success/10 text-gnova-success',
    'deposit_zarinpal': 'bg-gnova-success/10 text-gnova-success',
    'withdraw': 'bg-gnova-danger/10 text-gnova-danger',
    'reserve': 'bg-gnova-warning/10 text-gnova-warning',
    'conversion_credit': 'bg-blue-100 text-blue-700',
    'conversion_debit': 'bg-blue-100 text-blue-700',
  };
  
  const maxDaily = analytics?.daily_last_30_days?.length ? 
    Math.max(...analytics.daily_last_30_days.map(d => d.total || 0), 1) : 1;
  
  return (
    <div className="min-h-screen bg-gnova-background">
      <Sidebar />
      <main className="mr-64 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8 animate-fade-in">
            <p className="text-overline text-xs uppercase tracking-[0.2em] font-bold text-gnova-text-secondary mb-2">
              تحلیل
            </p>
            <h1 className="font-heading text-3xl font-bold text-gnova-text-primary flex items-center gap-3" style={{ fontFamily: 'Vazirmatn, sans-serif' }}>
              <BarChart3 className="w-8 h-8 text-gnova-primary" />
              تحلیل خرج‌کرد
            </h1>
            <p className="text-gnova-text-secondary mt-2">بینش‌های هوشمند از وضعیت مالی شما</p>
          </div>
          
          {loading ? (
            <div className="gnova-card text-center py-12 text-gnova-text-secondary">در حال محاسبه...</div>
          ) : (
            <>
              {/* This Month Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="gnova-card">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-gnova-success/10 rounded-lg flex items-center justify-center">
                      <ArrowDownToLine className="w-5 h-5 text-gnova-success" />
                    </div>
                    <span className="text-sm text-gnova-text-secondary">واریز این ماه</span>
                  </div>
                  <p className="font-mono-num text-2xl font-bold text-gnova-text-primary">
                    {formatNumber(analytics?.this_month?.total_deposits)}
                  </p>
                  <p className="text-xs text-gnova-text-secondary mt-1">IRR</p>
                </div>
                
                <div className="gnova-card">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-gnova-danger/10 rounded-lg flex items-center justify-center">
                      <ArrowUpFromLine className="w-5 h-5 text-gnova-danger" />
                    </div>
                    <span className="text-sm text-gnova-text-secondary">برداشت این ماه</span>
                  </div>
                  <p className="font-mono-num text-2xl font-bold text-gnova-text-primary">
                    {formatNumber(analytics?.this_month?.total_withdrawals)}
                  </p>
                  <p className="text-xs text-gnova-text-secondary mt-1">IRR</p>
                </div>
                
                <div className="gnova-card">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
                      <Activity className="w-5 h-5 text-blue-600" />
                    </div>
                    <span className="text-sm text-gnova-text-secondary">تعداد تراکنش‌ها</span>
                  </div>
                  <p className="font-mono-num text-2xl font-bold text-gnova-text-primary">
                    {formatNumber(analytics?.this_month?.total_transactions)}
                  </p>
                  <p className="text-xs text-gnova-text-secondary mt-1">عدد</p>
                </div>
              </div>
              
              {/* Net Flow */}
              <div className="gnova-card mb-6">
                <h3 className="font-heading font-semibold mb-3">جریان نقدی خالص</h3>
                <div className="flex items-baseline gap-3">
                  <span className={`font-mono-num text-3xl font-bold ${
                    (analytics?.this_month?.net_flow || 0) >= 0 ? 'text-gnova-success' : 'text-gnova-danger'
                  }`}>
                    {(analytics?.this_month?.net_flow || 0) >= 0 ? '+' : ''}{formatNumber(analytics?.this_month?.net_flow)}
                  </span>
                  <span className="text-gnova-text-secondary">IRR</span>
                  {(analytics?.this_month?.net_flow || 0) >= 0 ? (
                    <TrendingUp className="w-5 h-5 text-gnova-success" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-gnova-danger" />
                  )}
                </div>
                <p className="text-sm text-gnova-text-secondary mt-2">
                  واریز منهای برداشت در این ماه
                </p>
              </div>
              
              {/* Transactions by Type */}
              <div className="gnova-card mb-6">
                <h3 className="font-heading font-semibold mb-4">تراکنش‌ها بر اساس نوع</h3>
                {analytics?.by_type?.length ? (
                  <div className="space-y-3">
                    {analytics.by_type.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 hover:bg-gnova-background rounded-md transition-colors">
                        <div className="flex items-center gap-3">
                          <span className={`status-badge ${typeColors[item.type] || 'bg-gnova-background text-gnova-text-secondary'}`}>
                            {typeLabels[item.type] || item.type}
                          </span>
                          <span className="text-sm text-gnova-text-secondary">{item.count} عدد</span>
                        </div>
                        <span className="font-mono-num font-semibold">
                          {formatNumber(item.total)} IRR
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gnova-text-secondary text-sm text-center py-4">هنوز تراکنشی ندارید</p>
                )}
              </div>
              
              {/* Daily Chart */}
              {analytics?.daily_last_30_days?.length > 0 && (
                <div className="gnova-card">
                  <h3 className="font-heading font-semibold mb-4 flex items-center gap-2">
                    <Calendar className="w-5 h-5" />
                    فعالیت 30 روز اخیر
                  </h3>
                  <div className="space-y-2">
                    {analytics.daily_last_30_days.slice(0, 15).map((day, idx) => {
                      const widthPercent = ((day.total || 0) / maxDaily) * 100;
                      return (
                        <div key={idx} className="flex items-center gap-3">
                          <div className="font-mono-num text-xs text-gnova-text-secondary w-24">
                            {new Date(day.date).toLocaleDateString('fa-IR')}
                          </div>
                          <div className="flex-1 h-8 bg-gnova-background rounded relative overflow-hidden">
                            <div 
                              className="absolute right-0 top-0 h-full bg-gradient-to-l from-gnova-accent to-gnova-success transition-all" 
                              style={{ width: `${widthPercent}%` }}
                            ></div>
                            <div className="absolute inset-0 flex items-center justify-between px-3 text-xs">
                              <span className="font-mono-num text-gnova-text-secondary">
                                {day.count} تراکنش
                              </span>
                              <span className="font-mono-num font-bold">
                                {formatNumber(day.total)}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              
              {/* Smart Insights */}
              <div className="gnova-card mt-6 bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
                <h3 className="font-heading font-semibold mb-3 flex items-center gap-2">
                  <span className="text-2xl">💡</span> پیشنهادات هوشمند
                </h3>
                <div className="space-y-2 text-sm">
                  {(analytics?.this_month?.net_flow || 0) >= 0 ? (
                    <p className="text-blue-800">
                      ✅ جریان نقدی شما مثبت است. می‌توانید بخشی از دارایی‌ها را به USDT تبدیل کنید.
                    </p>
                  ) : (
                    <p className="text-blue-800">
                      ⚠️ برداشت‌های شما بیش از واریزها است. مدیریت هزینه‌ها را در نظر بگیرید.
                    </p>
                  )}
                  <p className="text-blue-800">
                    📊 تنظیم هشدار نرخ برای USDT می‌تواند به شما در زمان‌سنجی بهتر تبدیل کمک کند.
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
};

export default AnalyticsPage;
