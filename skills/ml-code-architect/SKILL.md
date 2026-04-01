---
name: ml-code-architect
description: Architect ML code following production best practices across the complete ML lifecycle. Use when users want to: (1) structure ML projects from scratch, (2) refactor notebook code into production-ready modules, (3) set up experiment tracking and config management, (4) create training/inference pipelines, (5) add testing and validation to ML code, (6) prepare models for deployment. Triggers on phrases like "architect my ML code", "structure my ML project", "production-ready ML", "refactor notebook to production", "MLOps setup".
---

# ML Code Architect

Architect ML systems by understanding intent first, then applying principles to derive structure.

> **Scope**: This skill covers ML project architecture (system-level structure). For line-level Python code quality (naming, functions, Clean Code rules), defer to the `production-coding` skill.

## Step 1: Understand the Project's Forces

Before writing any code or suggesting structure, understand these forces that shape ML projects:

### What is the project's lifecycle stage?
- **Exploration**: Prioritize speed, iteration, throwaway code is fine
- **Validation**: Need reproducibility, but flexibility still matters
- **Production**: Stability, testing, monitoring become critical
- **Maintenance**: Minimize change surface, clear interfaces

### What changes frequently vs rarely?
- Data sources and schemas
- Feature engineering logic
- Model architectures
- Hyperparameters
- Training infrastructure
- Serving infrastructure

**Principle**: Things that change together should live together. Things that change at different rates should be separated.

### Who interacts with what?
- Data scientists iterating on models
- ML engineers deploying pipelines
- Data engineers managing data flows
- Software engineers integrating predictions

**Principle**: Ownership boundaries should align with team boundaries.

### What are the failure modes?
- Data quality issues
- Training instability
- Serving latency
- Model degradation over time

**Principle**: Each failure mode needs its own detection and recovery mechanism.

## Step 2: Core Architectural Principles

### Principle 1: Separate Configuration from Code

**Why**: Hyperparameters, paths, and settings change constantly. Code should not.

**Indicators you need this**:
- Editing Python files just to change learning rate
- Different values hardcoded for "local" vs "production"
- Can't reproduce an old experiment because settings were lost

**Implementation approaches** (choose based on complexity):
- Simple: YAML/JSON files loaded at startup
- Medium: Hydra for hierarchical configs with CLI overrides
- Complex: Feature flags + config service for runtime changes

### Principle 2: Make Data Flow Explicit

**Why**: ML bugs often hide in implicit data transformations. Explicit pipelines are debuggable.

**Indicators you need this**:
- Unclear what preprocessing happened before training
- Train/serve skew (different transforms in training vs inference)
- Can't trace a prediction back to its input data

**Implementation approaches**:
- Define clear stage boundaries: raw → cleaned → features → predictions
- Each transformation should be a pure function (same input → same output)
- Log data schemas at each boundary

**Key insight**: If you can't draw the data flow on a whiteboard, your code is too tangled.

### Principle 3: Isolate Expensive Operations

**Why**: Training takes hours. You need to iterate on everything else without retraining.

**Indicators you need this**:
- Changing evaluation code requires retraining
- Can't test serving logic without a trained model
- Feature engineering and model training are one monolithic script

**Implementation approaches**:
- Checkpoint intermediate artifacts (processed data, trained models)
- Design interfaces so components can be tested with mocks
- Separate "compute features" from "train model" from "evaluate model"

**Key insight**: The unit of caching should match the unit of change.

### Principle 4: Validate at Pipeline Boundaries

**Why**: Silent data corruption produces models that train successfully but predict garbage.

**Indicators you need this**:
- Model trains but predictions are wrong
- Debugging requires tracing through entire pipeline
- Schema changes upstream break downstream silently

**ML-specific validation points**:
- Schema validation when data enters the system (Pandera, Pydantic)
- Assertion checks after each transformation (shape, dtypes, value ranges)
- Contract between feature pipeline and model input (Great Expectations)

> General fail-fast/validation patterns are in `production-coding`. This principle focuses on ML pipeline boundaries specifically.

### Principle 5: Make Experiments Reproducible

**Why**: "It worked yesterday" is not debugging. You need to recreate exact conditions.

**Indicators you need this**:
- Can't reproduce a good result from last week
- Different team members get different results
- No record of what changed between experiments

**What must be captured**:
- Code version (git commit)
- Configuration (all hyperparameters)
- Data version (hash, timestamp, or DVC pointer)
- Environment (dependencies, hardware)
- Random seeds

**Key insight**: Reproducibility is not optional—it's how you know your improvements are real.

### Principle 6: ML Test Hierarchy

**Why**: ML code has unique testing needs beyond standard unit/integration tests.

**ML-specific test priorities** (in order):
1. Data transformations — unit tests with known inputs/outputs
2. Model produces valid outputs — shape, range, dtype checks
3. Training improves metrics — loss decreases over N steps
4. End-to-end pipeline completes — integration test with small data
5. Model robustness — behavior under input perturbation

> General testability patterns (pure functions, DI, mocking) are in `production-coding`. This focuses on what's unique to ML testing.

## Step 3: Deriving Structure from Principles

Don't copy a template. Ask these questions:

### "What are the natural boundaries in this project?"

Look for:
- Points where data format changes
- Points where different people/teams take over
- Points where you'd want to cache/checkpoint
- Points where you'd want to swap implementations

Each boundary suggests a module or package.

### "What would I need to change to run a new experiment?"

