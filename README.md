# Physical AI & Humanoid Robotics Textbook

An interactive, AI-native textbook teaching Physical AI & Humanoid Robotics.

## Project Structure

This project has been reorganized into a professional full-stack structure:

```
BOOK/
├── website/                 # Docusaurus frontend (textbook content)
│   ├── docs/                # All textbook content organized by modules
│   │   ├── module1-ros2/    # ROS 2 fundamentals
│   │   ├── module2-gazebo-unity/ # Digital twin technologies
│   │   ├── module3-isaac/   # NVIDIA Isaac ecosystem
│   │   └── module4-vla/     # Voice-to-action and capstone projects
│   ├── src/                 # React components for the textbook
│   ├── static/              # Static assets (images, diagrams, examples)
│   ├── docusaurus.config.js # Main Docusaurus configuration
│   ├── sidebars.js          # Navigation structure
│   └── package.json         # Frontend dependencies
├── backend/                 # FastAPI backend for RAG implementation
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API routes for document management and querying
│   ├── db/                  # Database models
│   └── rag/                 # RAG-specific logic
├── rag/                     # Standalone RAG scripts
│   ├── ingest.py            # Document ingestion script
│   └── query.py             # Query testing script
├── specs/                   # Feature specifications and plans
└── history/                 # Prompt history records and ADRs
```

## Getting Started

### Frontend (Textbook)

To run the textbook locally:

```bash
cd website
npm install
npm start
```

The textbook will be available at http://localhost:3000.

### Backend (RAG Service)

To run the RAG backend service:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at http://localhost:8000, with interactive documentation at http://localhost:8000/docs.

### Standalone RAG Scripts

To use the standalone RAG scripts:

```bash
cd rag
pip install -r requirements.txt
python query.py --query "What is ROS 2?"
```

## Project Modules

The textbook is organized into 4 modules:

1. **Module 1: The Robotic Nervous System (ROS 2)** - Covers ROS 2 fundamentals and Python agents
2. **Module 2: The Digital Twin (Gazebo & Unity)** - Simulation technologies and transfer to reality
3. **Module 3: NVIDIA Isaac** - Isaac Sim, Isaac ROS, synthetic data, navigation, deployment
4. **Module 4: Voice-to-Action (VLA)** - Voice commands, LLM planning, capstone project

## Contributing

1. Clone the repository
2. Make changes to content in `website/docs/`
3. Test changes by running the development server with `npm start`
4. Submit a pull request

## License

[Add your license information here]