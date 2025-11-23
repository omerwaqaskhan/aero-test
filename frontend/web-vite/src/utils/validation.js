/**
 * Enhanced client-side validation utilities
 */

export const ValidationRules = {
  required: (value) => {
    if (!value || (typeof value === 'string' && !value.trim())) {
      return 'This field is required';
    }
    return null;
  },

  email: (value) => {
    if (!value) return null; // Let required handle empty
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return 'Please enter a valid email address';
    }
    return null;
  },

  minLength: (min) => (value) => {
    if (!value) return null;
    if (value.length < min) {
      return `Must be at least ${min} characters`;
    }
    return null;
  },

  maxLength: (max) => (value) => {
    if (!value) return null;
    if (value.length > max) {
      return `Must be no more than ${max} characters`;
    }
    return null;
  },

  password: (value) => {
    if (!value) return null;
    
    const errors = [];
    
    if (value.length < 10) {
      errors.push('at least 10 characters');
    }
    if (!/[A-Z]/.test(value)) {
      errors.push('one uppercase letter');
    }
    if (!/[a-z]/.test(value)) {
      errors.push('one lowercase letter');
    }
    if (!/[0-9]/.test(value)) {
      errors.push('one number');
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(value)) {
      errors.push('one special character');
    }
    
    if (errors.length > 0) {
      return `Password must contain ${errors.join(', ')}`;
    }
    
    // Check for common weak passwords
    const weakPasswords = ['password', '123456', 'qwerty', 'admin', 'letmein'];
    if (weakPasswords.some(weak => value.toLowerCase().includes(weak))) {
      return 'Password is too weak. Please choose a stronger password';
    }
    
    return null;
  },

  match: (otherValue, fieldName = 'field') => (value) => {
    if (!value) return null;
    if (value !== otherValue) {
      return `Must match ${fieldName}`;
    }
    return null;
  },

  phone: (value) => {
    if (!value) return null;
    const phoneRegex = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
    if (!phoneRegex.test(value.replace(/\s/g, ''))) {
      return 'Please enter a valid phone number';
    }
    return null;
  },

  url: (value) => {
    if (!value) return null;
    try {
      new URL(value);
      return null;
    } catch {
      return 'Please enter a valid URL';
    }
  },

  number: (value) => {
    if (!value) return null;
    if (isNaN(value) || value === '') {
      return 'Must be a valid number';
    }
    return null;
  },

  min: (min) => (value) => {
    if (!value) return null;
    const num = parseFloat(value);
    if (isNaN(num) || num < min) {
      return `Must be at least ${min}`;
    }
    return null;
  },

  max: (max) => (value) => {
    if (!value) return null;
    const num = parseFloat(value);
    if (isNaN(num) || num > max) {
      return `Must be no more than ${max}`;
    }
    return null;
  },

  date: (value) => {
    if (!value) return null;
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      return 'Please enter a valid date';
    }
    return null;
  },

  futureDate: (value) => {
    if (!value) return null;
    const date = new Date(value);
    const now = new Date();
    if (date <= now) {
      return 'Date must be in the future';
    }
    return null;
  },
};

/**
 * Validate a field with multiple rules
 */
export function validateField(value, rules) {
  if (!Array.isArray(rules)) {
    rules = [rules];
  }

  for (const rule of rules) {
    const error = typeof rule === 'function' ? rule(value) : null;
    if (error) {
      return error;
    }
  }

  return null;
}

/**
 * Validate an entire form
 */
export function validateForm(formData, schema) {
  const errors = {};
  let isValid = true;

  for (const [field, rules] of Object.entries(schema)) {
    const value = formData[field];
    const error = validateField(value, rules);
    
    if (error) {
      errors[field] = error;
      isValid = false;
    }
  }

  return { errors, isValid };
}

/**
 * Real-time validation hook helper
 */
export function useFieldValidation(fieldName, value, rules, touched) {
  if (!touched) {
    return null;
  }
  
  return validateField(value, rules);
}

/**
 * Format validation error for display
 */
export function formatValidationError(error) {
  if (typeof error === 'string') {
    return error;
  }
  
  if (error?.message) {
    return error.message;
  }
  
  return 'Invalid input';
}

