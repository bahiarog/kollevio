import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="owner")  # owner | member
    created_at = Column(DateTime, server_default=func.now())


class AgentRole(Base):
    __tablename__ = "agent_roles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    tagline = Column(String(500))
    description = Column(Text)
    system_prompt = Column(Text)
    color_accent = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())


class TenantAgent(Base):
    __tablename__ = "tenant_agents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    agent_role_id = Column(UUID(as_uuid=True), ForeignKey("agent_roles.id"), nullable=False)
    custom_name = Column(String(255))
    avatar_seed = Column(String(100))
    hired_at = Column(DateTime, server_default=func.now())


class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_agent_id = Column(UUID(as_uuid=True), ForeignKey("tenant_agents.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())


class AgentMessage(Base):
    __tablename__ = "agent_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("agent_conversations.id"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # user | agent
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
