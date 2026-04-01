# ML Architecture Patterns

Common patterns for different ML project scenarios.

## Pattern 1: Training Pipeline

Standard training loop with proper abstractions.

```python
# src/models/trainer.py
from dataclasses import dataclass
from typing import Protocol, Callable
import torch
from torch.utils.data import DataLoader

class MetricLogger(Protocol):
    def log(self, metrics: dict, step: int) -> None: ...

@dataclass
class TrainerConfig:
    epochs: int
    device: str
    grad_clip: float | None = None
    log_interval: int = 10

class Trainer:
    def __init__(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        criterion: Callable,
        config: TrainerConfig,
        logger: MetricLogger | None = None,
    ):
        self.model = model.to(config.device)
        self.optimizer = optimizer
        self.criterion = criterion
        self.config = config
        self.logger = logger
        self.global_step = 0
    
    def train_epoch(self, loader: DataLoader) -> dict:
        self.model.train()
        total_loss = 0.0
        
        for batch_idx, (data, target) in enumerate(loader):
            data = data.to(self.config.device)
            target = target.to(self.config.device)
            
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)
            loss.backward()
            
            if self.config.grad_clip:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), 
                    self.config.grad_clip
                )
            
            self.optimizer.step()
            total_loss += loss.item()
            self.global_step += 1
            
            if self.logger and batch_idx % self.config.log_interval == 0:
                self.logger.log({"train_loss": loss.item()}, self.global_step)
        
        return {"train_loss": total_loss / len(loader)}
    
    @torch.no_grad()
    def evaluate(self, loader: DataLoader) -> dict:
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        for data, target in loader:
            data = data.to(self.config.device)
            target = target.to(self.config.device)
            
            output = self.model(data)
            loss = self.criterion(output, target)
            total_loss += loss.item()
            
            pred = output.argmax(dim=1)
            correct += (pred == target).sum().item()
            total += target.size(0)
        
        return {
            "val_loss": total_loss / len(loader),
            "val_accuracy": correct / total,
        }
    
    def fit(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        callbacks: list | None = None,
    ) -> dict:
        best_val_loss = float("inf")
        
        for epoch in range(self.config.epochs):
            train_metrics = self.train_epoch(train_loader)
            val_metrics = self.evaluate(val_loader)
            
            metrics = {**train_metrics, **val_metrics, "epoch": epoch}
            
            if self.logger:
                self.logger.log(metrics, self.global_step)
            
            if val_metrics["val_loss"] < best_val_loss:
                best_val_loss = val_metrics["val_loss"]
                # Save checkpoint
            
            if callbacks:
                for callback in callbacks:
                    callback(epoch, metrics)
        
        return {"best_val_loss": best_val_loss}
```

## Pattern 2: Dataset with Transforms

Composable dataset with train/val/test splits.

```python
# src/data/dataset.py
from pathlib import Path
from typing import Callable
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, random_split

class TabularDataset(Dataset):
    def __init__(
        self,
        data: pd.DataFrame,
        target_col: str,
        feature_cols: list[str] | None = None,
        transform: Callable | None = None,
    ):
        self.feature_cols = feature_cols or [
            c for c in data.columns if c != target_col
        ]
        self.features = torch.tensor(
            data[self.feature_cols].values, 
            dtype=torch.float32
        )
        self.targets = torch.tensor(
            data[target_col].values, 
            dtype=torch.long
        )
        self.transform = transform
    
    def __len__(self) -> int:
        return len(self.targets)
    
    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.features[idx]
        y = self.targets[idx]
        
        if self.transform:
            x = self.transform(x)
        
        return x, y

def create_dataloaders(
    df: pd.DataFrame,
    target_col: str,
    batch_size: int,
    val_split: float = 0.2,
    test_split: float = 0.1,
    seed: int = 42,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    """Create train/val/test dataloaders from DataFrame."""
    
    dataset = TabularDataset(df, target_col)
    
    # Calculate sizes
    n = len(dataset)
    n_test = int(n * test_split)
    n_val = int(n * val_split)
    n_train = n - n_test - n_val
    
    # Split
    generator = torch.Generator().manual_seed(seed)
    train_ds, val_ds, test_ds = random_split(
        dataset, 
        [n_train, n_val, n_test],
        generator=generator
    )
    
    # Create loaders
    train_loader = DataLoader(
        train_ds, 
        batch_size=batch_size, 
        shuffle=True,
        num_workers=4,
        pin_memory=True,
    )
    val_loader = DataLoader(
        val_ds, 
        batch_size=batch_size,
        num_workers=4,
    )
    test_loader = DataLoader(
        test_ds, 
        batch_size=batch_size,
        num_workers=4,
    )
    
    return train_loader, val_loader, test_loader
```

## Pattern 3: Model Registry

