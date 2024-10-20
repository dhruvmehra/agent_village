# AI Agent System with Image Understanding

This project implements a multi-agent AI system capable of processing both text and image inputs. Each agent has its own personality, interests, and knowledge base, and can learn and evolve over time.

## Features

- Multiple AI agents with distinct personalities and interests
- Text and image query processing
- Web search integration for up-to-date information
- Continuous learning and knowledge base updates
- Inter-agent knowledge exchange
- Asynchronous task queue for managing learning processes

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/ai-agent-system.git
   cd ai-agent-system
   ```

2. Create a virtual environment and activate it:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key:
   Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Start the FastAPI server:

   ```
   uvicorn app.main:app --reload
   ```

2. Create an agent:

   ```
   curl -X POST "http://127.0.0.1:8000/agents" \
        -H "Content-Type: application/json" \
        -d '{
          "personality_type": "Curious and enthusiastic tech enthusiast",
          "interests": ["artificial intelligence", "space exploration", "quantum computing"],
          "metadata": {"creation_date": "2023-06-01", "creator": "Admin"}
        }'
   ```

3. Query an agent with text:

   ```
   curl -X POST "http://127.0.0.1:8000/query/1" \
        -H "Content-Type: application/json" \
        -d '{"query": "What are the latest developments in AI?"}'
   ```

4. Query an agent with text and image:

   ```
   curl -X POST "http://127.0.0.1:8000/query/1" \
        -H "Content-Type: multipart/form-data" \
        -F "query={\"query\": \"What can you tell me about this image?\"}" \
        -F "image=@path/to/your/image.jpg"
   ```

5. Trigger agent learning:

   ```
   curl -X POST "http://127.0.0.1:8000/agents/1/learn"
   ```

6. Initiate agent interaction:
   ```
   curl -X POST "http://127.0.0.1:8000/agents/1/interact/2"
   ```

## Project Structure

- `app/`: Main application directory
  - `main.py`: FastAPI application and routes
  - `models.py`: Pydantic models for data validation
  - `agents/`: Agent-related modules
    - `base_agent.py`: BaseAgent class implementation
    - `agent_factory.py`: AgentFactory for managing agents
  - `services/`: Service modules
    - `web_search.py`: Web search functionality
    - `image_processor.py`: Image processing using ViT
    - `task_queue.py`: Asynchronous task queue
  - `utils/`: Utility modules
    - `logger.py`: Logging configuration
- `data/`: Directory for storing agent data
- `requirements.txt`: Project dependencies
- `.env`: Environment variables (not in version control)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
