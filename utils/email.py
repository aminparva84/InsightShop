import boto3
from botocore.exceptions import ClientError
from config import Config
from datetime import datetime
import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid, formatdate
import os

ses_client = boto3.client('ses', region_name=Config.AWS_REGION) if Config.AWS_REGION else None

# WorkMail SMTP Configuration
WORKMAIL_SMTP_SERVER = os.getenv('WORKMAIL_SMTP_SERVER', 'smtp.mail.us-east-1.awsapps.com')
WORKMAIL_SMTP_PORT = int(os.getenv('WORKMAIL_SMTP_PORT', '465'))
WORKMAIL_SMTP_USERNAME = os.getenv('WORKMAIL_SMTP_USERNAME', '')
WORKMAIL_SMTP_PASSWORD = os.getenv('WORKMAIL_SMTP_PASSWORD', '')
USE_WORKMAIL = os.getenv('USE_WORKMAIL', 'true').lower() == 'true'

def escape_html(text: str) -> str:
    """Escape HTML characters."""
    return html.escape(str(text))

def send_email_via_workmail(to: str, subject: str, html_body: str, text_body: str = None, reply_to: str = None) -> bool:
    """Send email via WorkMail SMTP."""
    if not WORKMAIL_SMTP_PASSWORD:
        print("ERROR: WORKMAIL_SMTP_PASSWORD not set in environment variables")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr(('InsightShop', Config.FROM_EMAIL))
        msg['To'] = to
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain='insightshop.com')
        msg['Reply-To'] = reply_to if reply_to else Config.FROM_EMAIL
        
        if text_body:
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            msg.attach(text_part)
        
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        if WORKMAIL_SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(WORKMAIL_SMTP_SERVER, WORKMAIL_SMTP_PORT)
        else:
            server = smtplib.SMTP(WORKMAIL_SMTP_SERVER, WORKMAIL_SMTP_PORT)
            server.starttls()
        
        server.login(WORKMAIL_SMTP_USERNAME, WORKMAIL_SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f'Email sent successfully via WorkMail to {to}')
        return True
    except Exception as e:
        print(f"Error sending email via WorkMail: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_email_via_ses(to: str, subject: str, html_body: str, text_body: str = None, reply_to: str = None) -> bool:
    """Send email via AWS SES."""
    if not ses_client:
        print("ERROR: SES client not initialized")
        return False
    
    try:
        message = {
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': {'Html': {'Data': html_body, 'Charset': 'UTF-8'}}
        }
        
        if text_body:
            message['Body']['Text'] = {'Data': text_body, 'Charset': 'UTF-8'}
        
        from_email = formataddr(('InsightShop', Config.FROM_EMAIL))
        
        params = {
            'Source': from_email,
            'Destination': {'ToAddresses': [to]},
            'Message': message
        }
        
        if reply_to:
            params['ReplyToAddresses'] = [reply_to]
        else:
            params['ReplyToAddresses'] = [Config.FROM_EMAIL]
        
        ses_client.send_email(**params)
        print(f'Email sent successfully via SES to {to}')
        return True
    except ClientError as e:
        print(f"Error sending email via SES: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error sending email via SES: {e}")
        return False

def send_email(to: str, subject: str, html_body: str, text_body: str = None, reply_to: str = None) -> bool:
    """Send email via WorkMail SMTP (preferred) or AWS SES (fallback)."""
    if USE_WORKMAIL:
        result = send_email_via_workmail(to, subject, html_body, text_body, reply_to)
        if not result:
            print("WorkMail failed, trying SES as fallback...")
            return send_email_via_ses(to, subject, html_body, text_body, reply_to)
        return result
    else:
        return send_email_via_ses(to, subject, html_body, text_body, reply_to)

def send_order_confirmation_email(email: str, name: str, order) -> bool:
    """Send order confirmation email with receipt."""
    order_items_html = ''
    order_items_text = ''
    
    for item in order.items:
        product_name = item.product.name if item.product else 'Product'
        order_items_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{escape_html(product_name)}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center;">{item.quantity}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">${float(item.price):.2f}</td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">${float(item.price * item.quantity):.2f}</td>
        </tr>
        """
        order_items_text += f"{product_name} x {item.quantity} - ${float(item.price * item.quantity):.2f}\n"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #ec4899 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .header h2 {{ margin: 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            .order-info {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .order-info h3 {{ margin-top: 0; color: #7c3aed; }}
            table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }}
            th {{ background: #f3f4f6; padding: 12px; text-align: left; font-weight: 600; color: #374151; }}
            .total-row {{ font-weight: 700; font-size: 18px; background: #f9fafb; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Order Confirmation</h2>
                <p>Thank you for your purchase!</p>
            </div>
            <div class="content">
                <p>Hi {escape_html(name)},</p>
                <p>Your order has been confirmed and will be processed shortly.</p>
                
                <div class="order-info">
                    <h3>Order Details</h3>
                    <p><strong>Order Number:</strong> {order.order_number}</p>
                    <p><strong>Order Date:</strong> {order.created_at.strftime('%B %d, %Y at %I:%M %p') if order.created_at else 'N/A'}</p>
                    <p><strong>Status:</strong> {order.status.capitalize()}</p>
                </div>
                
                <h3 style="color: #7c3aed; margin-top: 30px;">Order Items</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th style="text-align: center;">Quantity</th>
                            <th style="text-align: right;">Price</th>
                            <th style="text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {order_items_html}
                        <tr class="total-row">
                            <td colspan="3" style="padding: 12px; text-align: right;"><strong>Subtotal:</strong></td>
                            <td style="padding: 12px; text-align: right;">${float(order.subtotal):.2f}</td>
                        </tr>
                        <tr>
                            <td colspan="3" style="padding: 12px; text-align: right;">Tax:</td>
                            <td style="padding: 12px; text-align: right;">${float(order.tax):.2f}</td>
                        </tr>
                        <tr>
                            <td colspan="3" style="padding: 12px; text-align: right;">Shipping:</td>
                            <td style="padding: 12px; text-align: right;">${float(order.shipping_cost):.2f}</td>
                        </tr>
                        <tr class="total-row">
                            <td colspan="3" style="padding: 12px; text-align: right;"><strong>Total:</strong></td>
                            <td style="padding: 12px; text-align: right;"><strong>${float(order.total):.2f}</strong></td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="order-info" style="margin-top: 20px;">
                    <h3>Shipping Address</h3>
                    <p>{escape_html(order.shipping_name)}<br>
                    {escape_html(order.shipping_address)}<br>
                    {escape_html(order.shipping_city)}, {escape_html(order.shipping_state)} {escape_html(order.shipping_zip)}<br>
                    {escape_html(order.shipping_country)}</p>
                </div>
                
                <div class="footer">
                    <p>This is your order confirmation and receipt.</p>
                    <p>If you have any questions, please contact us at {Config.ADMIN_EMAIL}</p>
                    <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
Order Confirmation - InsightShop
================================

Hi {name},

Your order has been confirmed and will be processed shortly.

Order Details:
- Order Number: {order.order_number}
- Order Date: {order.created_at.strftime('%B %d, %Y at %I:%M %p') if order.created_at else 'N/A'}
- Status: {order.status.capitalize()}

Order Items:
{order_items_text}

Subtotal: ${float(order.subtotal):.2f}
Tax: ${float(order.tax):.2f}
Shipping: ${float(order.shipping_cost):.2f}
Total: ${float(order.total):.2f}

Shipping Address:
{order.shipping_name}
{order.shipping_address}
{order.shipping_city}, {order.shipping_state} {order.shipping_zip}
{order.shipping_country}

This is your order confirmation and receipt.
If you have any questions, please contact us at {Config.ADMIN_EMAIL}

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}
    """.strip()
    
    return send_email(email, f'Order Confirmation - {order.order_number}', html_body, text_body)

def send_activation_email(email: str, first_name: str, activation_token: str) -> bool:
    """Send account activation email."""
    activation_link = f"{Config.BASE_URL}/activation?verify={activation_token}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #ec4899 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .header h2 {{ margin: 0; }}
            .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #7c3aed; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Welcome to InsightShop!</h2>
                <p>Account Activation</p>
            </div>
            <div class="content">
                <p>Hi {escape_html(first_name)},</p>
                <p>Thank you for registering! Please click the button below to activate your account:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{activation_link}" class="button">Click Here to Activate Your Account</a>
                </div>
                <p style="text-align: center; color: #6b7280; font-size: 14px;">This link will expire in 24 hours.</p>
                <div class="footer">
                    <p>This email was sent from InsightShop</p>
                    <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
Welcome to InsightShop!
======================

Hi {first_name},

Thank you for registering! Please activate your account by clicking the link below:

Click here to activate: {activation_link}

This link will expire in 24 hours.

---
This email was sent from InsightShop
Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}
    """.strip()
    
    return send_email(email, 'Activate Your Account - InsightShop', html_body, text_body)