Those things should be:
- In configuration, not code
- Easy to version and compare
- Logged automatically

### "What would break if this data were malformed?"

Those points need:
- Validation logic
- Clear error messages
- Possibly separate error handling code

### "What would I need to mock to test this?"

If the answer is "everything," the code is too coupled. Refactor until you can test pieces in isolation.

### "Who needs to understand this code?"

- Just you? Optimize for your workflow.
- Your team? Need conventions and documentation.
- External users? Need stable interfaces and versioning.

## Step 4: Common Patterns (Not Prescriptions)

These patterns solve recurring problems. Use them when you have the problem, not preemptively.

### Pattern: Config-Driven Training

**Problem**: Hyperparameters scattered across code, can't reproduce experiments.

**Solution**: Single source of truth for all settings, loaded at startup, logged with results.

```python
# The pattern, not the implementation
config = load_config(path_or_cli_args)
log_config(config)  # For reproducibility
model = build_model(config.model)
trainer = Trainer(config.training)
trainer.fit(model, data)
```

### Pattern: Transform Pipeline

**Problem**: Data preprocessing is ad-hoc, train/serve skew.

**Solution**: Composable, serializable transforms that can be applied consistently.

```python
# The pattern
pipeline = Pipeline([
    Transform1(params),
    Transform2(params),
])
pipeline.fit(train_data)
pipeline.save("pipeline.pkl")  # Same object used in training and serving

# Later, in serving
pipeline = Pipeline.load("pipeline.pkl")
features = pipeline.transform(new_data)
```

### Pattern: Model Registry

**Problem**: Multiple model types, selection logic scattered.

**Solution**: Central registration, creation by name.

```python
# The pattern
@register("model_v1")
class ModelV1: ...

@register("model_v2")  
class ModelV2: ...

# Usage
model = create_model(config.model.name, **config.model.params)
```

### Pattern: Checkpoint and Resume

**Problem**: Training crashes lose all progress, can't iterate on evaluation without retraining.

**Solution**: Save state at logical boundaries, design for resumption.

```python
# The pattern
if checkpoint_exists(path):
    state = load_checkpoint(path)
else:
    state = initial_state()

for epoch in range(state.epoch, max_epochs):
    train_one_epoch(state)
    save_checkpoint(state, path)
```

### Pattern: Validation Schemas

**Problem**: Silent data corruption, debugging by print statements.

**Solution**: Explicit schemas at data boundaries, fail fast on violations.

```python
# The pattern
class InputSchema:
    feature_a: float, range(0, 100)
    feature_b: int, not_null
    
def process(data):
    validate(data, InputSchema)  # Fails immediately if invalid
    # ... rest of processing
```

### Pattern: Experiment Tracking

**Problem**: Results in spreadsheets, can't compare runs systematically.

**Solution**: Automatic logging of params, metrics, artifacts with unique run IDs.

```python
# The pattern
with experiment.start_run():
    experiment.log_params(config)
    for epoch in range(epochs):
        metrics = train_epoch()
        experiment.log_metrics(metrics, step=epoch)
    experiment.log_artifact(model_path)
```

## Step 5: Anti-Patterns to Recognize

### "God Script"
One file that does everything: load data, preprocess, train, evaluate, save.

**Problem**: Can't test pieces, can't reuse pieces, can't parallelize.

**Fix**: Identify the stages, extract to functions/modules with clear interfaces.

### "Implicit Configuration"
Settings buried in code, different values in different branches/comments.

**Problem**: Can't reproduce, can't sweep hyperparameters, constant merge conflicts.

**Fix**: Extract ALL settings to config files, load once at entry point.

### "Notebook as Production"
Jupyter notebook deployed or converted to .py without refactoring.

**Problem**: Hidden state, cell order dependencies, can't test, can't version diff.

**Fix**: Notebooks for exploration only. Extract validated logic to modules.

### "Copy-Paste Preprocessing"
Same transformation code in training script and serving code.

**Problem**: Divergence over time (train/serve skew), bugs fixed in one place only.

**Fix**: Single implementation, imported by both training and serving.

## Step 6: Questions to Ask the User

Before architecting, understand:

1. **What's the end goal?** (Research paper, production service, one-off analysis)
2. **Who else will work on this?** (Solo, small team, large org)
3. **What's the iteration cycle?** (Hourly experiments, weekly releases, continuous)
4. **What's the deployment target?** (Notebook, batch job, real-time API, edge device)
5. **What existing infrastructure must you integrate with?**
6. **What's the expected lifetime?** (Throwaway, months, years)

The answers shape every architectural decision.

## Quick Reference: Tool Selection

| Need | Simple | Medium | Complex |
|------|--------|--------|---------|
| Config management | YAML + argparse | Hydra | Custom config service |
| Experiment tracking | CSV/JSON logs | MLflow | Weights & Biases + custom |
| Data validation | Assert statements | Pydantic/Pandera | Great Expectations |
| Data versioning | Git (small data) | DVC | Delta Lake / lakeFS |
| Model serving | Script | FastAPI + Docker | Kubernetes + autoscaling |
| Testing | pytest basics | pytest + fixtures | pytest + hypothesis + CI |

**Choose based on actual needs, not anticipated needs.** Start simple, add complexity when pain emerges.

## References

For detailed tool-specific guidance, see:
- `references/tools-reference.md` - Deep dives on Hydra, MLflow, DVC, Pydantic, pytest, FastAPI
- `references/patterns.md` - Reusable code patterns with full implementations
