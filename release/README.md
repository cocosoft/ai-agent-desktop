# AI Agent Desktop

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0%2B-green)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A powerful desktop application for managing and coordinating multiple AI agents with an intuitive graphical interface.

## 🚀 Features

### Core Framework
- **Modern Desktop App**: Built with PyQt6 for cross-platform compatibility
- **Configuration Management**: YAML-based configuration with GUI interface
- **Database System**: SQLite database with 17 core data tables
- **Logging System**: Structured logging and error handling

### AI Model Management
- **Multi-Model Support**: OpenAI GPT series, Ollama local models
- **Unified Interface**: Standardized model calling interface
- **Load Balancing**: Intelligent model selection and load management
- **Performance Monitoring**: Real-time performance metrics

### Capability Management
- **Capability Discovery**: Automatic testing and registration of AI capabilities
- **Capability Testing**: Multiple testing strategies and performance evaluation
- **Capability Mapping**: Intelligent model-to-capability mapping
- **Capability Optimization**: Performance optimization and cost control

### Agent Management
- **Agent Creation**: Graphical agent creation wizard
- **Lifecycle Management**: Start, stop, monitor, and fault recovery
- **Template System**: Predefined agent templates and custom templates
- **Status Monitoring**: Real-time agent status and performance monitoring

### Task System
- **Task Creation**: Support for multiple task types
- **Intelligent Assignment**: Capability-based task routing
- **Execution Monitoring**: Task execution status and result tracking
- **History Records**: Complete task execution history

### A2A Communication
- **Inter-Agent Communication**: Support for message passing between agents
- **Collaboration Workflows**: Sequential, parallel, hierarchical, and peer-to-peer collaboration
- **Task Decomposition**: Complex task decomposition and result merging
- **Error Propagation**: Complete error handling and recovery mechanism

### User Interface
- **Intuitive Interface**: Modern graphical user interface
- **Multi-Tab Design**: Functionally modular tab design
- **Real-time Monitoring**: Performance monitoring and status display panel
- **Configuration Interface**: Graphical configuration management interface

## 📋 Requirements

- **Python**: 3.8 or higher
- **Operating Systems**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Memory**: 4GB RAM (8GB recommended)
- **Storage**: 500MB available space

## 🛠️ Installation

### Method 1: Source Installation (Recommended for Developers)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/cocosoft/ai-agent-desktop.git
   cd ai-agent-desktop
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

### Method 2: Installer Packages (Recommended for Users)

- **Windows**: Download and run `AI_Agent_Desktop_Setup_v1.0.0.exe`
- **macOS**: Download and open `AI_Agent_Desktop_v1.0.0.dmg`
- **Linux**: Download and run `AI_Agent_Desktop_v1.0.0.AppImage`

## 🚀 Quick Start

1. **Launch the Application**:
   - Double-click the application icon or run `python main.py`

2. **Configure AI Models**:
   - Go to Settings → AI Models
   - Add your OpenAI API key or configure Ollama service

3. **Create Your First Agent**:
   - Click "New Agent" in the Agent Manager
   - Follow the agent creation wizard
   - Select capabilities and configure settings

4. **Send Your First Task**:
   - Go to the Tasks tab
   - Click "New Task"
   - Enter your task description and select an agent
   - Click "Send Task"

5. **View Results**:
   - Check the task history for execution results
   - Monitor agent performance in real-time

## 📁 Project Structure

```
ai_agent_desktop/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── setup.py               # Installation script
├── config/                # Configuration files
│   ├── app_config.yaml    # Main application configuration
│   └── model_configs/     # AI model configurations
├── src/                   # Source code
│   ├── core/              # Core business logic
│   ├── ui/                # User interface components
│   ├── adapters/          # AI model adapters
│   ├── data/              # Data access layer
│   ├── utils/             # Utility functions
│   └── a2a/               # Agent-to-agent communication
├── tests/                 # Test cases
└── docs/                  # Documentation
```

## 🔧 Configuration

The application automatically creates default configuration files on first run:

- **Main Config**: `config/app_config.yaml`
- **Database**: `data/app.db`
- **Logs**: `logs/app.log`

### Key Configuration Options

```yaml
# Application Settings
app:
  name: "AI Agent Desktop"
  version: "1.0.0"
  language: "en"

# Database Configuration
database:
  path: "data/app.db"
  backup_enabled: true

# Logging Configuration
logging:
  level: "INFO"
  format: "detailed"
  max_size: "10MB"

# UI Configuration
ui:
  theme: "default"
  font_size: 12
  auto_save: true
```

## 🎯 Usage Examples

### Creating an Agent

```python
# Example: Programmatic agent creation
from src.core.agent_model import Agent
from src.core.agent_lifecycle import AgentLifecycleManager

agent = Agent(
    name="Research Assistant",
    description="An AI agent specialized in research tasks",
    capabilities=["research", "analysis", "summarization"]
)

lifecycle_manager = AgentLifecycleManager()
lifecycle_manager.start_agent(agent)
```

### Sending a Task

```python
# Example: Programmatic task submission
from src.core.task_allocator import TaskAllocator

task = {
    "type": "research",
    "content": "Research the latest developments in AI",
    "priority": "high",
    "agent_id": "research_assistant_001"
}

allocator = TaskAllocator()
result = allocator.allocate_task(task)
```

## 🧪 Testing

Run the test suite to verify installation:

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/performance/   # Performance tests

# Generate test coverage report
pytest --cov=src tests/
```

## 🔍 Troubleshooting

### Common Issues

**Application won't start:**
- Check Python version (requires 3.8+)
- Verify all dependencies are installed
- Check log file: `logs/app.log`

**AI model connection fails:**
- Verify network connection
- Check API keys or service addresses
- Ensure model services are running

**Agent creation fails:**
- Verify agent configuration is complete
- Check required capabilities are configured
- Review agent logs for detailed error information

### Getting Help

- **Documentation**: Check the [User Manual](docs/USER_MANUAL.md)
- **Issues**: Report bugs or feature requests on [GitHub Issues](https://github.com/cocosoft/ai-agent-desktop/issues)
- **Community**: Join our community forum for support

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PyQt6 Team** for the excellent GUI framework
- **OpenAI** and **Ollama** for AI model services
- **All contributors** and test users for valuable feedback

## 📞 Contact

- **Project Maintainer**: AI Agent Desktop Team
- **Email**: your-email@example.com
- **GitHub**: [cocosoft](https://github.com/cocosoft)

---

**AI Agent Desktop Team**  
*Making AI Agent Management Simple!*
