import { useState } from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

/**
 * Enhanced form field component with better validation UX
 */
export default function FormField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  onBlur,
  error,
  helperText,
  required = false,
  disabled = false,
  placeholder,
  className = '',
  validationRules = [],
  showSuccess = false,
  ...props
}) {
  const [touched, setTouched] = useState(false);
  const [focused, setFocused] = useState(false);

  const handleBlur = (e) => {
    setTouched(true);
    setFocused(false);
    if (onBlur) {
      onBlur(e);
    }
  };

  const handleFocus = () => {
    setFocused(true);
  };

  const showError = touched && error;
  const showSuccessIcon = showSuccess && touched && !error && value;

  const inputClasses = `
    w-full px-4 py-3 rounded-lg border transition-all
    ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'}
    ${showError 
      ? 'border-red-500 focus:ring-red-500 focus:border-red-500' 
      : showSuccessIcon
      ? 'border-green-500 focus:ring-green-500 focus:border-green-500'
      : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
    }
    ${focused ? 'ring-2' : ''}
    ${className}
  `.trim();

  return (
    <div className="space-y-2">
      {label && (
        <label 
          htmlFor={name} 
          className="block text-sm font-medium text-gray-700"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      <div className="relative">
        <input
          id={name}
          name={name}
          type={type}
          value={value || ''}
          onChange={onChange}
          onBlur={handleBlur}
          onFocus={handleFocus}
          disabled={disabled}
          placeholder={placeholder}
          required={required}
          className={inputClasses}
          aria-invalid={showError ? 'true' : 'false'}
          aria-describedby={showError ? `${name}-error` : helperText ? `${name}-helper` : undefined}
          {...props}
        />

        {showSuccessIcon && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <CheckCircle2 className="w-5 h-5 text-green-500" />
          </div>
        )}

        {showError && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <AlertCircle className="w-5 h-5 text-red-500" />
          </div>
        )}
      </div>

      {showError && (
        <p 
          id={`${name}-error`}
          className="text-sm text-red-600 flex items-center gap-1"
          role="alert"
        >
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </p>
      )}

      {helperText && !showError && (
        <p 
          id={`${name}-helper`}
          className="text-sm text-gray-500"
        >
          {helperText}
        </p>
      )}
    </div>
  );
}

