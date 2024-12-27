from sqlalchemy import Column, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    saved_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create database and tables
engine = create_engine("sqlite:///./rag.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)