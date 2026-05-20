# Connector Access Checklist

Connector state is defined in `connectors/registry.yaml`.

Before enabling a connector, update the registry, add or update runtime enforcement tests, and run:

```bash
npm run validate:yaml
npm run test:unit
```
