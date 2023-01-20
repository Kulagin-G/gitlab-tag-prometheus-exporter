## Description
A simple Prometheus format metric generator and exporter tool based on data with git tag from Gitlab API.

## Metrics example

Both metrics use custom regex to sort all fetched tags, also only semver compatible tags will be fetched:

|         Metric name         |             Description              | Active labels                         | Type |
|:---------------------------:|:------------------------------------:|---------------------------------------|:----:|
| gitlab_project_rc_tag_info  | The latest release candidate git tag | project_name, tag_version, repository | info |
| gitlab_project_rel_tag_info |      The latest release git tag      | project_name, tag_version, repository | info |


## Sealed secrets
Helm chart supports `SealedSecret` for using encrypted data in `values.yaml`:
```yaml
secrets:
  sealedSecret:
    enabled: true
    annotations:
      sealedsecrets.bitnami.com/cluster-wide: "true"
  data:
    GITLAB_API_TOKEN: "AABxxxx"
```
If you don't need to hide sensitivity data:
```yaml
secrets:
  defaultSecret:
    enabled: true
    annotations: {}
  data:
    GITLAB_API_TOKEN: "TOKENxxx"
```

## Local testing

### Requirements
* Python 3.10+
* Libs from requirements.txt file.

### Local run

```bash
export GITLAB_API_TOKEN=your_token
./git_tag_exporter.py -c ./config/config.yaml
```

Be aware, that for local testing we use `config/config.yaml`, for k8s deployment config file is being generated from `exporterConfig` from `values.yaml`.