# ML Tools Reference

Detailed guidance on tools commonly used in production ML systems.

## Configuration Management Tools

### Hydra (Recommended)

**When to use**: Any project with more than a handful of hyperparameters.

**Key features**:
- Hierarchical config composition
- CLI overrides without code changes
- Multi-run sweeps (`--multirun`)
- Output directory management

**Config composition example**:
```yaml
# configs/config.yaml
defaults:
  - model: resnet50      # pulls from configs/model/resnet50.yaml
  - optimizer: adam      # pulls from configs/optimizer/adam.yaml
  - scheduler: cosine    # pulls from configs/scheduler/cosine.yaml
  - _self_               # this file's values override defaults

# Override any nested value
model:
  pretrained: true
```

**Package groups** (select one from a set):
```yaml
# configs/model/resnet50.yaml
# @package _global_
model:
  name: resnet50
  num_layers: 50
  
# configs/model/vgg16.yaml
# @package _global_
model:
  name: vgg16
  num_layers: 16
```

**Structured configs** (type-safe):
```python
from dataclasses import dataclass
from hydra.core.config_store import ConfigStore

@dataclass
class ModelConfig:
    name: str = "resnet50"
    pretrained: bool = True
    num_classes: int = 1000

@dataclass
class TrainingConfig:
    batch_size: int = 32
    learning_rate: float = 1e-3
    epochs: int = 100

@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)

cs = ConfigStore.instance()
cs.store(name="config", node=Config)
```

### OmegaConf

Hydra uses OmegaConf under the hood. Key features:

```python
from omegaconf import OmegaConf, DictConfig

# Variable interpolation
cfg = OmegaConf.create({
    "base_dir": "/data",
    "train_path": "${base_dir}/train",  # Resolves to /data/train
})

# Environment variables
cfg = OmegaConf.create({
    "api_key": "${oc.env:API_KEY}",
    "data_dir": "${oc.env:DATA_DIR,./data}",  # with default
})

# Convert to dict/yaml
OmegaConf.to_container(cfg, resolve=True)  # dict with resolved values
OmegaConf.to_yaml(cfg)  # yaml string
```

## Experiment Tracking Tools

### MLflow

**Setup**:
```python
import mlflow

# Local tracking (default)
mlflow.set_tracking_uri("file:./mlruns")

# Remote tracking server
mlflow.set_tracking_uri("http://mlflow-server:5000")
```

**Complete logging pattern**:
```python
def train_model(cfg):
    mlflow.set_experiment(cfg.experiment_name)
    
    with mlflow.start_run(run_name=cfg.run_name):
        # Log all params
        mlflow.log_params(flatten_dict(cfg))
        
        # Set tags for filtering
        mlflow.set_tags({
            "model_type": cfg.model.name,
            "dataset": cfg.data.name,
            "git_commit": get_git_hash(),
        })
        
        model = build_model(cfg)
        
        for epoch in range(cfg.epochs):
            metrics = train_epoch(model, ...)
            
            # Log metrics with step
            mlflow.log_metrics(metrics, step=epoch)
            
            # Log artifacts periodically
            if epoch % 10 == 0:
                save_checkpoint(model, f"checkpoint_{epoch}.pt")
                mlflow.log_artifact(f"checkpoint_{epoch}.pt")
        
        # Log final model
        mlflow.pytorch.log_model(
            model, 
            "model",
            registered_model_name=cfg.model.name
        )
        
        # Log any files
        mlflow.log_artifacts("outputs/plots")
```

**Model registry**:
```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Register model
model_uri = f"runs:/{run_id}/model"
mv = client.create_model_version(
    name="my-model",
    source=model_uri,
    run_id=run_id
)

# Transition stage
client.transition_model_version_stage(
    name="my-model",
    version=mv.version,
    stage="Production"
)

# Load production model
model = mlflow.pytorch.load_model("models:/my-model/Production")
```

### DVC (Data Version Control)

**When to use**: Large datasets/models that don't fit in Git.

**Basic workflow**:
```bash
# Initialize DVC in Git repo
dvc init
git add .dvc .dvcignore
git commit -m "Initialize DVC"

# Add remote storage
dvc remote add -d myremote s3://mybucket/dvc-store

# Track large files
dvc add data/raw/dataset.parquet
git add data/raw/dataset.parquet.dvc data/raw/.gitignore
git commit -m "Track dataset"

# Push data to remote
dvc push

# Pull data (on another machine)
dvc pull
```

**DVC Pipelines** (dvc.yaml):
```yaml
stages:
  preprocess:
    cmd: python src/data/preprocess.py
    deps:
      - src/data/preprocess.py
      - data/raw/
    outs:
      - data/processed/
    params:
      - preprocess.min_samples
      - preprocess.test_split

  train:
    cmd: python scripts/train.py
    deps:
      - scripts/train.py
      - src/models/
      - data/processed/
    params:
      - model
      - training
    outs:
      - models/model.pt
    metrics:
      - metrics.json:
          cache: false
    plots:
      - plots/loss.csv:
          x: epoch
          y: loss
```

```bash
# Run pipeline (only changed stages)
dvc repro

# Compare experiments
dvc exp run --set-param training.lr=0.001
dvc exp show
dvc exp diff
```

## Data Validation Tools

### Pydantic v2

**For API inputs and configs**:
```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal

class ModelConfig(BaseModel):
    name: Literal["resnet", "vgg", "efficientnet"]
    num_layers: int = Field(ge=1, le=200)
    dropout: float = Field(ge=0, le=1, default=0.5)
    
    @field_validator('num_layers')
    @classmethod
    def validate_layers(cls, v, info):
        name = info.data.get('name')
        if name == 'resnet' and v not in [18, 34, 50, 101, 152]:
            raise ValueError(f"ResNet only supports 18/34/50/101/152 layers")
        return v

class TrainingRequest(BaseModel):
    features: list[list[float]]
    labels: list[int] | None = None
    
    @model_validator(mode='after')
    def check_shapes(self):
        if self.labels is not None:
            if len(self.features) != len(self.labels):
                raise ValueError("Features and labels must have same length")
        return self
```

