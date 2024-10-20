from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class AgentCreate(BaseModel):
    personality_type: str
    interests: List[str]
    metadata: Dict[str, str]

class AgentUpdate(BaseModel):
    interests: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None

class AgentResponse(BaseModel):
    agent_id: int
    personality_type: str
    interests: List[str]
    metadata: Dict[str, str]
    last_learning_time: datetime

class Query(BaseModel):
    query: str

class QueryResponse(BaseModel):
    agent_id: int
    personality_type: str
    interests: List[str]
    query: str
    response: str

class AgentList(BaseModel):
    agents: List[AgentResponse]