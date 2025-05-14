# Project Brief: Group Decision Making Platform

## Project Overview
This project is a web-based platform for conducting group decision-making experiments. The system facilitates group discussions with various configurations including AI moderators and AI participants. The platform is designed to study how different group compositions and AI involvement affect decision-making processes and outcomes.

## Core Requirements

### Backend (Django)
- Django-based server with WebSocket support for real-time communication
- PostgreSQL database for data persistence
- Redis for WebSocket channel layers
- Support for AWS deployment (Elastic Beanstalk)
- API endpoints for experiment management and data collection

### Frontend (Vue.js)
- Vue.js application with routing capabilities
- Real-time chat interface using WebSockets
- Survey components for data collection
- Support for different user roles (participants, moderators)
- AWS Amplify deployment

### Experiment Features
- Group formation with configurable sizes and conditions
- Support for different experimental conditions:
  - Moderator conditions (0: No AI Moderator, 1: AI Moderator)
  - Participant conditions (0: 2 Human Participants, 1: 2 Human + Advocating AI, 2: 2 Human + Disputing AI, 3: 2+1 Human)
- Turn-based discussion system
- Avatar assignment for participants
- Comprehensive survey system (demographic, pre-discussion, post-discussion)
- Early exit handling and attention checks

### Data Collection
- Participant demographic information
- Discussion messages and timestamps
- Survey responses
- Participation metrics and timing data

## Technical Parameters
Based on the memory provided:
- n=[500,1000,2000,5000] (likely participant or data point counts)
- skew=[0,3,5] (likely distribution parameters)
- d=[128,256,768] (likely dimension parameters, possibly for embeddings)

## Deployment Targets
- Backend: AWS Elastic Beanstalk
- Frontend: AWS Amplify
- Database: AWS RDS (PostgreSQL)
- WebSockets: Redis on AWS ElastiCache
