# Glossary of CrewAI Terms

This glossary defines the CrewAI terms used throughout `crewai-recipes`. For a broader view of how they fit together, start with the [Architecture Overview](./architecture.md).

## Agent

An **Agent** is one instance of `crewai.Agent`: a specialized worker configured with a `role`, `goal`, `backstory`, an `llm`, and optional tools. Agents in this repository follow a narrow responsibility and collaborate through tasks; see the [Agent Design Philosophy](./architecture.md#agent-design-philosophy) and [Agent Design Patterns](./agent-patterns.md).

## Task

A **Task** is one instance of `crewai.Task`: a specific assignment whose `description` states the work and whose `expected_output` defines what completion should look like. A task can also depend on results from earlier tasks; see the [Task Context Graph](./architecture.md#task-context-graph).

## Crew

A **Crew** is one instance of `crewai.Crew` that bundles agents, tasks, and a process into one runnable workflow. The crew defines who participates and how their work is coordinated; see [Core Abstractions](./architecture.md#core-abstractions) and [Process Types](./architecture.md#process-types).

## Process

A **Process** is the execution strategy a crew uses to coordinate its tasks. `Process.sequential` runs tasks in order and is the default used by most recipes, while `Process.hierarchical` adds a manager that assigns and coordinates work; see [Process Types](./architecture.md#process-types).

## Tool

A **Tool** is a callable capability an agent can use to take an action, such as searching the web or reading a file. Tools are assigned only where the agent needs them, keeping responsibilities and available actions explicit; see [Adding Tools](./architecture.md#adding-tools).

## Context Chaining

**Context chaining** passes the output of one task into another with `Task(context=[...])`. It makes dependencies explicit and lets downstream tasks build on selected upstream results; see the [Task Context Graph](./architecture.md#task-context-graph).

## Kickoff

**Kickoff** is the call to `crew.kickoff()` that starts a configured crew and returns its result after the process finishes. Recipes build their agents, tasks, and crew before kickoff, as shown in [Core Abstractions](./architecture.md#core-abstractions) and the [recipe-writing workflow](./writing-a-recipe.md).
