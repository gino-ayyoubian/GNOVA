import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Sparkles, 
  Wallet, 
  Repeat, 
  BarChart3, 
  Shield, 
  Send,
  Zap,
  TrendingUp,
  Lock,
  ArrowLeft,
  CheckCircle2
} from 'lucide-react';
import { GNOVA } from '@/constants/testIds';

const LandingPage = () => {
  const features = [
    {
      icon: Wallet,
      title: 'کیف پول چند ارزی',
      description: 'مدیریت ریال، USDT و بیت‌کوین در یک پلتفرم'
    },
    {
      icon: Repeat,
      title: 'تبدیل آنی',
      description: 'تبدیل دارایی‌ها با نرخ قفل‌شده و کارمزد پایین'
    },
    {
      icon: BarChart3,
      title: 'تحلیل هوشمند',
      description: 'بینش‌های مالی و گزارش‌های دقیق از خرج‌کرد شما'
    },
    {
      icon: Shield,
      title: 'امنیت بالا',
      description: 'دفتر کل غیرقابل تغییر و تأیید دو مرحله‌ای'
    },
    {
      icon: Send,
      title: 'بات تلگرام',
      description: 'دسترسی کامل از طریق @KKM_GNOVA_bot'
    },
    {
      icon: Zap,
      title: 'پردازش سریع',
      description: 'واریز در کمتر از 5 دقیقه، برداشت 24 ساعته'
    }
  ];
  
  const stats = [
    { label: 'تراکنش روزانه', value: '10K+' },
    { label: 'دارایی پشتیبانی شده', value: '4' },
    { label: 'زمان پردازش', value: '<5min' },
    { label: 'امنیت', value: '99.9%' }
  ];
  
  return (
    <div className="min-h-screen bg-gnova-background">
      {/* Header */}
      <header className="glass-header sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3" data-testid={GNOVA.navLogo}>
            <div className="w-10 h-10 bg-gnova-primary rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-heading font-bold text-xl text-gnova-text-primary">GNOVA</h1>
              <p className="text-xs text-gnova-text-secondary">Fintech Platform</p>
            </div>
          </Link>
          
          <div className="flex items-center gap-3">
            <a 
              href="https://t.me/KKM_GNOVA_bot" 
              target="_blank" 
              rel="noopener noreferrer"
              data-testid={GNOVA.heroCtaTelegram}
              className="hidden md:flex items-center gap-2 px-4 py-2 text-gnova-text-primary hover:text-gnova-accent transition-colors"
            >
              <Send className="w-4 h-4" />
              <span>بات تلگرام</span>
            </a>
            <Link 
              to="/login" 
              data-testid={GNOVA.heroCtaDashboard}
              className="gnova-button-primary"
            >
              ورود
            </Link>
          </div>
        </div>
      </header>
      
      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20 lg:py-32">
        <div className="max-w-4xl mx-auto text-center animate-fade-in">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-gnova-accent/10 text-gnova-accent rounded-full text-sm font-medium mb-6">
            <CheckCircle2 className="w-4 h-4" />
            <span>پلتفرم مالی هوشمند برای ایرانیان</span>
          </div>
          
          <h1 
            data-testid={GNOVA.heroTitle}
            className="font-heading text-4xl sm:text-5xl lg:text-6xl font-black text-gnova-text-primary mb-6 leading-tight"
            style={{ fontFamily: 'Vazirmatn, sans-serif' }}
          >
            مدیریت دارایی‌های شما
            <br />
            <span className="text-gnova-accent">به سادگی یک پیام تلگرام</span>
          </h1>
          
          <p className="text-lg sm:text-xl text-gnova-text-secondary mb-10 max-w-2xl mx-auto leading-relaxed">
            GNOVA پلتفرم جامع مالی برای واریز، برداشت، تبدیل ارز و رمزارز با امنیت بانکی و سادگی تلگرام.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <a 
              href="https://t.me/KKM_GNOVA_bot" 
              target="_blank" 
              rel="noopener noreferrer"
              className="gnova-button-accent flex items-center gap-2 text-base px-8 py-4"
              data-testid="gnova-hero-telegram-btn"
            >
              <Send className="w-5 h-5" />
              <span>شروع با تلگرام</span>
            </a>
            <Link 
              to="/login"
              className="gnova-button-primary flex items-center gap-2 text-base px-8 py-4"
              data-testid="gnova-hero-login-btn"
            >
              <span>ورود به داشبورد</span>
              <ArrowLeft className="w-5 h-5" />
            </Link>
          </div>
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-4xl mx-auto">
          {stats.map((stat, idx) => (
            <div key={idx} className="text-center animate-slide-up" style={{ animationDelay: `${idx * 100}ms` }}>
              <div className="font-mono-num text-3xl md:text-4xl font-bold text-gnova-primary mb-2">
                {stat.value}
              </div>
              <div className="text-sm text-gnova-text-secondary">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </section>
      
      {/* Features */}
      <section className="container mx-auto px-6 py-20">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <p className="text-overline text-xs uppercase tracking-[0.2em] font-bold text-gnova-text-secondary mb-3">
            ویژگی‌ها
          </p>
          <h2 className="font-heading text-3xl sm:text-4xl lg:text-5xl font-bold text-gnova-text-primary mb-4" style={{ fontFamily: 'Vazirmatn, sans-serif' }}>
            همه چیزی که نیاز دارید
          </h2>
          <p className="text-lg text-gnova-text-secondary">
            از واریز ساده تا تحلیل پیشرفته، GNOVA همه نیازهای مالی شما را پوشش می‌دهد.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <div 
                key={idx}
                data-testid={GNOVA.featureCard}
                className="gnova-card gnova-card-hover animate-slide-up"
                style={{ animationDelay: `${idx * 100}ms` }}
              >
                <div className="w-12 h-12 bg-gnova-primary/5 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-gnova-primary" />
                </div>
                <h3 className="font-heading font-semibold text-xl text-gnova-text-primary mb-2">
                  {feature.title}
                </h3>
                <p className="text-gnova-text-secondary leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </section>
      
      {/* Trust Section */}
      <section className="container mx-auto px-6 py-20">
        <div className="bg-gnova-primary rounded-2xl p-12 lg:p-20 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-gnova-accent/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 rounded-full text-sm font-medium mb-6">
              <Lock className="w-4 h-4" />
              <span>امنیت در اولویت</span>
            </div>
            <h2 className="font-heading text-3xl sm:text-4xl lg:text-5xl font-bold mb-6" style={{ fontFamily: 'Vazirmatn, sans-serif' }}>
              معماری امنیتی بانکی برای دارایی‌های شما
            </h2>
            <p className="text-lg text-white/80 mb-8 leading-relaxed">
              GNOVA با استفاده از دفتر کل غیرقابل تغییر (Immutable Ledger)، رمزنگاری پیشرفته و تأیید چند مرحله‌ای، 
              امنیتی هم‌تراز با بانک‌های بین‌المللی ارائه می‌دهد.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <div className="font-mono-num text-3xl font-bold text-gnova-accent mb-1">256-bit</div>
                <div className="text-sm text-white/70">رمزنگاری</div>
              </div>
              <div>
                <div className="font-mono-num text-3xl font-bold text-gnova-accent mb-1">2FA</div>
                <div className="text-sm text-white/70">احراز هویت</div>
              </div>
              <div>
                <div className="font-mono-num text-3xl font-bold text-gnova-accent mb-1">99.9%</div>
                <div className="text-sm text-white/70">آپتایم</div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* CTA Section */}
      <section className="container mx-auto px-6 py-20">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-heading text-3xl sm:text-4xl lg:text-5xl font-bold text-gnova-text-primary mb-6" style={{ fontFamily: 'Vazirmatn, sans-serif' }}>
            آماده شروع هستید؟
          </h2>
          <p className="text-lg text-gnova-text-secondary mb-10">
            در کمتر از 30 ثانیه ثبت‌نام کنید و تجربه‌ای جدید از مدیریت دارایی‌های مالی را آغاز کنید.
          </p>
          <a 
            href="https://t.me/KKM_GNOVA_bot" 
            target="_blank" 
            rel="noopener noreferrer"
            className="gnova-button-accent inline-flex items-center gap-2 text-lg px-10 py-5"
          >
            <Send className="w-6 h-6" />
            <span>شروع رایگان</span>
          </a>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="border-t border-gnova-border bg-white">
        <div className="container mx-auto px-6 py-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gnova-primary rounded-md flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="font-heading font-bold text-gnova-text-primary">GNOVA Fintech</span>
            </div>
            <div className="text-sm text-gnova-text-secondary">
              © 2026 GNOVA. تمامی حقوق محفوظ است.
            </div>
            <div className="flex gap-4">
              <a href="https://t.me/KKM_GNOVA_bot" target="_blank" rel="noopener noreferrer" 
                 className="text-gnova-text-secondary hover:text-gnova-accent transition-colors">
                <Send className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
