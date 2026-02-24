"""Contact form API: submit inquiry and email to support."""

from flask import Blueprint, request, jsonify
from config import Config
from utils.email import send_email, escape_html

contact_bp = Blueprint('contact', __name__)


@contact_bp.route('', methods=['POST'])
def submit_contact():
    """Accept contact form submission and email to support."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    order_number = (data.get('order_number') or '').strip()
    message = (data.get('message') or '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    if not message:
        return jsonify({'error': 'Message is required'}), 400

    to_email = Config.ADMIN_EMAIL or Config.FROM_EMAIL
    subject = f'Contact form: {escape_html(name)}'
    order_line = f'<p><strong>Order number:</strong> {escape_html(order_number)}</p>' if order_number else ''
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <p><strong>From:</strong> {escape_html(name)} &lt;{escape_html(email)}&gt;</p>
        {order_line}
        <p><strong>Message:</strong></p>
        <p>{escape_html(message).replace(chr(10), '<br>')}</p>
    </body>
    </html>
    """
    text_body = f"From: {name} <{email}>\n"
    if order_number:
        text_body += f"Order number: {order_number}\n"
    text_body += f"\nMessage:\n{message}"

    sent = send_email(to_email, subject, html_body, text_body=text_body, reply_to=email)
    if not sent:
        return jsonify({'error': 'Unable to send message. Please try again later.'}), 503

    return jsonify({'success': True}), 200
