import React, { useState, useEffect } from 'react';
import { BellRing, Plus, Trash2, ArrowUp, ArrowDown, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';

const AlertsPage = () => {
  const { apiCall } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [form, setForm] = useState({
    from_asset: 'USDT',
    to_asset: 'IRR',
    target_rate: '',
    condition: 'below'
  });
  
  useEffect(() => {
    fetchAlerts();
  }, []);
  
  const fetchAlerts = async () => {
    try {
      const response = await apiCall('GET', '/alerts');
      setAlerts(response.data.alerts || []);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const createAlert = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage({ type: '', text: '' });
    try {
      await apiCall('POST', '/alerts/rate', {
        ...form,
        target_rate: parseFloat(form.target_rate)
      });
      setMessage({ type: 'success', text: 'هشدار با موفقیت ایجاد شد' });
      setForm({ from_asset: 'USDT', to_asset: 'IRR', target_rate: '', condition: 'below' });
      setShowForm(false);
      await fetchAlerts();
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'خطا در ایجاد هشدار' });
    } finally {
      setSubmitting(false);
    }
  };
  
  const deleteAlert = async (alertId) => {
    try {
      await apiCall('DELETE', `/alerts/${alertId}`);
      await fetchAlerts();
    } catch (error) {
      console.error('Failed to delete alert:', error);
    }
  };
  
  return (
    <div className="min-h-screen bg-gnova-background">
      <Sidebar />
      <main className="mr-64 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8 animate-fade-in flex items-start justify-between">
            <div>
              <p className="text-overline text-xs uppercase tracking-[0.2em] font-bold text-gnova-text-secondary mb-2">
                هشدارها
              </p>
              <h1 className="font-heading text-3xl font-bold text-gnova-text-primary flex items-center gap-3" style={{ fontFamily: 'Vazirmatn, sans-serif' }}>
                <BellRing className="w-8 h-8 text-gnova-primary" />
                هشدارهای نرخ
              </h1>
              <p className="text-gnova-text-secondary mt-2">با تغییر نرخ‌های مهم بازار، در تلگرام مطلع شوید</p>
            </div>
            <button onClick={() => setShowForm(!showForm)} className="gnova-button-primary flex items-center gap-2" data-testid="alert-new-btn">
              <Plus className="w-4 h-4" />
              هشدار جدید
            </button>
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
          
          {/* Create Alert Form */}
          {showForm && (
            <div className="gnova-card mb-6 animate-fade-in">
              <h3 className="font-heading font-semibold mb-4">ایجاد هشدار جدید</h3>
              <form onSubmit={createAlert} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">از</label>
                    <select 
                      value={form.from_asset} 
                      onChange={(e) => setForm({...form, from_asset: e.target.value})}
                      className="gnova-input"
                      data-testid="alert-from-asset"
                    >
                      <option value="USDT">USDT</option>
                      <option value="BTC">BTC</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">به</label>
                    <select 
                      value={form.to_asset} 
                      onChange={(e) => setForm({...form, to_asset: e.target.value})}
                      className="gnova-input"
                      data-testid="alert-to-asset"
                    >
                      <option value="IRR">IRR</option>
                      <option value="USDT">USDT</option>
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">شرط</label>
                    <select 
                      value={form.condition} 
                      onChange={(e) => setForm({...form, condition: e.target.value})}
                      className="gnova-input"
                      data-testid="alert-condition"
                    >
                      <option value="below">کمتر از</option>
                      <option value="above">بیشتر از</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">نرخ هدف</label>
                    <input 
                      type="number"
                      step="any"
                      value={form.target_rate}
                      onChange={(e) => setForm({...form, target_rate: e.target.value})}
                      className="gnova-input font-mono-num"
                      placeholder="65000"
                      data-testid="alert-target-rate"
                      required
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button type="submit" disabled={submitting} className="gnova-button-accent flex-1" data-testid="alert-submit">
                    {submitting ? 'در حال ایجاد...' : 'ایجاد هشدار'}
                  </button>
                  <button type="button" onClick={() => setShowForm(false)} className="px-4 py-3 border border-gnova-border rounded-md">
                    انصراف
                  </button>
                </div>
              </form>
            </div>
          )}
          
          {/* Alerts List */}
          {loading ? (
            <div className="gnova-card text-center py-8 text-gnova-text-secondary">در حال بارگیری...</div>
          ) : alerts.length === 0 ? (
            <div className="gnova-card text-center py-16">
              <BellRing className="w-16 h-16 text-gnova-text-secondary mx-auto mb-4 opacity-30" />
              <h3 className="font-heading font-semibold mb-2">هنوز هشداری ندارید</h3>
              <p className="text-gnova-text-secondary mb-4">
                هشدار اول خود را ایجاد کنید تا از تغییرات نرخ مطلع شوید
              </p>
              {!showForm && (
                <button onClick={() => setShowForm(true)} className="gnova-button-primary">
                  ایجاد هشدار اول
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div key={alert.id} className="gnova-card flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                      alert.condition === 'below' ? 'bg-gnova-danger/10' : 'bg-gnova-success/10'
                    }`}>
                      {alert.condition === 'below' ? (
                        <ArrowDown className={`w-6 h-6 text-gnova-danger`} />
                      ) : (
                        <ArrowUp className={`w-6 h-6 text-gnova-success`} />
                      )}
                    </div>
                    <div>
                      <h4 className="font-semibold">
                        {alert.from_asset} → {alert.to_asset}
                      </h4>
                      <p className="text-sm text-gnova-text-secondary">
                        وقتی نرخ {alert.condition === 'below' ? 'کمتر از' : 'بیشتر از'}{' '}
                        <span className="font-mono-num font-semibold">
                          {Number(alert.target_rate).toLocaleString('fa-IR')}
                        </span>{' '}
                        شد
                      </p>
                      <p className="text-xs text-gnova-text-secondary mt-1 font-mono-num">
                        ایجاد: {new Date(alert.created_at).toLocaleDateString('fa-IR')}
                      </p>
                    </div>
                  </div>
                  <button 
                    onClick={() => deleteAlert(alert.id)}
                    className="p-2 hover:bg-gnova-danger/10 rounded-md text-gnova-danger transition-colors"
                    data-testid={`alert-delete-${alert.id}`}
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          )}
          
          {/* Info Box */}
          <div className="mt-6 gnova-card bg-blue-50 border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-2">📢 چگونه کار می‌کند؟</h4>
            <ul className="text-sm text-blue-800 space-y-1 mr-4">
              <li>• هر دقیقه نرخ‌های بازار بررسی می‌شوند</li>
              <li>• اگر شرط هشدار شما برقرار شود، پیام به تلگرام شما ارسال می‌شود</li>
              <li>• هر هشدار فقط یک بار فعال می‌شود</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AlertsPage;
