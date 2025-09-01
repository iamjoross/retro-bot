# Dutch Tutor Assistant

A full-stack AI-powered conversational assistant built with modern web technologies and containerized for easy deployment.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed on your system

### Running the Application

1. Clone the repository
2. Copy environment files:
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   ```
3. Start the entire stack:
   ```bash
   docker-compose up --build
   ```

The application will be available at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **MongoDB**: localhost:27017

## 🏗️ Architecture & Technologies

### Backend

- **FastAPI** - Modern Python web framework with automatic API documentation
- **Python 3.11** - Latest stable Python version
- **Pydantic** - Data validation and settings management
- **Motor/PyMongo** - Async MongoDB driver
- **Transformers/Torch** - Hugging Face AI model integration
- **TinyLlama** - 1.1B parameter chat model for local inference

### Frontend

- **Next.js 15** - React framework with App Router
- **React 19** - Latest React with concurrent features
- **TypeScript** - Type-safe JavaScript
- **TanStack Query** - Server state management with caching
- **Tailwind CSS** - Utility-first CSS framework

### Infrastructure

- **MongoDB 7.0** - Document database with automatic initialization
- **Docker Compose** - Multi-container orchestration
- **Yarn 4** - Modern package manager with PnP

## More Abaout the App

### Terminal UI Design

- **Retro Computer Aesthetic**: Inspired by 80s/90s computer terminals
- **Green Phosphor Display**: Classic CRT monitor color scheme

### AI Model Selection

- **Local-First**: No external API dependencies
- **TinyLlama 1.1B**: Balanced performance vs. resource usage
- **CPU Optimized**: Runs on standard hardware without GPU
- **Fast Inference**: Optimized for quick response times

### Architecture Decisions

- **Feature-Based Structure**: Organized by business domains
- **Type Safety**: Full TypeScript coverage
- **Async/Await**: Modern async patterns throughout
- **Container Isolation**: Each service in separate container
- **Development Optimized**: Hot reload for both frontend and backend

## 📁 Project Structure

```
dutch-tutor-app/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── features/       # Feature-based modules
│   │   │   ├── chat/       # Chat functionality
│   │   │   └── conversations/ # Conversation management
│   │   └── shared/         # Shared utilities
│   │       ├── llm/        # AI model integration
│   │       └── database/   # MongoDB connection
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js React frontend
│   ├── features/           # Feature-based React components
│   │   └── conversation/   # Conversation UI components
│   ├── shared/             # Shared utilities
│   │   └── api/            # API client and TanStack Query
│   ├── pages/              # Next.js pages
│   └── styles/             # CSS styles
├── docker-compose.yml      # Container orchestration
└── mongo-init.js          # Database initialization
```

### Environment Configuration

**Root `.env`** (Docker Compose variables):

```env
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=password
DATABASE_NAME=assistant
```

**Backend `.env`** (Application settings):

```env
MODEL_ASSISTANT=TinyLlama/TinyLlama-1.1B-Chat-v1.0
MAX_NEW_TOKENS=100
TEMPERATURE=0.8
TOP_P=0.9
MONGODB_URL=mongodb://assistant_user:assistant_pass@mongodb:27017/assistant
DATABASE_NAME=assistant
```

### First Run

On first startup, the system will:

1. Download the TinyLlama model (~2.2GB)
2. Initialize MongoDB with collections and indexes
3. Build frontend and backend containers
4. Start all services with health checks

## 🧪 Testing

## 📊 API Documentation

With the backend running, visit:

- **Interactive Docs**: http://localhost:8000/docs
