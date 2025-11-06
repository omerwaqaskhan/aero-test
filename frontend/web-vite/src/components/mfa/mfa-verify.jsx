import React, { useState, useRef, useEffect } from 'react';
import { Shield, AlertCircle } from 'lucide-react';
import { authApi } from '../../lib/auth-api';
import { useToast } from '../../hooks/use-toast-context';

const MFAVerify = ({ onVerify, onCancel, methods = ['totp'] }) => {
  const [code, setCode] = useState('');
  const [method, setMethod] = useState(methods[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);
  const { error: showError, success } = useToast();

  useEffect(() => {
    // Auto-focus input
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleVerify = async () => {
    if (!code || code.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      
      const response = await authApi.verifyMFA({ code, method });
      
      if (response && onVerify) {
        success('Verified', 'MFA verification successful');
        onVerify(response);
      }
    } catch (err) {
      const errorMsg = err.message || 'Invalid verification code';
      setError(errorMsg);
      showError('Verification Failed', errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCodeChange = (e) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setCode(value);
    setError('');
    
    // Auto-submit when 6 digits entered
    if (value.length === 6) {
      setTimeout(() => handleVerify(), 100);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && code.length === 6) {
      handleVerify();
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-xl shadow-lg">
      <div className="text-center mb-6">
        <Shield className="w-16 h-16 mx-auto mb-4 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Two-Factor Authentication</h2>
        <p className="text-gray-600">
          Enter the verification code from your authenticator app
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Verification Code
        </label>
        <input
          ref={inputRef}
          type="text"
          value={code}
          onChange={handleCodeChange}
          onKeyPress={handleKeyPress}
          placeholder="000000"
          className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-center text-2xl font-mono tracking-widest"
          maxLength={6}
          disabled={isLoading}
        />
        <p className="mt-2 text-sm text-gray-500 text-center">
          Enter the 6-digit code from your authenticator app
        </p>
      </div>

      <div className="flex space-x-3">
        <button
          onClick={handleVerify}
          disabled={isLoading || code.length !== 6}
          className="flex-1 bg-gradient-to-r from-blue-600 to-teal-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-teal-700 transition-all disabled:opacity-50"
        >
          {isLoading ? 'Verifying...' : 'Verify'}
        </button>
        {onCancel && (
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transition-all disabled:opacity-50"
          >
            Cancel
          </button>
        )}
      </div>

      <div className="mt-6 text-center">
        <button
          onClick={() => {
            // Resend code or use backup code
            setError('');
            setCode('');
          }}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          Having trouble? Use a backup code
        </button>
      </div>
    </div>
  );
};

export default MFAVerify;


