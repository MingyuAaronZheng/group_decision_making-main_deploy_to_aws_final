# System Patterns

## Architecture Patterns
- **WebSocket Communication**: Real-time bidirectional communication between clients and server using Django Channels with Redis as the channel layer
- **Room-based Chat System**: Organization of discussions into separate rooms/channels based on group IDs
- **Frontend-Backend Separation**: Clear separation between Vue.js frontend and Django backend with API communication
- **Turn-based Discussion**: Structured conversation flow with turn management for group discussions
- **Experimental Conditions**: System supports different experimental configurations:
  - Moderator conditions (0: No AI Moderator, 1: AI Moderator)
  - Participant conditions (0: 2 Human Participants, 1: 2 Human + Advocating AI, 2: 2 Human + Disputing AI, 3: 2+1 Human)

## Code Organization
- **Django App Structure**: 
  - `experiment/` app contains the core functionality
  - `server/` contains project settings and configuration
  - Models organized by experimental entities (Subject, Group, MessageRecord, etc.)
  - WebSocket consumers handle real-time communication
- **Vue.js Component Structure**: 
  - Standard Vue.js project with router-based navigation
  - WebSocketClient for communication with backend
  - Survey components for data collection
  - Chat interface components

## Data Flow Patterns
- **Group Formation**: Subjects are assigned to groups based on experimental conditions
- **Message Broadcasting**: Messages are broadcast to all members of a group
- **Turn Management**: System tracks and enforces turn-based discussion rules
- **Survey Data Collection**: Structured collection of pre/post discussion survey data
- **AI Integration**: GPT integration for AI moderator and AI participant roles

## API Patterns
- **WebSocket API**: Used for real-time communication
  - Endpoints: `/ws/chat/<room_name>/` and `/ws/echo/`
  - ChatConsumer handles group chat functionality
  - EchoConsumer provides testing functionality
- **REST API**: Django views provide HTTP endpoints for:
  - User management
  - Survey submission
  - Experiment configuration

## Deployment Patterns
- **AWS Elastic Beanstalk**: Configuration for Django backend deployment
  - Custom Nginx configuration for WebSocket support
  - Environment variables for database and Redis connections
- **AWS Amplify**: Configuration for Vue.js frontend deployment
- **Database**: PostgreSQL on AWS RDS for production, local PostgreSQL for development
- **WebSocket Infrastructure**: Redis on AWS ElastiCache for channel layers

## Testing Patterns
- Test files present for both views and GPT functionality
- Separate test environment configuration

[2025-05-13 22:00:09] - Updated with detailed system architecture information
