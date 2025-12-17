# Quickstart: Project Folder Structure Reorganization

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)
- Python (v3.8 or higher)
- Git

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Navigate to the Website Directory
```bash
cd website
```

### 3. Install Docusaurus Dependencies
```bash
npm install
```

### 4. Start the Development Server
```bash
npm start
```

This will start the Docusaurus development server and open the textbook in your browser at http://localhost:3000.

### 5. Explore the Backend Structure
The backend/ directory contains a FastAPI skeleton structure for future RAG implementation:

```bash
cd ../backend
ls -la
```

To run the FastAPI development server:
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### 6. Check the RAG Scripts
The rag/ directory contains placeholder scripts for future implementation:

```bash
cd ../rag
ls -la
```

## Key Directories

- `website/docs/` - Contains all textbook content organized by modules
- `website/src/` - Contains custom React components for the textbook
- `website/static/` - Contains diagrams, images, and code examples
- `backend/` - Contains the FastAPI structure for future RAG implementation
- `rag/` - Contains standalone scripts for RAG functionality

## Building for Production

To build the static site for production:

```bash
cd website
npm run build
```

The built site will be available in the `build/` directory.