"""External messaging services for email and SMS."""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from ..core.config import config
from ..core.exceptions import SystemError


class EmailService:
    """Email service for sending notifications."""
    
    def __init__(self):
        self.smtp_host = config.smtp_host
        self.smtp_port = config.smtp_port
        self.smtp_username = config.smtp_username
        self.smtp_password = config.smtp_password
        self.smtp_use_tls = config.smtp_use_tls
        self.from_email = config.email_from
        self.from_name = config.email_from_name
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """Send an email."""
        if not self.smtp_host:
            raise SystemError("SMTP not configured")
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name or self.from_name} <{from_email or self.from_email}>"
            msg['To'] = to_email
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls(context=context)
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            raise SystemError(f"Failed to send email: {str(e)}")
    
    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
        tenant_name: str = "WindWays"
    ) -> bool:
        """Send email verification email."""
        subject = f"Verify your email address - {tenant_name}"
        
        verification_url = f"https://app.windways.com/verify-email?token={verification_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to {tenant_name}!</h2>
            <p>Please click the link below to verify your email address:</p>
            <p><a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to {tenant_name}!
        
        Please click the link below to verify your email address:
        {verification_url}
        
        This link will expire in 24 hours.
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        tenant_name: str = "WindWays"
    ) -> bool:
        """Send password reset email."""
        subject = f"Reset your password - {tenant_name}"
        
        reset_url = f"https://app.windways.com/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password for {tenant_name}.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}" style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        You requested to reset your password for {tenant_name}.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_mfa_code_email(
        self,
        to_email: str,
        mfa_code: str,
        tenant_name: str = "WindWays"
    ) -> bool:
        """Send MFA code via email."""
        subject = f"Your verification code - {tenant_name}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Verification Code</h2>
            <p>Your verification code for {tenant_name} is:</p>
            <h1 style="color: #007bff; font-size: 32px; letter-spacing: 5px;">{mfa_code}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Verification Code
        
        Your verification code for {tenant_name} is: {mfa_code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this, please ignore this email.
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_booking_confirmation_email(
        self,
        to_email: str,
        booking_reference: str,
        hotel_name: str,
        check_in: str,
        check_out: str,
        guests: int,
        rooms: int,
        total_price: str,
        currency: str = "USD",
        guest_name: str = "Guest",
        tenant_name: str = "Aero Hotels"
    ) -> bool:
        """Send booking confirmation email to user."""
        subject = f"Booking Confirmation - {booking_reference}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
                    Booking Confirmation
                </h2>
                
                <p>Dear {guest_name},</p>
                
                <p>Thank you for booking with {tenant_name}! Your booking has been received and is being processed.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #007bff;">Booking Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0;"><strong>Booking Reference:</strong></td>
                            <td style="padding: 8px 0;">{booking_reference}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>Hotel:</strong></td>
                            <td style="padding: 8px 0;">{hotel_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>Check-in:</strong></td>
                            <td style="padding: 8px 0;">{check_in}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>Check-out:</strong></td>
                            <td style="padding: 8px 0;">{check_out}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>Guests:</strong></td>
                            <td style="padding: 8px 0;">{guests}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>Rooms:</strong></td>
                            <td style="padding: 8px 0;">{rooms}</td>
                        </tr>
                        <tr style="border-top: 2px solid #007bff;">
                            <td style="padding: 12px 0;"><strong>Total Price:</strong></td>
                            <td style="padding: 12px 0; font-size: 18px; color: #007bff;"><strong>{currency} {total_price}</strong></td>
                        </tr>
                    </table>
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #856404;">Next Steps</h4>
                    <p style="margin: 5px 0;">The hotel will receive your booking request shortly. They will contact you directly to confirm availability and provide payment instructions.</p>
                    <p style="margin: 5px 0;">Please keep this booking reference for your records: <strong>{booking_reference}</strong></p>
                </div>
                
                <p>If you have any questions or need to make changes to your booking, please contact us with your booking reference.</p>
                
                <p style="margin-top: 30px;">
                    Best regards,<br>
                    <strong>The {tenant_name} Team</strong>
                </p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Booking Confirmation
        
        Dear {guest_name},
        
        Thank you for booking with {tenant_name}! Your booking has been received and is being processed.
        
        BOOKING DETAILS:
        Booking Reference: {booking_reference}
        Hotel: {hotel_name}
        Check-in: {check_in}
        Check-out: {check_out}
        Guests: {guests}
        Rooms: {rooms}
        Total Price: {currency} {total_price}
        
        NEXT STEPS:
        The hotel will receive your booking request shortly. They will contact you directly to confirm availability and provide payment instructions.
        
        Please keep this booking reference for your records: {booking_reference}
        
        If you have any questions or need to make changes to your booking, please contact us with your booking reference.
        
        Best regards,
        The {tenant_name} Team
        
        ---
        This is an automated message. Please do not reply to this email.
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)


class SMSService:
    """SMS service for sending verification codes."""
    
    def __init__(self):
        self.provider = config.sms_provider
        self.api_key = config.sms_api_key
        self.api_secret = config.sms_api_secret
    
    async def send_sms(
        self,
        to_phone: str,
        message: str
    ) -> bool:
        """Send SMS message."""
        if not self.provider or not self.api_key:
            raise SystemError("SMS not configured")
        
        try:
            if self.provider == "twilio":
                return await self._send_twilio_sms(to_phone, message)
            elif self.provider == "aws_sns":
                return await self._send_aws_sns_sms(to_phone, message)
            else:
                raise SystemError(f"Unsupported SMS provider: {self.provider}")
                
        except Exception as e:
            raise SystemError(f"Failed to send SMS: {str(e)}")
    
    async def _send_twilio_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS via Twilio."""
        try:
            from twilio.rest import Client
            
            client = Client(self.api_key, self.api_secret)
            message = client.messages.create(
                body=message,
                from_=config.sms_from_number,  # Would need to add this to config
                to=to_phone
            )
            
            return message.status in ['queued', 'sent', 'delivered']
            
        except ImportError:
            raise SystemError("Twilio library not installed")
    
    async def _send_aws_sns_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS via AWS SNS."""
        try:
            import boto3
            
            sns = boto3.client(
                'sns',
                aws_access_key_id=self.api_key,
                aws_secret_access_key=self.api_secret
            )
            
            response = sns.publish(
                PhoneNumber=to_phone,
                Message=message
            )
            
            return response['ResponseMetadata']['HTTPStatusCode'] == 200
            
        except ImportError:
            raise SystemError("Boto3 library not installed")
    
    async def send_mfa_code_sms(
        self,
        to_phone: str,
        mfa_code: str,
        tenant_name: str = "WindWays"
    ) -> bool:
        """Send MFA code via SMS."""
        message = f"Your {tenant_name} verification code is: {mfa_code}. This code expires in 10 minutes."
        return await self.send_sms(to_phone, message)
