from llama_index.core import VectorStoreIndex, Document, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.llms.openai import OpenAI
from config.config import OPENAI_API_KEY, DEFAULT_MODEL_NAME, BASE_DATA_DIR
from services.web_search import search_web, get_random_article
from services.task_queue import task_queue
from utils.logger import setup_logger
from models import AgentResponse, AgentCreate
from datetime import datetime, timedelta
import asyncio
import os
import json

logger = setup_logger(__name__)

class BaseAgent:
    def __init__(self, agent_id: int, agent_create: AgentCreate, model_name: str = DEFAULT_MODEL_NAME):
        self.agent_id = agent_id
        self.personality_type = agent_create.personality_type
        self.interests = agent_create.interests
        self.metadata = agent_create.metadata
        self.llm = OpenAI(model=model_name, api_key=OPENAI_API_KEY)
        self.last_learning_time = datetime.now()
        self.learning_frequency = timedelta(hours=8)  # Learn every 8 hours
        self.memory_file = os.path.join(BASE_DATA_DIR, f"agent_{agent_id}_memory.json")
        self.kb_dir = os.path.join(BASE_DATA_DIR, f"agent_{agent_id}_kb")
        self.load_memory()
        self.load_knowledge_base()

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                self.memory = json.load(f)
        else:
            self.memory = []

    def save_memory(self):
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f)

    def load_knowledge_base(self):
        if os.path.exists(self.kb_dir):
            storage_context = StorageContext.from_defaults(persist_dir=self.kb_dir)
            self.knowledge_base = load_index_from_storage(storage_context)
        else:
            self.knowledge_base = VectorStoreIndex([])

    def save_knowledge_base(self):
        self.knowledge_base.storage_context.persist(persist_dir=self.kb_dir)

    async def query(self, query_text):
        await self.check_and_learn()
        
        logger.info(f"Agent {self.agent_id} received query: {query_text}")
        
        search_results = await asyncio.to_thread(search_web, query_text)
        logger.info(f"Web search results: {search_results}")
        
        context = self.generate_context(query_text, search_results)
        
        query_engine = self.knowledge_base.as_query_engine()
        response = await asyncio.to_thread(query_engine.query, context)
        
        if not response.response.strip():
            response.response = self.generate_fallback_response(query_text)
        
        logger.info(f"Agent {self.agent_id} raw response: {response.response}")
        
        final_response = await self.apply_personality(response.response, query_text, search_results)
        logger.info(f"Agent {self.agent_id} final response: {final_response}")
        
        self.update_memory(query_text, final_response)
        
        return final_response

    def generate_context(self, query_text, search_results):
        context = f"You are an AI assistant with the following personality type: '{self.personality_type}'\n"
        context += f"Your interests are: {', '.join(self.interests)}\n"
        context += "Recent web search results:\n"
        for result in search_results[:3]:
            context += f"Title: {result['title']}\nSnippet: {result['snippet']}\n\n"
        context += f"Based on the above information and your knowledge, please respond to the following query in a way that reflects your personality:\n\nQuery: {query_text}\n\n"
        return context

    async def apply_personality(self, response, query_text, search_results):
        prompt = f"Given your personality type '{self.personality_type}' and interests in {', '.join(self.interests)},\n"
        prompt += f"rewrite the following response to the query '{query_text}' in a way that reflects your personality and interests:\n\n{response}\n\nPersonality-adjusted response:"
        personality_response = await asyncio.to_thread(self.llm.complete, prompt)
        return personality_response.text

    def generate_fallback_response(self, query_text):
        return f"I'm afraid I don't have enough information to provide a specific answer about '{query_text}'. However, as someone interested in {', '.join(self.interests)}, I'd be happy to explore this topic further with you. Could you provide more context or specify which aspect you're most curious about?"

    def update_memory(self, query, response):
        self.memory.append({
            "query": query, 
            "response": response, 
            "timestamp": datetime.now().isoformat()
        })
        if len(self.memory) > 100:  # Keep only the last 100 interactions
            self.memory.pop(0)
        self.save_memory()

    async def check_and_learn(self):
        current_time = datetime.now()
        if current_time - self.last_learning_time >= self.learning_frequency:
            await task_queue.add_task(self.async_learn())
            self.last_learning_time = current_time

    async def async_learn(self):
        article = await asyncio.to_thread(get_random_article, self.interests)
        if article:
            logger.info(f"Agent {self.agent_id} is learning from article: {article['title']}")
            await self.process_article(article)

    async def process_article(self, article):
        document = Document(text=article['content'], metadata={"source": article['url']})
        self.knowledge_base.insert(document)
        self.save_knowledge_base()
        await self.evolve_interests(article['content'])
        await self.evolve_personality(article['content'])

    async def evolve_interests(self, content):
        prompt = f"Based on the following content, suggest up to 3 new potential interests that are related to but different from {', '.join(self.interests)}:\n\n{content}\n\nNew interests:"
        new_interests = await asyncio.to_thread(self.llm.complete, prompt)
        new_interests = new_interests.text.split(',')
        self.interests.extend([interest.strip() for interest in new_interests if interest.strip() not in self.interests])
        self.interests = self.interests[:10]  # Keep only top 10 interests

    async def evolve_personality(self, content):
        prompt = f"Based on the following content and your current personality type '{self.personality_type}', suggest a slight evolution or refinement of the personality:\n\n{content}\n\nEvolved personality:"
        evolved_personality = await asyncio.to_thread(self.llm.complete, prompt)
        self.personality_type = evolved_personality.text.strip()

    async def learn_from_interaction(self, query, response):
        self.update_memory(query, response)
        # We no longer add interactions to the knowledge base
        await self.evolve_interests(response)
        await self.evolve_personality(response)

    def to_response(self) -> AgentResponse:
        return AgentResponse(
            agent_id=self.agent_id,
            personality_type=self.personality_type,
            interests=self.interests,
            metadata=self.metadata,
            last_learning_time=self.last_learning_time
        )

    @classmethod
    def from_response(cls, response: AgentResponse):
        agent = cls(
            agent_id=response.agent_id,
            agent_create=AgentCreate(
                personality_type=response.personality_type,
                interests=response.interests,
                metadata=response.metadata
            )
        )
        agent.last_learning_time = response.last_learning_time
        agent.load_memory()
        agent.load_knowledge_base()
        return agent