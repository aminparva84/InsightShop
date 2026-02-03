"""Model for storing AI assistant / agent API configurations (admin-configured)."""
from models.database import db
from datetime import datetime


class AiAssistantConfig(db.Model):
    """Stores AI agent API configurations set by the admin. The chatbot uses the active config."""
    __tablename__ = 'ai_assistant_configs'

    id = db.Column(db.Integer, primary_key=True)
    # Display name for this configuration (e.g. "Production Claude", "OpenAI GPT-4")
    name = db.Column(db.String(255), nullable=False, default='AI Assistant')
    # Provider: 'bedrock' | 'openai' | 'custom'
    provider = db.Column(db.String(50), nullable=False, default='bedrock')
    # API key (stored as-is; use env or secrets manager in production for extra security)
    api_key = db.Column(db.String(1024), nullable=True)
    # For custom agent: API base URL / endpoint
    api_endpoint = db.Column(db.String(1024), nullable=True)
    # Model identifier (e.g. anthropic.claude-3-sonnet-..., gpt-4)
    model_id = db.Column(db.String(255), nullable=True)
    # AWS region (for Bedrock)
    region = db.Column(db.String(64), nullable=True)
    # Only one config should be active at a time; the chatbot uses this one
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self, mask_secrets=True):
        """Serialize for API. By default mask api_key for listing."""
        return {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'api_key': '••••••••' if (self.api_key and mask_secrets) else self.api_key,
            'api_endpoint': self.api_endpoint,
            'model_id': self.model_id,
            'region': self.region,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_internal_dict(self):
        """Full dict for server-side use (includes real api_key)."""
        return {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'api_key': self.api_key,
            'api_endpoint': self.api_endpoint,
            'model_id': self.model_id,
            'region': self.region,
            'is_active': self.is_active,
        }
