import React from 'react';

const ProfileSettings = ({ user }) => {
  const kycLabel =
    user?.kyc_status === 'approved'
      ? 'تایید شده'
      : user?.kyc_status === 'submitted'
        ? 'در حال بررسی'
        : 'در انتظار';

  return (
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
            {kycLabel}
          </span>
        </div>
        <div className="flex justify-between py-3 border-b border-gnova-border">
          <span className="text-gnova-text-secondary">سطح ریسک</span>
          <span className="font-medium">{user?.risk_level || 'low'}</span>
        </div>
        <div className="flex justify-between py-3">
          <span className="text-gnova-text-secondary">تاریخ عضویت</span>
          <span className="font-mono-num text-sm">
            {user?.created_at ? new Date(user.created_at).toLocaleDateString('fa-IR') : '-'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ProfileSettings;
