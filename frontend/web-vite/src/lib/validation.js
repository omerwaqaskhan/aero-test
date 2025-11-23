


export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!email) return "Email is required"
  if (!emailRegex.test(email)) return "Please enter a valid email address"
  return null
}

export const validatePassword = (password) => {
  if (!password) return "Password is required"
  if (password.length < 8) return "Password must be at least 8 characters long"
  if (!/(?=.*[a-z])/.test(password)) return "Password must contain at least one lowercase letter"
  if (!/(?=.*[A-Z])/.test(password)) return "Password must contain at least one uppercase letter"
  if (!/(?=.*\d)/.test(password)) return "Password must contain at least one number"
  if (!/(?=.*[@$!%*?&])/.test(password)) return "Password must contain at least one special character"
  return null
}

export const validatePhone = (phone) => {
  const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/
  if (!phone) return "Phone number is required"
  if (!phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ""))) {
    return "Please enter a valid phone number"
  }
  return null
}

export const validateName = (name, fieldName) => {
  if (!name) return `${fieldName} is required`
  if (name.length < 2) return `${fieldName} must be at least 2 characters long`
  if (name.length > 50) return `${fieldName} must be less than 50 characters`
  if (!/^[a-zA-Z\s]+$/.test(name)) return `${fieldName} can only contain letters and spaces`
  return null
}

export const validateLoginForm = (email, password) => {
  const errors = []

  const emailError = validateEmail(email)
  if (emailError) errors.push({ field: "email", message: emailError })

  if (!password) errors.push({ field: "password", message: "Password is required" })

  return {
    isValid: errors.length === 0,
    errors,
  }
}

export const validateRegisterForm = (formData) => {
  const errors = []

  const firstNameError = validateName(formData.firstName, "First name")
  if (firstNameError) errors.push({ field: "firstName", message: firstNameError })

  const lastNameError = validateName(formData.lastName, "Last name")
  if (lastNameError) errors.push({ field: "lastName", message: lastNameError })

  const emailError = validateEmail(formData.email)
  if (emailError) errors.push({ field: "email", message: emailError })

  const phoneError = validatePhone(formData.phone)
  if (phoneError) errors.push({ field: "phone", message: phoneError })

  const passwordError = validatePassword(formData.password)
  if (passwordError) errors.push({ field: "password", message: passwordError })

  if (formData.password !== formData.confirmPassword) {
    errors.push({ field: "confirmPassword", message: "Passwords do not match" })
  }

  if (!formData.termsAccepted) {
    errors.push({ field: "terms", message: "You must accept the terms and conditions" })
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

export const validateForgotPasswordForm = (email) => {
  const errors = []

  const emailError = validateEmail(email)
  if (emailError) errors.push({ field: "email", message: emailError })

  return {
    isValid: errors.length === 0,
    errors,
  }
}

export const validateResetPasswordForm = (password, confirmPassword) => {
  const errors = []

  const passwordError = validatePassword(password)
  if (passwordError) errors.push({ field: "password", message: passwordError })

  if (password !== confirmPassword) {
    errors.push({ field: "confirmPassword", message: "Passwords do not match" })
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}
