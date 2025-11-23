import * as React from "react"
import { cn } from "../../lib/utils"

const Form = React.forwardRef(
  ({ className, ...props }, ref) => (
    <form
      ref={ref}
      className={cn("space-y-4", className)}
      {...props}
    />
  )
)
Form.displayName = "Form"

const FormField = React.forwardRef(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("space-y-2", className)}
      {...props}
    >
      {children}
    </div>
  )
)
FormField.displayName = "FormField"

export { Form, FormField }
