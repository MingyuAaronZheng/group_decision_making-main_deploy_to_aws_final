# Active Context

## Current Focus
- Understanding the group decision-making experiment platform structure
- Examining the deployment configuration for AWS (Elastic Beanstalk for backend, Amplify for frontend)
- Documenting the experimental conditions and participant roles

## Recent Changes
- Reviewed project structure including Django backend and Vue.js frontend
- Examined WebSocket implementation for real-time chat functionality
- Analyzed database models for experiment data collection

## Open Questions/Issues
- How are the experimental parameters n=[500,1000,2000,5000], skew=[0,3,5], d=[128,256,768] used in the experiment?
- What is the specific workflow for participants in different experimental conditions?
- How is the GPT integration implemented for AI moderator and AI participant roles?
- What are the specific deployment steps for AWS Elastic Beanstalk and Amplify?

## Current Session Goals
- Complete comprehensive memory bank documentation
- Understand the experimental workflow and conditions
- Document the system architecture and communication patterns
- Clarify deployment configuration requirements

## Important Features
- Group formation with configurable sizes and conditions
- Turn-based discussion system with real-time WebSocket communication
- AI integration for moderator and participant roles
- Comprehensive survey system (demographic, pre-discussion, post-discussion)
- Experimental conditions:
  - Moderator conditions (0: No AI Moderator, 1: AI Moderator)
  - Participant conditions (0: 2 Human Participants, 1: 2 Human + Advocating AI, 2: 2 Human + Disputing AI, 3: 2+1 Human)

## Experimental Parameters
- n=[500,1000,2000,5000] - Likely related to participant counts or data sample sizes
- skew=[0,3,5] - Possibly distribution parameters for data or participant assignment
- d=[128,256,768] - Possibly dimension parameters for embeddings or feature vectors

[2025-05-13 22:00:09] - Updated with detailed project information
