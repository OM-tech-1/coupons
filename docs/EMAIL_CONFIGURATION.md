# Email Configuration Guide

This guide explains how to configure email sending for OTP (password reset) and other notifications in VoucherGalaxy.

## Required Environment Variables

Add these to your `.env` file:

```env
# Email/SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@vouchergalaxy.com
FROM_NAME=VoucherGalaxy

# Frontend URL for Password Reset
FRONTEND_RESET_URL=https://frontend.vouchergalaxy.com/reset-password
```

## Configuration Options

### 1. Gmail (Recommended for Development)

**Setup Steps:**
1. Use a Gmail account
2. Enable 2-Factor Authentication
3. Generate an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
4. Use the generated password (not your regular Gmail password)

**Configuration:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=VoucherGalaxy
```

**Limitations:**
- 500 emails per day limit
- May be flagged as spam
- Not recommended for production

### 2. SendGrid (Recommended for Production)

**Setup Steps:**
1. Sign up at https://sendgrid.com
2. Verify your sender identity/domain
3. Create an API key

**Configuration:**
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@vouchergalaxy.com
FROM_NAME=VoucherGalaxy
```

**Benefits:**
- 100 emails/day free tier
- Better deliverability
- Email analytics
- Domain authentication

### 3. AWS SES (Best for Production)

**Setup Steps:**
1. Enable AWS SES in your AWS account
2. Verify your domain or email
3. Create SMTP credentials
4. Move out of sandbox mode (for production)

**Configuration:**
```env
SMTP_HOST=email-smtp.ap-southeast-2.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
FROM_EMAIL=noreply@vouchergalaxy.com
FROM_NAME=VoucherGalaxy
```

**Benefits:**
- Very low cost ($0.10 per 1000 emails)
- High deliverability
- Scales automatically
- Integrates with AWS ecosystem

### 4. Mailgun

**Configuration:**
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-password
FROM_EMAIL=noreply@vouchergalaxy.com
FROM_NAME=VoucherGalaxy
```

### 5. Office 365 / Outlook

**Configuration:**
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
FROM_EMAIL=your-email@outlook.com
FROM_NAME=VoucherGalaxy
```

## Environment Variable Details

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SMTP_HOST` | Yes | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | No | SMTP port (default: 587) | `587` |
| `SMTP_USER` | Yes | SMTP username/email | `user@gmail.com` |
| `SMTP_PASSWORD` | Yes | SMTP password/API key | `app-password-here` |
| `FROM_EMAIL` | Yes | Sender email address | `noreply@vouchergalaxy.com` |
| `FROM_NAME` | No | Sender display name | `VoucherGalaxy` |
| `FRONTEND_RESET_URL` | Yes | URL for password reset page | `https://site.com/reset-password` |

## Testing Email Configuration

### 1. Test with Python Script

Create a test file `test_email.py`:

```python
import asyncio
from app.utils.email import send_reset_email

async def test():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    result = await send_reset_email("test@example.com", token)
    print(f"Email sent: {result}")

if __name__ == "__main__":
    asyncio.run(test())
```

Run:
```bash
python test_email.py
```

### 2. Test via API

Use the forgot password endpoint:

```bash
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### 3. Check Logs

Monitor application logs for email sending errors:
```bash
docker logs -f container_name | grep -i email
```

## Troubleshooting

### Common Issues

**1. Authentication Failed**
- Verify SMTP_USER and SMTP_PASSWORD are correct
- For Gmail: Use App Password, not regular password
- Check if 2FA is enabled (required for Gmail)

**2. Connection Timeout**
- Verify SMTP_HOST and SMTP_PORT
- Check firewall/network settings
- Try port 465 (SSL) instead of 587 (TLS)

**3. Emails Going to Spam**
- Set up SPF, DKIM, and DMARC records
- Use a verified domain
- Avoid spam trigger words
- Use a reputable email service

**4. SSL/TLS Errors**
- Current config uses STARTTLS (port 587)
- For SSL (port 465), update email.py:
  ```python
  MAIL_STARTTLS=False,
  MAIL_SSL_TLS=True,
  ```

### Debug Mode

To see detailed SMTP logs, modify `app/utils/email.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Recommendations

1. **Use a dedicated email service** (SendGrid, AWS SES, Mailgun)
2. **Verify your domain** for better deliverability
3. **Set up SPF/DKIM/DMARC** records
4. **Monitor email metrics** (delivery rate, bounces, spam reports)
5. **Use environment-specific configs**:
   - Development: Gmail with app password
   - Staging: SendGrid free tier
   - Production: AWS SES or SendGrid paid tier
6. **Implement rate limiting** to prevent abuse
7. **Add email templates** for better branding
8. **Log all email attempts** for debugging

## Security Best Practices

1. Never commit `.env` file with real credentials
2. Use different SMTP credentials for each environment
3. Rotate SMTP passwords regularly
4. Use API keys instead of passwords when possible
5. Enable 2FA on email service accounts
6. Monitor for suspicious email activity
7. Implement rate limiting on password reset endpoints

## Email Templates

Current password reset email template is in `app/utils/email.py`. It includes a dynamic magic link:

```python
reset_link = f"{FRONTEND_RESET_URL}?token={token}"
html = f"""
<html>
    <body style="font-family: 'Inter', sans-serif; background-color: #f9fafb;">
        <div style="max-width: 600px; margin: 40px auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h2 style="color: #111827; margin-bottom: 24px;">Password Reset Request</h2>
            <p style="color: #4b5563; line-height: 1.6;">You requested to reset your password. Click the button below to set a new password. This link is valid for 15 minutes and can only be used once.</p>
            <div style="text-align: center; margin: 32px 0;">
                <a href="{reset_link}" style="background-color: #2563eb; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block;">Reset Password</a>
            </div>
            <p style="color: #9ca3af; font-size: 14px;">If you didn't request this, you can safely ignore this email.</p>
        </div>
    </body>
</html>
"""
```

## Cost Comparison

| Service | Free Tier | Paid Pricing | Best For |
|---------|-----------|--------------|----------|
| Gmail | 500/day | N/A | Development only |
| SendGrid | 100/day | $19.95/mo (50K) | Small-medium apps |
| AWS SES | 62K/mo (from EC2) | $0.10/1000 | High volume |
| Mailgun | 5K/mo | $35/mo (50K) | Medium apps |
| Postmark | 100/mo | $15/mo (10K) | Transactional |

## Next Steps

1. Choose an email service provider
2. Add credentials to `.env` file
3. Test with the forgot password endpoint
4. Monitor email delivery in production
5. Set up domain authentication (SPF/DKIM)
6. Configure email templates for branding
