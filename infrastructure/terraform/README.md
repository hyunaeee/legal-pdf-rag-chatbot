# Google Cloud deployment

This Terraform stack provisions the minimum Google Cloud resources required by the current application:

- Artifact Registry Docker repository
- Dedicated Cloud Run runtime service account
- Vertex AI and observability IAM roles
- Private Cloud Run v2 service with health probes and bounded scaling

The service is private by default. Set `allow_unauthenticated = true` only for a deliberate public demo.

## 1. Build and push the image

```bash
PROJECT_ID="your-project"
REGION="asia-northeast3"
REPOSITORY="enterprise-ai"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/enterprise-policy-agent:latest"

gcloud builds submit --tag "${IMAGE}" .
```

The Artifact Registry repository must exist before the first push. Apply Terraform once with an existing bootstrap image, or create the repository first and then perform the final apply.

## 2. Configure Terraform

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -check
terraform validate
terraform plan
terraform apply
```

## 3. Invoke the private service

```bash
SERVICE_URI="$(terraform output -raw service_uri)"
TOKEN="$(gcloud auth print-identity-token)"

curl -H "Authorization: Bearer ${TOKEN}" "${SERVICE_URI}/health"
```

## Operational notes

- Vertex AI uses Application Default Credentials from the Cloud Run service account; no API key is stored in the container.
- `EPA_REQUIRE_TENANT_HEADER` is enabled, but the header is only a namespace input. Production identity middleware must map an authenticated principal to an allowed tenant rather than trusting a caller-provided value.
- The SQLite structured-data adapter is a local demonstration backend. A production deployment should replace it with Cloud SQL, AlloyDB, or another durable service through the repository interface.
- OTLP export is disabled until a reachable collector endpoint is supplied.