Factory pattern for model creation.

```python
# src/models/registry.py
from typing import Callable, TypeVar
import torch.nn as nn

T = TypeVar('T', bound=nn.Module)

class ModelRegistry:
    """Registry for model architectures."""
    
    _models: dict[str, Callable[..., nn.Module]] = {}
    
    @classmethod
    def register(cls, name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator to register a model."""
        def wrapper(model_cls: Callable[..., T]) -> Callable[..., T]:
            cls._models[name] = model_cls
            return model_cls
        return wrapper
    
    @classmethod
    def create(cls, name: str, **kwargs) -> nn.Module:
        """Create a model by name."""
        if name not in cls._models:
            raise ValueError(
                f"Model '{name}' not found. "
                f"Available: {list(cls._models.keys())}"
            )
        return cls._models[name](**kwargs)
    
    @classmethod
    def list_models(cls) -> list[str]:
        """List all registered models."""
        return list(cls._models.keys())

# Usage
@ModelRegistry.register("mlp")
class MLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )
    
    def forward(self, x):
        return self.layers(x)

@ModelRegistry.register("deep_mlp")
class DeepMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: list[int], output_dim: int):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for dim in hidden_dims:
            layers.extend([nn.Linear(prev_dim, dim), nn.ReLU(), nn.Dropout(0.1)])
            prev_dim = dim
        layers.append(nn.Linear(prev_dim, output_dim))
        self.layers = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.layers(x)

# In training script
model = ModelRegistry.create(
    cfg.model.name,
    input_dim=cfg.model.input_dim,
    hidden_dim=cfg.model.hidden_dim,
    output_dim=cfg.model.output_dim,
)
```

## Pattern 4: Callbacks System

Extensible training callbacks.

```python
# src/models/callbacks.py
from abc import ABC, abstractmethod
from pathlib import Path
import torch

class Callback(ABC):
    @abstractmethod
    def on_epoch_end(self, epoch: int, metrics: dict) -> bool:
        """Called at end of each epoch. Return False to stop training."""
        pass

class EarlyStopping(Callback):
    def __init__(
        self, 
        patience: int = 10, 
        min_delta: float = 0.0,
        metric: str = "val_loss",
        mode: str = "min",
    ):
        self.patience = patience
        self.min_delta = min_delta
        self.metric = metric
        self.mode = mode
        self.best = float("inf") if mode == "min" else float("-inf")
        self.counter = 0
    
    def on_epoch_end(self, epoch: int, metrics: dict) -> bool:
        current = metrics[self.metric]
        
        if self.mode == "min":
            improved = current < self.best - self.min_delta
        else:
            improved = current > self.best + self.min_delta
        
        if improved:
            self.best = current
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                print(f"Early stopping at epoch {epoch}")
                return False
        
        return True

class ModelCheckpoint(Callback):
    def __init__(
        self,
        model: torch.nn.Module,
        save_dir: Path,
        metric: str = "val_loss",
        mode: str = "min",
    ):
        self.model = model
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.metric = metric
        self.mode = mode
        self.best = float("inf") if mode == "min" else float("-inf")
    
    def on_epoch_end(self, epoch: int, metrics: dict) -> bool:
        current = metrics[self.metric]
        
        if self.mode == "min":
            improved = current < self.best
        else:
            improved = current > self.best
        
        if improved:
            self.best = current
            path = self.save_dir / f"best_model.pt"
            torch.save(self.model.state_dict(), path)
            print(f"Saved best model at epoch {epoch} ({self.metric}={current:.4f})")
        
        return True

class LearningRateScheduler(Callback):
    def __init__(self, scheduler):
        self.scheduler = scheduler
    
    def on_epoch_end(self, epoch: int, metrics: dict) -> bool:
        self.scheduler.step()
        return True
```

## Pattern 5: Feature Pipeline

Composable feature transformations.

