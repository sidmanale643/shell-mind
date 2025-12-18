# ShellMind 

An intelligent shell assistant that translates natural language into precise shell commands using AI. Perfect for developers, DevOps engineers, and system administrators who want to work faster and more efficiently in the terminal.

![ShellMind Demo](https://via.placeholder.com/800x400/1a1a2e/00d4ff?text=ShellMind+Terminal+Interface)

## Features

- **Natural Language Processing**: Ask questions in plain English and get accurate shell commands
- **Multi-Tool Support**: Works with Docker, Kubernetes, Git, AWS CLI, Terraform, and more
- **Interactive Clarification**: Asks follow-up questions when commands need more context
- **Command Explanation**: Understand what complex commands do with the `explain` feature
- **Safe Execution**: Built-in warnings for potentially dangerous operations
- **Beautiful Interface**: Rich terminal UI with syntax highlighting and panels
- **Direct Execution**: Run generated commands with a single confirmation

## Quick Start

### Prerequisites

- Python 3.11+
- Groq API key (get one at [groq.com](https://groq.com))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/shell-mind.git
   cd shell-mind
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # or if using uv
   uv sync
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

4. **Run ShellMind**
   ```bash
   python -m src.main
   ```

## Use Cases

### Development Workflow
- **Project Setup**: Initialize Git repo, create virtual environment, install dependencies
- **Code Analysis**: Find large files, check disk usage, analyze project structure
- **Version Control**: Branch management, commit history, remote operations
- **Environment Management**: Process monitoring, resource usage, system diagnostics

### DevOps Operations
- **Container Management**: Deploy, monitor, and troubleshoot containerized applications
- **Kubernetes Orchestration**: Pod management, service discovery, cluster operations
- **Infrastructure Monitoring**: Resource utilization, log analysis, performance metrics
- **CI/CD Pipelines**: Build automation, deployment scripts, rollback procedures

### System Administration
- **Server Maintenance**: Service management, log rotation, security monitoring
- **Network Diagnostics**: Connectivity testing, port scanning, traffic analysis
- **Database Operations**: Backup procedures, query optimization, connection management
- **Security Auditing**: Permission checks, access control, vulnerability assessment

### Cloud Management
- **AWS Operations**: EC2 instance management, S3 bucket operations, Lambda functions
- **Infrastructure as Code**: Terraform deployments, configuration validation, state management
- **Multi-cloud Monitoring**: Resource inventory, cost optimization, compliance checks

## Command Explanation

Use the `explain` command to understand what shell commands do:

```
You: explain
ShellMind: What command would you like me to explain?

You: kubectl get pods -n production --field-selector status.phase=Running
ShellMind: This command retrieves all pods in the 'production' namespace that are currently in the 'Running' phase...

You: explain docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
ShellMind: This Docker command lists all containers (including stopped ones) in a formatted table showing names, status, and ports...
```

## Safety Features

- **Confirmation Prompts**: Dangerous commands require explicit confirmation before execution
- **Warning Messages**: Clear warnings for potentially destructive operations
- **Clarification Questions**: Asks for clarification when commands could be ambiguous or risky
- **Safe Defaults**: Uses conservative flags and options by default

## Architecture

```
shell-mind/
├── src/
│   ├── main.py          # Main application and CLI interface
│   ├── llm.py           # Groq API integration and response parsing
│   ├── prompt.py        # System prompts and templates
│   ├── tools/           # Extensible tool integrations
│   └── memory/          # Conversation memory (future feature)
├── cli/                 # CLI wrapper scripts
├── sample_queries.txt   # Example queries and use cases
└── pyproject.toml       # Project configuration
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Supported Models

ShellMind currently uses:
- **Moonshot AI Kimi K2 Instruct** (via Groq)

## 📚 Supported Tools & Technologies

### Container & Orchestration
- **Docker**: Container management and operations
- **Kubernetes**: Pod, service, and cluster management
- **Helm**: Kubernetes package management

### Cloud Platforms
- **AWS CLI**: EC2, S3, Lambda, RDS operations
- **Google Cloud**: GKE, Cloud Storage, Cloud Functions
- **Azure**: AKS, Blob Storage, Functions

### Infrastructure as Code
- **Terraform**: Infrastructure provisioning and management
- **Ansible**: Configuration management and automation

### Version Control
- **Git**: Repository management, branching, merging
- **GitHub/GitLab CLI**: Repository operations

### System Administration
- **SystemD**: Service management
- **Nginx/Apache**: Web server configuration
- **PostgreSQL/MySQL**: Database operations
- **SSH**: Remote server access

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the tests**: `python -m pytest`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

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

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/shell-mind/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/shell-mind/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/shell-mind/wiki)

---

**Made with ❤️ for developers who live in the terminal**
