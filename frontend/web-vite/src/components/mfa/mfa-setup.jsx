import React, { useState } from 'react';
import { Shield, CheckCircle, AlertCircle, Copy, Download } from 'lucide-react';
import { authApi } from '../../lib/auth-api';
import { useToast } from '../../hooks/use-toast-context';

const MFASetup = ({ onComplete, onCancel }) => {
  const [step, setStep] = useState(1); // 1: QR code, 2: Verify, 3: Backup codes
  const [qrCode, setQrCode] = useState(null);
  const [secret, setSecret] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [backupCodes, setBackupCodes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const { success, error } = useToast();

  const handleSetup = async () => {
    try {
      setIsLoading(true);
      const response = await authApi.setupMFA({ method: 'totp' });
      
      if (response) {
        setQrCode(response.qr_code);
        setSecret(response.secret);
        setStep(2);
        success('MFA Setup', 'Scan the QR code with your authenticator app');
      }
    } catch (err) {
      error('MFA Setup Failed', err.message || 'Failed to setup MFA');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      error('Invalid Code', 'Please enter a 6-digit code');
      return;
    }

    try {
      setIsLoading(true);
      const response = await authApi.verifyMFA({ code: verificationCode });
      
      if (response) {
        setBackupCodes(response.backup_codes || []);
        setStep(3);
        success('MFA Enabled', 'Multi-factor authentication has been enabled');
      }
    } catch (err) {
      error('Verification Failed', err.message || 'Invalid verification code');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopySecret = () => {
    navigator.clipboard.writeText(secret);
    success('Copied', 'Secret key copied to clipboard');
  };

  const handleDownloadBackupCodes = () => {
    const codesText = backupCodes.join('\n');
    const blob = new Blob([codesText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mfa-backup-codes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (step === 1) {
    return (
      <div className="max-w-md mx-auto p-6 bg-white rounded-xl shadow-lg">
        <div className="text-center mb-6">
          <Shield className="w-16 h-16 mx-auto mb-4 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Enable Two-Factor Authentication</h2>
          <p className="text-gray-600">
            Add an extra layer of security to your account
          </p>
        </div>

        <div className="space-y-4 mb-6">
          <div className="flex items-start space-x-3">
            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <p className="font-medium text-gray-900">Enhanced Security</p>
              <p className="text-sm text-gray-600">Protect your account from unauthorized access</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <p className="font-medium text-gray-900">Easy to Use</p>
              <p className="text-sm text-gray-600">Scan QR code with Google Authenticator or similar app</p>
            </div>
          </div>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleSetup}
            disabled={isLoading}
            className="flex-1 bg-gradient-to-r from-blue-600 to-teal-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-teal-700 transition-all disabled:opacity-50"
          >
            {isLoading ? 'Setting up...' : 'Start Setup'}
          </button>
          {onCancel && (
            <button
              onClick={onCancel}
              className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition-all"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    );
  }

  if (step === 2) {
    return (
      <div className="max-w-md mx-auto p-6 bg-white rounded-xl shadow-lg">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Scan QR Code</h2>
          <p className="text-gray-600">
            Use your authenticator app to scan this QR code
          </p>
        </div>

        {qrCode && (
          <div className="mb-6 flex justify-center">
            <img
              src={`data:image/png;base64,${qrCode}`}
              alt="MFA QR Code"
              className="w-64 h-64 border-2 border-gray-200 rounded-lg"
            />
          </div>
        )}

        {secret && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Or enter this code manually:</p>
            <div className="flex items-center space-x-2">
              <code className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded font-mono text-sm">
                {secret}
              </code>
              <button
                onClick={handleCopySecret}
                className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-all"
                title="Copy secret"
              >
                <Copy className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Enter verification code
          </label>
          <input
            type="text"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            placeholder="000000"
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center text-2xl font-mono tracking-widest"
            maxLength={6}
          />
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleVerify}
            disabled={isLoading || verificationCode.length !== 6}
            className="flex-1 bg-gradient-to-r from-blue-600 to-teal-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-teal-700 transition-all disabled:opacity-50"
          >
            {isLoading ? 'Verifying...' : 'Verify & Enable'}
          </button>
          <button
            onClick={() => setStep(1)}
            className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition-all"
          >
            Back
          </button>
        </div>
      </div>
    );
  }

  if (step === 3) {
    return (
      <div className="max-w-md mx-auto p-6 bg-white rounded-xl shadow-lg">
        <div className="text-center mb-6">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-500" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">MFA Enabled Successfully!</h2>
          <p className="text-gray-600">
            Save these backup codes in a safe place
          </p>
        </div>

        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <p className="text-sm text-yellow-800">
              These codes can be used to access your account if you lose your authenticator device.
              Each code can only be used once.
            </p>
          </div>
        </div>

        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-2 gap-2">
            {backupCodes.map((code, index) => (
              <code
                key={index}
                className="px-3 py-2 bg-white border border-gray-300 rounded font-mono text-sm text-center"
              >
                {code}
              </code>
            ))}
          </div>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleDownloadBackupCodes}
            className="flex-1 flex items-center justify-center space-x-2 bg-gray-100 text-gray-700 px-6 py-3 rounded-xl font-semibold hover:bg-gray-200 transition-all"
          >
            <Download className="w-5 h-5" />
            <span>Download Codes</span>
          </button>
          {onComplete && (
            <button
              onClick={onComplete}
              className="flex-1 bg-gradient-to-r from-blue-600 to-teal-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-teal-700 transition-all"
            >
              Done
            </button>
          )}
        </div>
      </div>
    );
  }

  return null;
};

export default MFASetup;


