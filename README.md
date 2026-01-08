# ShellMind

AI-driven command synthesis for a seamless terminal experience. ShellMind translates natural language into precise shell commands, empowering developers, DevOps engineers, and system administrators to work faster and smarter.

## Features

- **Natural Language Processing** - Ask questions in plain English and get accurate shell commands
- **Multi-Tool Support** - Works with Docker, Kubernetes, Git, AWS CLI, Terraform, and more
- **Web Search Integration** - Search documentation and find "how to" guides for unfamiliar tools
- **Interactive Clarification** - Asks follow-up questions when commands need more context
- **Command Explanation** - Understand what complex commands do with the `explain` feature
- **Safe Execution** - Built-in warnings for potentially dangerous operations
- **Direct Execution** - Run generated commands with a single confirmation
- **Agent Mode** - Autonomous tool execution for complex multi-step tasks

## Quick Start (CLI)

Get up and running with ShellMind in under 5 minutes!

### Prerequisites

- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Groq API key** - Get one free at [console.groq.com](https://console.groq.com)
- (Optional) **Tavily API key** for web search - [Get at tavily.com](https://tavily.com)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/sidmanale643/shell-mind.git
cd shell-mind
```

**2. Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```env
GROQ_API_KEY=gsk_...your_actual_key_here
TAVILY_API_KEY=tvly-...your_key_here  # Optional
```

> **⚠️ Security Note**: Never commit your `.env` file to version control!

**3. Install dependencies**
```bash
# Using pip
pip install -r requirements.txt

# Or using uv (faster)
uv sync
```

**4. (Optional) Install system-wide command**
```bash
# This installs the 'sm' command globally
pip install -e .
```

### Running ShellMind

**Interactive Mode (Recommended)**
```bash
python -m cli.main

# Or if you installed system-wide:
sm
```

**One-Shot Commands**
```bash
# Generate and execute a command
python -m cli.main "list all docker containers"

# Explain a complex command
python -m cli.main --explain "kubectl get pods -n production"

# Auto-execute without confirmation
python -m cli.main --execute "find large files in /tmp"
```

### Agent Mode

Agent Mode enables autonomous tool execution for complex multi-step tasks:

```bash
# Enable for this session
python -m cli.main --agent

# Set agent mode as your default
python -m cli.main --set-mode agent

# Revert to default mode
python -m cli.main --set-mode default
```

**What Agent Mode does:**
- Executes commands directly with tools
- Performs web searches for documentation
- Handles multi-step operations autonomously
- Perfect for complex DevOps workflows

### Example Queries

Try these commands to get started:

**File System Operations**
```
"Find all large files over 100MB in my home directory"
"List all Python files modified in the last 24 hours"
"Find and remove all .log files older than 30 days"
```

**Docker Operations**
```
"Show me all running Docker containers"
"Stop all containers with exit code 1"
"Remove all dangling Docker images"
"Create a network named my-network and attach container nginx to it"
```

**Git Operations**
```
"Create a git branch called feature/new-ui"
"Show me the last 5 commits with author names"
"Undo the last commit but keep changes staged"
"Push all branches to remote origin"
```

**Kubernetes**
```
"Get all pods in the production namespace"
"Restart the deployment named api-server"
"Scale the frontend deployment to 5 replicas"
"Show all resources with label app=frontend"
```

**System Administration**
```
"List all processes using more than 1GB of memory"
"Check which process is using port 3000"
"Show disk usage for all mounted filesystems"
"Find all open network connections"
```

**Command Explanation**
```
/explain kubectl get pods -n production --field-selector status.phase=Running
/explain docker run -d -p 8080:80 --name web nginx:alpine
/explain tar -xzf archive.tar.gz -C /destination
```

### Quick Tips

- **Interactive Mode**: Just type `python -m cli.main` for the full experience with follow-up questions
- **Quick Queries**: Pass your query directly: `python -m cli.main "your question here"`
- **Explain Mode**: Use `/explain` prefix to understand any command
- **Agent Mode**: Enable with `--agent` flag for autonomous execution
- **Exit**: Type `exit` or `quit` in interactive mode, or press `Ctrl+C`

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required: Get your API key at https://console.groq.com
GROQ_API_KEY=your_groq_api_key_here

# Optional: OpenRouter API key (alternative LLM provider)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: For web search functionality - Get at https://tavily.com
TAVILY_API_KEY=your_tavily_api_key_here

# LLM Provider: groq or openrouter
LLM_PROVIDER=groq
```

### Supported Models

ShellMind currently uses:
- **Moonshot AI Kimi K2 Instruct** (via Groq)

## How It Works

### Command Generation

Simply describe what you want to do in plain English:

```
You: Find all Python files modified in the last 7 days

ShellMind: find . -name "*.py" -mtime -7 -type f

Run this command? [y/N]: y
```

### Command Explanation

Use the `explain` keyword to understand any command:

```
You: explain docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

ShellMind: This Docker command lists all containers (including stopped ones) in a
formatted table showing:
- Container names
- Current status (running, exited, etc.)
- Published ports

The --format flag uses Go template syntax to customize the output columns.
```

### Safety Features

- **Confirmation Prompts** - Dangerous commands require explicit confirmation
- **Warning Messages** - Clear warnings for destructive operations
- **Clarification Questions** - Asks when commands could be ambiguous
- **Safe Defaults** - Uses conservative flags and options by default

## Supported Tools

### Container & Orchestration
- **Docker** - Container management and operations
- **Kubernetes** - Pod, service, and cluster management
- **Helm** - Kubernetes package management

### Cloud Platforms
- **AWS CLI** - EC2, S3, Lambda, RDS operations
- **Google Cloud** - GKE, Cloud Storage, Cloud Functions
- **Azure** - AKS, Blob Storage, Functions

### Infrastructure as Code
- **Terraform** - Infrastructure provisioning and management
- **Ansible** - Configuration management and automation

### Version Control
- **Git** - Repository management, branching, merging
- **GitHub/GitLab CLI** - Repository operations

### System Administration
- **SystemD** - Service management
- **Nginx/Apache** - Web server configuration
- **PostgreSQL/MySQL** - Database operations
- **SSH** - Remote server access

## Troubleshooting

### Common Issues

**Problem**: `ModuleNotFoundError: No module named '...'`
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

**Problem**: API errors or authentication failures
```bash
# Solution: Verify your API key in .env file
cat .env | grep GROQ_API_KEY
```

**Problem**: Python version too old
```bash
# Solution: Install Python 3.11 or higher
# Check your version:
python --version
```

**Problem**: Command not found: `sm`
```bash
# Solution: Use the full command instead
python -m cli.main
```

**Problem**: Agent mode not working
- Ensure backend dependencies are installed
- Check that API keys are properly configured
- Verify you have necessary system permissions

### Getting Help

- Check the [sample_queries.txt](sample_queries.txt) for more examples
- Review [devops_use_cases.md](devops_use_cases.md) for DevOps-specific scenarios
- Open an issue on [GitHub Issues](https://github.com/sidmanale643/shell-mind/issues)

## Development

### Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run tests: `python -m pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest

# Run linting
python -m flake8 src/

# Format code
python -m black src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Groq** for providing fast and affordable LLM inference
- **Rich** for beautiful terminal interfaces
- **Moonshot AI** for the Kimi model family
- **Textual** for terminal UI components

---

**Made with ❤️ for developers who live in the terminal**
