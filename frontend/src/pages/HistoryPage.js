import React, { useState, useEffect } from 'react';
import { History as HistoryIcon, ArrowDownToLine, ArrowUpFromLine, Repeat, Activity, Download, Filter } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import { GNOVA } from '@/constants/testIds';

const HistoryPage = () => {
  const { apiCall } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  
  useEffect(() => {
    fetchTransactions();
  }, []);
  
  const fetchTransactions = async () => {
    try {
      const response = await apiCall('GET', '/transactions?limit=100');
      setTransactions(response.data.transactions || []);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const typeMap = {
    deposit: { label: 'واریز', icon: ArrowDownToLine, color: 'text-gnova-success', bg: 'bg-gnova-success/10' },
    deposit_confirmed: { label: 'واریز', icon: ArrowDownToLine, color: 'text-gnova-success', bg: 'bg-gnova-success/10' },
    withdraw: { label: 'برداشت', icon: ArrowUpFromLine, color: 'text-gnova-danger', bg: 'bg-gnova-danger/10' },
    reserve: { label: 'برداشت در انتظار', icon: ArrowUpFromLine, color: 'text-gnova-warning', bg: 'bg-gnova-warning/10' },
    conversion_credit: { label: 'تبدیل (دریافت)', icon: Repeat, color: 'text-blue-600', bg: 'bg-blue-50' },
    conversion_debit: { label: 'تبدیل (پرداخت)', icon: Repeat, color: 'text-blue-600', bg: 'bg-blue-50' },
  };
  
  const filteredTransactions = filter === 'all' 
    ? transactions 
    : transactions.filter(tx => {
        if (filter === 'deposit') return ['deposit', 'deposit_confirmed'].includes(tx.type);
        if (filter === 'withdraw') return ['withdraw', 'reserve'].includes(tx.type);
        if (filter === 'convert') return ['conversion_credit', 'conversion_debit'].includes(tx.type);
        return true;
      });
  
  const exportCSV = () => {
    const headers = ['ID', 'Type', 'Status', 'Amount', 'Asset', 'Date'];
    const rows = filteredTransactions.map(tx => [
      tx.id,
      tx.type,
      tx.status,
      tx.amount_from_minor,
      tx.asset_from_code || 'IRR',
      new Date(tx.created_at).toLocaleString('fa-IR')
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gnova-transactions-${Date.now()}.csv`;
    a.click();
  };
  
  return (
    <div className="min-h-screen bg-gnova-background">
      <Sidebar />
      <main className="mr-64 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8 animate-fade-in flex items-center justify-between">
            <div>
              <p className="text-overline text-xs uppercase tracking-[0.2em] font-bold text-gnova-text-secondary mb-2">
                گزارش‌ها
              </p>
              <h1 className="font-heading text-3xl font-bold text-gnova-text-primary flex items-center gap-3">
                <HistoryIcon className="w-8 h-8 text-gnova-primary" />
                تاریخچه تراکنش‌ها
              </h1>
            </div>
            <button
              onClick={exportCSV}
              data-testid={GNOVA.historyExportCsv}
              className="gnova-button-primary flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              خروجی CSV
            </button>
          </div>
          
          {/* Filters */}
          <div className="gnova-card mb-6">
            <div className="flex items-center gap-3 flex-wrap">
              <Filter className="w-4 h-4 text-gnova-text-secondary" />
              {[
                { value: 'all', label: 'همه' },
                { value: 'deposit', label: 'واریزها' },
                { value: 'withdraw', label: 'برداشت‌ها' },
                { value: 'convert', label: 'تبدیل‌ها' }
              ].map(f => (
                <button
                  key={f.value}
                  onClick={() => setFilter(f.value)}
                  data-testid={`gnova-filter-${f.value}`}
                  className={`px-4 py-2 rounded-md text-sm transition-all ${
                    filter === f.value
                      ? 'bg-gnova-primary text-white'
                      : 'border border-gnova-border text-gnova-text-secondary hover:border-gnova-primary/50'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Transactions Table */}
          <div className="gnova-card overflow-hidden p-0">
            {loading ? (
              <div className="p-12 text-center text-gnova-text-secondary">در حال بارگیری...</div>
            ) : filteredTransactions.length === 0 ? (
              <div className="p-12 text-center text-gnova-text-secondary">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>تراکنشی یافت نشد</p>
              </div>
            ) : (
              <div className="overflow-x-auto" data-testid={GNOVA.historyTable}>
                <table className="w-full">
                  <thead className="bg-gnova-background border-b border-gnova-border">
                    <tr className="text-xs text-gnova-text-secondary uppercase tracking-wider">
                      <th className="px-6 py-4 text-right">نوع</th>
                      <th className="px-6 py-4 text-right">مبلغ</th>
                      <th className="px-6 py-4 text-right">ارز</th>
                      <th className="px-6 py-4 text-right">وضعیت</th>
                      <th className="px-6 py-4 text-right">تاریخ</th>
                      <th className="px-6 py-4 text-right">شناسه</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gnova-border">
                    {filteredTransactions.map((tx) => {
                      const info = typeMap[tx.type] || { label: tx.type, icon: Activity, color: 'text-gnova-text-secondary', bg: 'bg-gnova-background' };
                      const Icon = info.icon;
                      const statusClass = tx.status === 'settled' ? 'status-success' : 
                                          tx.status === 'processing' ? 'status-pending' : 'status-failed';
                      
                      return (
                        <tr key={tx.id} data-testid={GNOVA.historyRow} className="hover:bg-gnova-background transition-colors">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className={`w-8 h-8 ${info.bg} rounded-full flex items-center justify-center`}>
                                <Icon className={`w-4 h-4 ${info.color}`} />
                              </div>
                              <span className="font-medium text-sm">{info.label}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 font-mono-num font-semibold">
                            {tx.amount_from_minor?.toLocaleString('fa-IR')}
                          </td>
                          <td className="px-6 py-4 text-sm text-gnova-text-secondary">
                            {tx.asset_from_code || 'IRR'}
                          </td>
                          <td className="px-6 py-4">
                            <span className={`status-badge ${statusClass}`}>
                              {tx.status === 'settled' ? 'تکمیل' : tx.status === 'processing' ? 'در حال انجام' : 'ناموفق'}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm font-mono-num">
                            {new Date(tx.created_at).toLocaleString('fa-IR')}
                          </td>
                          <td className="px-6 py-4">
                            <code className="text-xs font-mono-num text-gnova-text-secondary">
                              {tx.id.substring(0, 8)}...
                            </code>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          
          <p className="text-xs text-gnova-text-secondary text-center mt-6">
            {filteredTransactions.length} تراکنش نمایش داده شده
          </p>
        </div>
      </main>
    </div>
  );
};

export default HistoryPage;
