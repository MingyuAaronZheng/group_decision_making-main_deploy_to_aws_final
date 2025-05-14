# Product Context

## Project Overview
This project is a comprehensive platform for conducting controlled experiments on group decision-making processes. The system facilitates group discussions with various configurations including AI moderators and AI participants, allowing researchers to study how different group compositions and AI involvement affect decision-making processes and outcomes.

## Why This Project Exists
- To enable research on group decision-making dynamics in controlled environments
- To study the impact of AI participation and moderation on group discussions
- To collect structured data on how different experimental conditions affect discussion outcomes
- To provide a platform for testing hypotheses about group behavior and decision-making processes

## Problems It Solves
- Creates a controlled environment for group decision-making experiments
- Enables systematic variation of experimental conditions (moderator types, participant compositions)
- Facilitates data collection through structured surveys and discussion records
- Supports remote participation in experiments through web-based interface
- Allows integration of AI agents as participants or moderators with controlled behaviors

## Components
- **Backend**: Django-based server with WebSocket support for real-time communication
- **Frontend**: Vue.js application with responsive design
- **Database**: PostgreSQL for structured data storage
- **WebSockets**: Redis-backed channel layers for real-time communication
- **Deployment**: AWS Elastic Beanstalk and AWS Amplify configurations

## Key Features
- Real-time chat functionality using WebSockets
- Group formation with configurable experimental conditions
- Turn-based discussion system
- AI integration for moderator and participant roles
- Comprehensive survey system (demographic, pre-discussion, post-discussion)
- Avatar assignment for participant identification
- Early exit handling and attention checks for data quality

## User Experience Goals
- Provide a seamless and intuitive discussion interface for participants
- Enable natural conversation flow while maintaining experimental control
- Collect rich data on participant opinions and behaviors
- Support different experimental conditions without changing the core user experience
- Ensure consistent experience across different devices and browsers
- Maintain participant engagement throughout the experiment

## Experimental Design
- **Moderator Conditions**:
  - 0: No AI Moderator (control)
  - 1: AI Moderator (treatment)
- **Participant Conditions**:
  - 0: 2 Human Participants (control)
  - 1: 2 Human Participants + ADVOCATING AI Participant
  - 2: 2 Human Participants + DISPUTING AI Participant
  - 3: 2+1 Human Participants

## Technical Architecture
- Django backend with Channels for WebSocket support
- Vue.js frontend for responsive user interface
- PostgreSQL database for data storage
- Redis for WebSocket channel layers
- AWS deployment infrastructure

[2025-05-13 22:00:09] - Updated with detailed product information
