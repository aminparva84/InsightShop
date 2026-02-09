"""Models for AI assistant: 3 fixed providers (OpenAI, Gemini, Anthropic) and selected model. All use simple API keys."""
from models.database import db
from datetime import datetime

# Exactly 3 fixed providers. One row per provider. All use simple API keys from Admin panel.
FIXED_PROVIDERS = ('openai', 'gemini', 'anthropic')
PROVIDER_DISPLAY_NAMES = {
    'openai': 'OpenAI',
    'gemini': 'Google Gemini',
    'anthropic': 'Anthropic',
}
# SDK label shown in admin table (can be overridden per row if we add sdk column later)
PROVIDER_SDK = {
    'openai': 'REST API',
    'gemini': 'REST API',
    'anthropic': 'REST API',
}


class AiAssistantConfig(db.Model):
    """One row per fixed provider. Stores API key, validity, last test time."""
    __tablename__ = 'ai_assistant_configs'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False, unique=True)  # openai, gemini, anthropic
    name = db.Column(db.String(255), nullable=False)  # display name
    sdk = db.Column(db.String(64), nullable=True)  # e.g. REST API, AWS SDK
    api_key = db.Column(db.String(1024), nullable=True)  # from admin; empty = use env
    model_id = db.Column(db.String(255), nullable=True)
    region = db.Column(db.String(64), nullable=True)  # optional, e.g. for future providers
    source = db.Column(db.String(20), nullable=False, default='env')  # 'admin' | 'env'
    is_valid = db.Column(db.Boolean, default=False, nullable=False)  # from last test
    is_enabled = db.Column(db.Boolean, default=False, nullable=False)  # admin can enable/disable; off when no valid key
    last_tested_at = db.Column(db.DateTime, nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self, mask_secrets=True):
        return {
            'id': self.id,
            'provider': self.provider,
            'name': self.name or PROVIDER_DISPLAY_NAMES.get(self.provider, self.provider),
            'sdk': self.sdk or PROVIDER_SDK.get(self.provider, 'REST API'),
            'api_key': '••••••••' if (self.api_key and mask_secrets) else (self.api_key or ''),
            'model_id': self.model_id,
            'region': self.region,
            'source': self.source,
            'is_valid': self.is_valid,
            'is_enabled': self.is_enabled,
            'last_tested_at': self.last_tested_at.isoformat() if self.last_tested_at else None,
            'latency_ms': self.latency_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_internal_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'name': self.name,
            'sdk': self.sdk,
            'api_key': self.api_key,
            'model_id': self.model_id,
            'region': self.region,
            'source': self.source,
            'is_valid': self.is_valid,
            'is_enabled': self.is_enabled,
            'last_tested_at': self.last_tested_at,
            'latency_ms': self.latency_ms,
        }


class AISelectedProvider(db.Model):
    """Single row: which provider the chatbot uses. Default 'auto'."""
    __tablename__ = 'ai_selected_provider'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(20), nullable=False, default='auto')  # auto, openai, gemini, anthropic
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
