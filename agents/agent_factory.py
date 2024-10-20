import os
import json
from datetime import datetime
from agents.base_agent import BaseAgent
from config.config import BASE_DATA_DIR, DEFAULT_MODEL_NAME
from utils.logger import setup_logger
from models import AgentCreate, AgentUpdate, AgentResponse, AgentList

logger = setup_logger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class AgentFactory:
    def __init__(self, base_data_dir: str = BASE_DATA_DIR, model_name: str = DEFAULT_MODEL_NAME):
        self.base_data_dir = base_data_dir
        self.model_name = model_name
        self.agents = {}
        self.agents_file = os.path.join(base_data_dir, "agents.json")
        os.makedirs(base_data_dir, exist_ok=True)
        self.load_agents()

    def load_agents(self):
        if os.path.exists(self.agents_file):
            try:
                with open(self.agents_file, 'r') as f:
                    agents_data = json.load(f)
                for agent_data in agents_data:
                    agent_data['last_learning_time'] = datetime.fromisoformat(agent_data['last_learning_time'])
                    agent = BaseAgent.from_response(AgentResponse(**agent_data))
                    self.agents[agent.agent_id] = agent
            except json.JSONDecodeError:
                logger.error(f"Error decoding {self.agents_file}. Starting with empty agents list.")
                self.agents = {}
        else:
            logger.info(f"{self.agents_file} not found. Starting with empty agents list.")

    def save_agents(self):
        agents_data = [agent.to_response().dict() for agent in self.agents.values()]
        with open(self.agents_file, 'w') as f:
            json.dump(agents_data, f, cls=DateTimeEncoder)

    def create_agent(self, agent_create: AgentCreate) -> BaseAgent:
        agent_id = max(self.agents.keys() or [0]) + 1
        agent = BaseAgent(agent_id, agent_create, self.model_name)
        self.agents[agent_id] = agent
        self.save_agents()
        logger.info(f"Created agent {agent_id} with personality type: {agent_create.personality_type}")
        return agent

    def get_agent(self, agent_id: int) -> BaseAgent:
        return self.agents.get(agent_id)

    def list_agents(self) -> AgentList:
        return AgentList(agents=[agent.to_response() for agent in self.agents.values()])

    def update_agent(self, agent_id: int, agent_update: AgentUpdate):
        agent = self.get_agent(agent_id)
        if agent:
            if agent_update.interests is not None:
                agent.interests = agent_update.interests
            if agent_update.metadata is not None:
                agent.metadata.update(agent_update.metadata)
            self.save_agents()
            logger.info(f"Updated agent {agent_id}")
        else:
            logger.error(f"Agent {agent_id} not found")

    def delete_agent(self, agent_id: int):
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.save_agents()
            logger.info(f"Deleted agent {agent_id}")
        else:
            logger.error(f"Agent {agent_id} not found")