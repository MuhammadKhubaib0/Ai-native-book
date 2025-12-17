# Agent Context Update - Manual Step

**Feature**: 2-gazebo-unity-digital-twin
**Date**: 2025-12-12

## Description

As part of the planning phase, the agent context should be updated with new technology information from this plan. This would typically be done by running:

`.specify/scripts/powershell/update-agent-context.ps1 -AgentType qwen`

This script would detect that Qwen is the AI agent in use and update the appropriate agent-specific context file with the new technologies from the current plan, while preserving manual additions between markers.

## Technologies to Add to Context

- Gazebo Harmonic simulation engine
- Unity 2022.3 LTS
- Unity ML-Agents Toolkit
- SDF (Simulation Description Format)
- Physics simulation concepts (ODE, Bullet, DART engines)
- Sensor simulation (LiDAR, depth cameras, IMUs)
- Sim-to-real transfer techniques
- Domain randomization
- System identification

These technologies should be added to the agent's context to provide better assistance during implementation of this feature.