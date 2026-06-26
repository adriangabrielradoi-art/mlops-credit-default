# `conf/`: Kedro configuration

| Folder | Purpose | Gitted? |
| ------------ | -------------------------------------------------- | -------- |
| `base/` | Shared config (catalog, parameters, globals) | yes |
| `local/` | Per-developer overrides + credentials | **no** |

`local/` overrides anything declared in `base/` with the same key. Put
secrets (Hopsworks API keys, MLflow remote-tracking URIs) in
`local/credentials.yml`, never in `base/`.
