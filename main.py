from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from agents.agent_factory import AgentFactory
from utils.logger import setup_logger
from models import AgentCreate, AgentUpdate, AgentResponse, Query, QueryResponse, AgentList
from services.task_queue import task_queue
import asyncio
import nltk
import ssl

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create background tasks and initialize NLTK
    task_queue_task = asyncio.create_task(task_queue.run())
    
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    try:
        nltk.download('punkt', quiet=True)
    except Exception as e:
        logger.warning(f"Failed to download NLTK data: {str(e)}")
        logger.warning("NLTK tokenization might not work properly.")
    
    yield
    
    # Shutdown: cancel background tasks
    task_queue_task.cancel()
    try:
        await task_queue_task
    except asyncio.CancelledError:
        logger.info("Task queue has been shut down")

app = FastAPI(lifespan=lifespan)
agent_factory = AgentFactory()

@app.post("/agents", response_model=AgentResponse)
async def create_agent(agent_create: AgentCreate):
    agent = agent_factory.create_agent(agent_create)
    return agent.to_response()

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int):
    agent = agent_factory.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.to_response()

@app.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, agent_update: AgentUpdate):
    agent_factory.update_agent(agent_id, agent_update)
    agent = agent_factory.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.to_response()

@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: int):
    agent_factory.delete_agent(agent_id)
    return {"message": "Agent deleted successfully"}

@app.post("/query/{agent_id}", response_model=QueryResponse)
async def query_agent(agent_id: int, query: Query):
    agent = agent_factory.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    response = await agent.query(query.query)
    return QueryResponse(
        agent_id=agent_id,
        personality_type=agent.personality_type,
        interests=agent.interests,
        query=query.query,
        response=response
    )

@app.get("/agents", response_model=AgentList)
async def list_agents():
    return agent_factory.list_agents()

@app.post("/agents/{agent_id}/learn")
async def trigger_agent_learning(agent_id: int):
    agent = agent_factory.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await task_queue.add_task(agent.async_learn())
    return {"message": f"Learning task for agent {agent_id} has been queued"}

@app.post("/agents/{agent_id}/interact/{target_agent_id}")
async def agent_interaction(agent_id: int, target_agent_id: int):
    agent = agent_factory.get_agent(agent_id)
    target_agent = agent_factory.get_agent(target_agent_id)
    if not agent or not target_agent:
        raise HTTPException(status_code=404, detail="One or both agents not found")
    
    shared_interests = set(agent.interests) & set(target_agent.interests)
    if shared_interests:
        interest = list(shared_interests)[0]
        query = f"What's the latest development in {interest}?"
        response = await agent.query(query)
        await target_agent.learn_from_interaction(query, response)
        return {"message": f"Agents {agent_id} and {target_agent_id} exchanged knowledge about {interest}"}
    else:
        return {"message": "No shared interests found for knowledge exchange"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)