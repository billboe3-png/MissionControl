# Decision Matrix

Every future feature must answer these questions before implementation.

## Questions

| # | Question | Options |
|---|----------|---------|
| 1 | Is it vendor-specific? | Yes / No |
| 2 | Is it optional (not every customer needs it)? | Yes / No |
| 3 | Can it be independently updated? | Yes / No |
| 4 | Does it require agent-side execution? | Yes / No |
| 5 | Does it need both server and agent components? | Yes / No |

## Decision Tree

```
Is it vendor-specific?
├── YES → Is it optional?
│   ├── YES → Is it agent-side?
│   │   ├── YES → Does it need server component too?
│   │   │   ├── YES → HYBRID PLUGIN
│   │   │   └── NO → AGENT PLUGIN
│   │   └── NO → SERVER PLUGIN
│   └── NO → [Discuss: should it really be vendor-specific?]
└── NO → Is it core infrastructure?
    ├── YES → CORE
    └── NO → Is it a framework?
        ├── YES → CORE (framework only)
        └── NO → PLUGIN
```

## Examples

| Feature | Vendor? | Optional? | Agent? | Result |
|---------|---------|-----------|--------|--------|
| Zabbix monitoring | Yes | Yes | No | Server Plugin |
| RustDesk remote | Yes | Yes | Yes | Agent Plugin |
| Patch management | Yes | Yes | Yes | Hybrid Plugin |
| JWT authentication | No | No | No | Core |
| Plugin manager | No | No | No | Core |
| Dashboard framework | No | No | No | Core |
| Windows Event Logs | Yes | Yes | Yes | Agent Plugin |
| Multi-tenancy | No | No | No | Core |
| Slack notifications | Yes | Yes | No | Server Plugin |
| SMART disk monitoring | Yes | Yes | Yes | Agent Plugin |

## Validation Checklist

Before implementing any feature, confirm:

- [ ] Core features are vendor-agnostic
- [ ] Vendor features are plugins
- [ ] Plugins use only SDK public interfaces
- [ ] Plugins are independently versioned
- [ ] Plugins are independently deployable
- [ ] Core does not import plugin code
- [ ] Plugins do not import core internal code
