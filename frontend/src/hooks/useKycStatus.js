import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

/**
 * Manages KYC submission status and actions (submit, demo auto-approve).
 */
export const useKycStatus = (onMessage) => {
  const { apiCall, refetch } = useAuth();
  const [kycSubmission, setKycSubmission] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchKYCStatus = useCallback(async () => {
    try {
      const response = await apiCall('GET', '/kyc/status');
      setKycSubmission(response.data.submission);
    } catch (error) {
      console.error('Failed to fetch KYC status:', error);
    }
  }, [apiCall]);

  useEffect(() => {
    fetchKYCStatus();
  }, [fetchKYCStatus]);

  const submitKYC = useCallback(async (kycForm) => {
    setLoading(true);
    onMessage({ type: '', text: '' });
    try {
      await apiCall('POST', '/kyc/submit', kycForm);
      onMessage({ type: 'success', text: 'درخواست KYC با موفقیت ارسال شد. در حال بررسی...' });
      await fetchKYCStatus();
      await refetch();
    } catch (error) {
      onMessage({ type: 'error', text: error.response?.data?.detail || 'خطا در ارسال' });
    } finally {
      setLoading(false);
    }
  }, [apiCall, fetchKYCStatus, refetch, onMessage]);

  const autoApproveKYC = useCallback(async () => {
    setLoading(true);
    onMessage({ type: '', text: '' });
    try {
      await apiCall('POST', '/kyc/auto-approve');
      onMessage({ type: 'success', text: 'KYC تایید شد! اکنون می‌توانید برداشت کنید.' });
      await fetchKYCStatus();
      await refetch();
    } catch (error) {
      onMessage({ type: 'error', text: error.response?.data?.detail || 'خطا' });
    } finally {
      setLoading(false);
    }
  }, [apiCall, fetchKYCStatus, refetch, onMessage]);

  return { kycSubmission, loading, submitKYC, autoApproveKYC };
};