### Pandera

**For DataFrame validation**:
```python
import pandera as pa
from pandera.typing import DataFrame, Series
import pandas as pd

class RawDataSchema(pa.DataFrameModel):
    id: Series[int] = pa.Field(unique=True, ge=0)
    timestamp: Series[pa.Timestamp]
    feature_a: Series[float] = pa.Field(ge=0, le=100)
    feature_b: Series[float] = pa.Field(nullable=True)
    target: Series[int] = pa.Field(isin=[0, 1])
    
    class Config:
        strict = True  # No extra columns allowed
        coerce = True  # Attempt type coercion

# Use as decorator
@pa.check_types
def load_data(path: str) -> DataFrame[RawDataSchema]:
    df = pd.read_parquet(path)
    return df  # Validation happens automatically

# Or validate explicitly
RawDataSchema.validate(df)
```

**Custom checks**:
```python
class TrainingDataSchema(pa.DataFrameModel):
    feature: Series[float]
    label: Series[int]
    
    @pa.check("feature")
    def no_outliers(cls, series: pd.Series) -> bool:
        z_scores = (series - series.mean()) / series.std()
        return (z_scores.abs() < 5).all()
    
    @pa.dataframe_check
    def balanced_classes(cls, df: pd.DataFrame) -> bool:
        counts = df["label"].value_counts()
        ratio = counts.min() / counts.max()
        return ratio > 0.1  # At least 10% minority class
```

### Great Expectations

**For production data pipelines**:
```python
import great_expectations as gx

# Create context
context = gx.get_context()

# Add data source
datasource = context.sources.add_pandas("my_datasource")
asset = datasource.add_dataframe_asset("training_data")

# Build expectation suite
batch = asset.build_batch_request()
validator = context.get_validator(batch_request=batch)

# Define expectations
validator.expect_column_to_exist("feature_a")
validator.expect_column_values_to_be_between("feature_a", min_value=0, max_value=100)
validator.expect_column_values_to_not_be_null("target")
validator.expect_column_distinct_values_to_be_in_set("target", [0, 1])

# Save suite
validator.save_expectation_suite()

# Run validation
checkpoint = context.add_or_update_checkpoint(
    name="training_checkpoint",
    validations=[{"batch_request": batch, "expectation_suite_name": "training_suite"}]
)
result = checkpoint.run()
```

## Testing Tools

### pytest

**Fixtures for ML**:
```python
# conftest.py
import pytest
import torch
import numpy as np

@pytest.fixture(scope="session")
def seed():
    """Set random seeds for reproducibility."""
    torch.manual_seed(42)
    np.random.seed(42)
    return 42

@pytest.fixture(scope="session")
def sample_data():
    """Small dataset for testing."""
    X = np.random.randn(100, 10).astype(np.float32)
    y = (X[:, 0] > 0).astype(np.int64)
    return X, y

@pytest.fixture(scope="module")
def trained_model(sample_data):
    """Pre-trained model for inference tests."""
    X, y = sample_data
    model = SimpleModel()
    model.fit(X, y)
    return model

@pytest.fixture
def temp_checkpoint(tmp_path):
    """Temporary directory for checkpoints."""
    return tmp_path / "checkpoints"
```

**Parameterized tests**:
```python
@pytest.mark.parametrize("model_name,expected_params", [
    ("resnet18", 11_689_512),
    ("resnet50", 25_557_032),
])
def test_model_parameters(model_name, expected_params):
    model = create_model(model_name)
    actual = sum(p.numel() for p in model.parameters())
    assert actual == expected_params

@pytest.mark.parametrize("batch_size", [1, 16, 64])
@pytest.mark.parametrize("input_size", [(224, 224), (256, 256)])
def test_forward_pass(model, batch_size, input_size):
    x = torch.randn(batch_size, 3, *input_size)
    output = model(x)
    assert output.shape == (batch_size, 1000)
```

**Markers for test organization**:
```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "gpu: marks tests requiring GPU",
    "integration: marks integration tests",
]

# tests
@pytest.mark.slow
def test_full_training():
    ...

@pytest.mark.gpu
@pytest.mark.skipif(not torch.cuda.is_available(), reason="No GPU")
def test_gpu_inference():
    ...
```

## Deployment Tools

### FastAPI

**Production-ready patterns**:
```python
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

# Lifespan for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Loading model...")
    app.state.model = load_model()
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="ML Inference API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
def get_model():
    return app.state.model

@app.post("/predict")
async def predict(
    request: PredictRequest,
    model = Depends(get_model),
    background_tasks: BackgroundTasks = None
):
    result = model.predict(request.features)
    
    # Log prediction async
    background_tasks.add_task(log_prediction, request, result)
    
    return {"prediction": result}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/ready")
async def ready(model = Depends(get_model)):
    if model is None:
        raise HTTPException(503, "Model not loaded")
    return {"status": "ready"}
```

### Docker

**Multi-stage build**:
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd --create-home appuser
USER appuser

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser models/ ./models/

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Code Quality Tools

### pyproject.toml (unified config)

```toml
[project]
name = "ml-project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "torch>=2.0",
    "hydra-core>=1.3",
    "mlflow>=2.0",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
    "ruff",
    "black",
    "mypy",
    "pre-commit",
]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "B", "C4", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

### pre-commit hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```
