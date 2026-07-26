# Plugin Marketplace

The Mission Control marketplace is a centralized repository for discovering, installing, and distributing plugins. It supports both community and enterprise plugins with various pricing models.

## Publishing Plugins

### Prerequisites

1. **Mission Control Account**: Create an account at marketplace.mission-control.io
2. **Developer License**: Accept the developer terms of service
3. **Plugin Package**: Prepare plugin package (tar.gz format)

### Package Structure

```
my-plugin/
├── manifest.json
├── README.md
├── CHANGELOG.md
├── LICENSE
├── server/
│   └── index.py
├── agent/
│   └── index.py
├── assets/
│   ├── icon.png
│   └── screenshots/
└── tests/
    └── test_plugin.py
```

### Build Package

```bash
# Build plugin package
mission-control plugin build ./my-plugin/

# This creates: my-plugin-1.0.0.tar.gz
```

### Publish to Marketplace

```bash
# Login to marketplace
mission-control marketplace login

# Publish plugin
mission-control plugin publish ./my-plugin-1.0.0.tar.gz

# Publish with specific visibility
mission-control plugin publish ./my-plugin-1.0.0.tar.gz --visibility private
```

### Programmatic Publishing

```python
from mission_control.marketplace import MarketplaceClient

client = MarketplaceClient(api_key="your-api-key")

# Publish plugin
result = client.publish(
    package_path="./my-plugin-1.0.0.tar.gz",
    visibility="public",
    changelog="Initial release with system monitoring features"
)

print(f"Published: {result.url}")
```

## Listing Requirements

### Minimum Requirements

1. **Valid Manifest**: All required fields must be present
2. **No External Dependencies**: No pip packages or system dependencies
3. **Python 3.12 Compatible**: Code must be compatible with Python 3.12
4. **Complete Documentation**: README with usage instructions
5. **License File**: Valid open-source or proprietary license
6. **Changelog**: Documented version history
7. **Icon**: 128x128 PNG icon

### Code Quality Requirements

1. **No Security Vulnerabilities**: Pass security scan
2. **No Malicious Code**: Pass code review
3. **Proper Error Handling**: Graceful error handling
4. **Logging**: Appropriate logging levels
5. **Type Hints**: Python type hints for public APIs

### Documentation Requirements

1. **README.md**: Installation, configuration, usage
2. **CHANGELOG.md**: Version history
3. **API Documentation**: Public API documentation
4. **Examples**: Usage examples
5. **Troubleshooting**: Common issues and solutions

## Review Process

### Automated Checks

1. **Manifest Validation**: Validate manifest.json schema
2. **Security Scan**: Check for security vulnerabilities
3. **Code Analysis**: Static code analysis
4. **Compatibility Check**: Verify Mission Control compatibility
5. **Dependency Check**: Validate plugin dependencies

### Manual Review

1. **Code Quality**: Review code for best practices
2. **Documentation**: Review documentation completeness
3. **Functionality**: Test plugin functionality
4. **Performance**: Verify performance impact
5. **Compliance**: Check compliance with guidelines

### Review Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Automated | 1 hour | Automated checks and scans |
| Manual | 2-5 days | Human review and testing |
| Approval | 1 day | Final approval and publishing |

### Review Feedback

```python
from mission_control.marketplace import MarketplaceClient

client = MarketplaceClient(api_key="your-api-key")

# Check review status
status = client.get_review_status(plugin_name="my-plugin")

print(f"Status: {status.phase}")
print(f"Feedback: {status.feedback}")
```

### Addressing Feedback

```python
# Update plugin with fixes
client.update_plugin(
    plugin_name="my-plugin",
    version="1.0.1",
    package_path="./my-plugin-1.0.1.tar.gz",
    changelog="Fixed review feedback: improved error handling"
)
```

## Pricing Models

### Community Plugins

Free plugins available to all users:

- **Free to install**: No cost for users
- **Free to distribute**: No marketplace fees
- **Optional donations**: Support through donations
- **Community support**: Community-driven support

### Enterprise Plugins

Commercial plugins with paid licensing:

- **Per-agent pricing**: Price per agent host
- **Per-user pricing**: Price per user
- **Flat rate**: Fixed price per installation
- **Subscription**: Monthly/annual subscription

### Pricing Configuration

```json
{
  "pricing": {
    "model": "per_agent",
    "price": 10.00,
    "currency": "USD",
    "billing_cycle": "monthly",
    "trial_days": 14,
    "free_tier": {
      "agents": 5,
      "features": ["basic_monitoring"]
    }
  }
}
```

### Pricing Models

| Model | Description | Example |
|-------|-------------|---------|
| `free` | No cost | Community plugins |
| `per_agent` | Price per agent host | $10/agent/month |
| `per_user` | Price per user | $5/user/month |
| `flat_rate` | Fixed price | $100 one-time |
| `subscription` | Recurring payment | $20/month |
| `tiered` | Usage-based tiers | $0-100 agents: $5, 100+: $3 |

### Enterprise Features

Enterprise plugins can offer:

- **Priority support**: Direct support from developers
- **Custom features**: Customization options
- **SLA guarantees**: Service level agreements
- **Dedicated resources**: Dedicated infrastructure
- **Compliance certifications**: SOC2, HIPAA, etc.

## Categories

