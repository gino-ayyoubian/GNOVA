import React from 'react';
import Sidebar from '../components/Sidebar';
import { Wallet, BarChart3, BellRing, Settings as SettingsIcon, Construction } from 'lucide-react';

const PlaceholderPage = ({ title, icon: Icon, description }) => (
  <div className="min-h-screen bg-gnova-background">
    <Sidebar />
    <main className="mr-64 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 animate-fade-in">
          <p className="text-overline text-xs uppercase tracking-[0.2em] font-bold text-gnova-text-secondary mb-2">
            GNOVA
          </p>
          <h1 className="font-heading text-3xl font-bold text-gnova-text-primary flex items-center gap-3">
            <Icon className="w-8 h-8 text-gnova-primary" />
            {title}
          </h1>
          <p className="text-gnova-text-secondary mt-2">{description}</p>
        </div>
        
        <div className="gnova-card text-center py-16">
          <Construction className="w-16 h-16 text-gnova-warning mx-auto mb-4 opacity-60" />
          <h2 className="font-heading text-xl font-semibold text-gnova-text-primary mb-2">
            در حال توسعه
          </h2>
          <p className="text-gnova-text-secondary max-w-md mx-auto">
            این بخش به زودی فعال خواهد شد. تا آن زمان می‌توانید از سایر امکانات استفاده کنید.
          </p>
        </div>
      </div>
    </main>
  </div>
);

export const WalletPage = () => (
  <PlaceholderPage title="کیف پول" icon={Wallet} description="مدیریت کامل دارایی‌های شما" />
);

export const AnalyticsPage = () => (
  <PlaceholderPage title="تحلیل" icon={BarChart3} description="بینش‌های هوشمند از وضعیت مالی شما" />
);

export const AlertsPage = () => (
  <PlaceholderPage title="هشدارهای نرخ" icon={BellRing} description="مدیریت اعلان‌های تغییر نرخ" />
);

export const SettingsPage = () => (
  <PlaceholderPage title="تنظیمات" icon={SettingsIcon} description="تنظیمات حساب و امنیت" />
);