```python
# src/features/pipeline.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder

T = TypeVar('T', pd.DataFrame, np.ndarray)

class Transform(ABC):
    @abstractmethod
    def fit(self, X: T) -> 'Transform':
        pass
    
    @abstractmethod
    def transform(self, X: T) -> T:
        pass
    
    def fit_transform(self, X: T) -> T:
        return self.fit(X).transform(X)

class Pipeline:
    def __init__(self, transforms: list[Transform]):
        self.transforms = transforms
    
    def fit(self, X: T) -> 'Pipeline':
        for t in self.transforms:
            X = t.fit_transform(X)
        return self
    
    def transform(self, X: T) -> T:
        for t in self.transforms:
            X = t.transform(X)
        return X

class ColumnSelector(Transform):
    def __init__(self, columns: list[str]):
        self.columns = columns
    
    def fit(self, X: pd.DataFrame) -> 'ColumnSelector':
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        return X[self.columns].copy()

class NullFiller(Transform):
    def __init__(self, strategy: str = "mean"):
        self.strategy = strategy
        self.fill_values: dict = {}
    
    def fit(self, X: pd.DataFrame) -> 'NullFiller':
        for col in X.columns:
            if self.strategy == "mean":
                self.fill_values[col] = X[col].mean()
            elif self.strategy == "median":
                self.fill_values[col] = X[col].median()
            elif self.strategy == "mode":
                self.fill_values[col] = X[col].mode()[0]
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col, val in self.fill_values.items():
            X[col] = X[col].fillna(val)
        return X

class Normalizer(Transform):
    def __init__(self):
        self.scaler = StandardScaler()
    
    def fit(self, X: pd.DataFrame) -> 'Normalizer':
        self.scaler.fit(X)
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            self.scaler.transform(X),
            columns=X.columns,
            index=X.index,
        )

# Usage
pipeline = Pipeline([
    ColumnSelector(["age", "income", "score"]),
    NullFiller(strategy="median"),
    Normalizer(),
])

X_train = pipeline.fit_transform(train_df)
X_test = pipeline.transform(test_df)
```

## Pattern 6: Inference Service

Production inference with batching and caching.

```python
# src/serving/inference.py
from functools import lru_cache
from typing import TypeVar
import torch
import numpy as np
from concurrent.futures import ThreadPoolExecutor

T = TypeVar('T')

class InferenceService:
    def __init__(
        self,
        model_path: str,
        device: str = "cuda",
        batch_size: int = 32,
        max_workers: int = 4,
    ):
        self.device = device
        self.batch_size = batch_size
        self.model = self._load_model(model_path)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def _load_model(self, path: str) -> torch.nn.Module:
        model = torch.jit.load(path)
        model.to(self.device)
        model.eval()
        return model
    
    @torch.no_grad()
    def predict_batch(self, inputs: np.ndarray) -> np.ndarray:
        """Predict on a batch of inputs."""
        tensor = torch.tensor(inputs, dtype=torch.float32, device=self.device)
        outputs = self.model(tensor)
        return outputs.cpu().numpy()
    
    def predict(self, inputs: list[list[float]]) -> list[dict]:
        """Predict with automatic batching."""
        inputs_array = np.array(inputs)
        results = []
        
        for i in range(0, len(inputs_array), self.batch_size):
            batch = inputs_array[i:i + self.batch_size]
            batch_outputs = self.predict_batch(batch)
            
            for output in batch_outputs:
                results.append({
                    "prediction": int(output.argmax()),
                    "probabilities": output.tolist(),
                })
        
        return results
    
    async def predict_async(self, inputs: list[list[float]]) -> list[dict]:
        """Async prediction for high concurrency."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.predict, inputs)
    
    def warmup(self, sample_input: np.ndarray) -> None:
        """Warm up the model with a sample input."""
        for _ in range(3):
            self.predict_batch(sample_input)
```

## Pattern 7: Experiment Comparison

Compare and analyze experiments.

```python
# src/evaluation/compare.py
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient

def compare_experiments(
    experiment_name: str,
    metric: str = "val_loss",
    top_k: int = 5,
) -> pd.DataFrame:
    """Compare top runs from an experiment."""
    client = MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=[f"metrics.{metric} ASC"],
        max_results=top_k,
    )
    
    data = []
    for run in runs:
        row = {
            "run_id": run.info.run_id[:8],
            "run_name": run.info.run_name,
            metric: run.data.metrics.get(metric),
            "duration_min": (
                run.info.end_time - run.info.start_time
            ) / 60000 if run.info.end_time else None,
        }
        # Add relevant params
        for key in ["model.name", "training.learning_rate", "training.batch_size"]:
            row[key] = run.data.params.get(key)
        data.append(row)
    
    return pd.DataFrame(data)

def get_best_model_uri(
    experiment_name: str,
    metric: str = "val_loss",
    ascending: bool = True,
) -> str:
    """Get the model URI for the best run."""
    client = MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    
    order = "ASC" if ascending else "DESC"
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=[f"metrics.{metric} {order}"],
        max_results=1,
    )
    
    if not runs:
        raise ValueError(f"No runs found in experiment {experiment_name}")
    
    return f"runs:/{runs[0].info.run_id}/model"
```

## Pattern 8: Logging Setup

Structured logging for ML projects.

```python
# src/utils/logging.py
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(
    name: str = "ml",
    level: int = logging.INFO,
    log_dir: Path | None = None,
) -> logging.Logger:
    """Configure structured logging."""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    
    # Format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(log_dir / f"{name}_{timestamp}.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Usage
logger = setup_logging("training", log_dir=Path("outputs/logs"))
logger.info("Starting training", extra={"epoch": 1, "lr": 0.001})
```
