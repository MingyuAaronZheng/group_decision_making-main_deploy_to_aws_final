# Technical Context

## Technologies Used
- **Backend**:
  - Django 3.0.4 (Python web framework)
  - Django Channels (for WebSocket support)
  - Django REST Framework (for API endpoints)
  - Redis (for Channels layer in WebSocket communication)
  - PostgreSQL (primary database)
  - GPT integration for AI moderator and participant roles
  - Asynchronous consumers for WebSocket handling

- **Frontend**:
  - Vue.js (JavaScript framework)
  - Vue Router for navigation
  - WebSocket client implementation for real-time communication
  - Bootstrap Vue for UI components
  - AWS Amplify for authentication and deployment

- **Deployment**:
  - AWS Elastic Beanstalk for Django backend
  - AWS Amplify for Vue.js frontend
  - AWS RDS for PostgreSQL database
  - AWS ElastiCache for Redis
  - Nginx with custom configuration for WebSocket support

## Development Setup
- Django development server for backend
- Vue.js development server with hot-reloading
- Local PostgreSQL database for development
- Local Redis instance for WebSocket channel layers
- WebSocket connections for real-time communication

## Technical Constraints
- WebSocket connection requirements for real-time chat
- AWS deployment configuration and environment variables
- Cross-origin resource sharing (CORS) configuration for frontend-backend communication
- Database migration management for experiment model changes
- GPT API integration requirements

## Dependencies
- **Backend Dependencies**:
  - Django and Django Channels
  - Channels Redis for WebSocket support
  - psycopg2 for PostgreSQL connection
  - Django REST Framework
  - GPT-related libraries

- **Frontend Dependencies**:
  - Vue.js and Vue Router
  - Bootstrap Vue
  - WebSocket client library
  - AWS Amplify libraries

## Environment Configuration
- Multiple allowed hosts configured for various environments (development, staging, production)
- Debug mode disabled in production settings
- Database configuration based on environment variables
- Redis connection configuration for WebSocket channels
- CORS configuration for allowed origins

## Experimental Parameters
- n=[500,1000,2000,5000] - Likely participant counts or data sample sizes for different experimental conditions
- skew=[0,3,5] - Possibly distribution parameters for participant assignment or data generation
- d=[128,256,768] - Possibly dimension parameters for embeddings or feature vectors in AI integration

[2025-05-13 22:00:09] - Updated with detailed technical information