### Available Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `monitoring` | System and application monitoring | System metrics, APM, log monitoring |
| `utilities` | General utilities and tools | File management, data processing |
| `security` | Security and access control | Authentication, encryption, auditing |
| `automation` | Workflow automation | Task scheduling, event-driven workflows |
| `integration` | Third-party integrations | Cloud services, APIs, databases |
| `backup` | Backup and recovery | Data backup, disaster recovery |
| `networking` | Network management | Network monitoring, configuration |
| `database` | Database operations | Database management, optimization |
| `development` | Development tools | CI/CD, testing, debugging |

### Category Guidelines

1. **Accurate Categorization**: Choose the most appropriate category
2. **Multiple Categories**: Can list in up to 3 categories
3. **Category Requirements**: Each category has specific requirements
4. **Category Icons**: Use category-specific icons

## Search

### Search Features

- **Keyword search**: Search by name, description, tags
- **Category filtering**: Filter by category
- **Type filtering**: Filter by plugin type (server/agent/hybrid)
- **Price filtering**: Filter by price range
- **Rating filtering**: Filter by user rating
- **Version filtering**: Filter by compatibility

### Search API

```python
from mission_control.marketplace import MarketplaceClient

client = MarketplaceClient()

# Search plugins
results = client.search(
    query="monitoring",
    category="utilities",
    plugin_type="hybrid",
    min_rating=4.0,
    max_price=50.0,
    sort_by="rating",
    limit=20
)

for plugin in results:
    print(f"{plugin.name} - {plugin.rating} stars")
```

### Search Results

```json
{
  "results": [
    {
      "name": "advanced-monitoring",
      "version": "2.1.0",
      "description": "Advanced monitoring plugin",
      "author": "Mission Control Team",
      "rating": 4.8,
      "reviews": 125,
      "installs": 1500,
      "price": 0,
      "categories": ["monitoring", "utilities"],
      "type": "hybrid",
      "compatibility": {
        "minMissionControl": "2.0.0",
        "maxMissionControl": "3.0.0"
      }
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 20
}
```

## Ratings and Reviews

### Rating System

- **1-5 stars**: User ratings
- **Written reviews**: User feedback
- **Verified installs**: Only from installed plugins
- **Helpful votes**: Mark reviews as helpful

### Review API

```python
from mission_control.marketplace import MarketplaceClient

client = MarketplaceClient(api_key="your-api-key")

# Submit review
client.submit_review(
    plugin_name="my-plugin",
    rating=5,
    title="Great plugin!",
    body="Works perfectly for our monitoring needs.",
    version="1.0.0"
)

# Get reviews
reviews = client.get_reviews(
    plugin_name="my-plugin",
    sort_by="recent",
    limit=50
)
```

### Review Guidelines

1. **Be specific**: Describe your experience
2. **Include context**: Version used, use case
3. **Be constructive**: Suggest improvements
4. **No spam**: Genuine reviews only
5. **Respectful**: Maintain professional tone

## Plugin Updates

### Updating Plugins

```bash
# Check for updates
mission-control plugin check-updates

# Update specific plugin
mission-control plugin update my-plugin

# Update all plugins
mission-control plugin update --all
```

### Update Notifications

```python
from mission_control.marketplace import MarketplaceClient

client = MarketplaceClient()

# Check for updates
updates = client.check_updates()

for update in updates:
    print(f"Update available: {update.name} {update.current} -> {update.latest}")
    print(f"Changelog: {update.changelog}")
```

### Auto-Updates

Configure automatic updates:

```yaml
# mission-control.yaml
plugins:
  auto_update: true
  update_strategy: "patch"  # major, minor, patch, none
  excluded_plugins:
    - "critical-plugin"
  update_window:
    day: "sunday"
    time: "02:00"
```

## Installation

### From Marketplace

```bash
# Search for plugins
mission-control plugin search monitoring

# Install plugin
mission-control plugin install advanced-monitoring

# Install specific version
mission-control plugin install advanced-monitoring@2.1.0

# Install with configuration
mission-control plugin install advanced-monitoring --config api_key=xxx
```

### Programmatic Installation

```python
from mission_control.plugins import PluginManager

manager = PluginManager()

# Install plugin
manager.install(
    "advanced-monitoring",
    version="2.1.0",
    config={"api_key": "xxx"}
)

# Enable plugin
manager.enable("advanced-monitoring")
```

### Installation Options

| Option | Description | Default |
|--------|-------------|---------|
| `--version` | Specific version | latest |
| `--config` | Configuration values | none |
| `--force` | Force installation | false |
| `--skip-deps` | Skip dependencies | false |

## Best Practices

1. **Thorough Testing**: Test plugin before publishing
2. **Clear Documentation**: Provide comprehensive documentation
3. **Responsive Support**: Address user issues promptly
4. **Regular Updates**: Maintain and update plugin regularly
5. **Follow Guidelines**: Adhere to marketplace guidelines
6. **Monitor Usage**: Track plugin usage and feedback

## Next Steps

- [MANIFEST.md](MANIFEST.md) — Manifest format reference
- [VERSIONING.md](VERSIONING.md) — Versioning details
- [PLUGIN_SDK.md](PLUGIN_SDK.md) — SDK overview
- [AGENT_SDK.md](AGENT_SDK.md) — Agent plugin development
- [SERVER_PLUGINS.md](SERVER_PLUGINS.md) — Server plugin development
