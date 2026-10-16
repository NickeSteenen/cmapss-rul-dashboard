import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn import metrics
import joblib

from project_settings import COMPLETE_TRAINING_DATA_PATH, MODEL_PATH

NON_FEATURE_COLUMNS = ["RUL", "unit", "source_dataset"]  # RUL is the target, and unit and source_dataset only identify the engine


def split_features_and_target(df):
    X = df.drop(columns=NON_FEATURE_COLUMNS)
    y = df["RUL"]
    return X, y


def split_train_validation(X, y, groups, test_size=0.2, random_state=42):
    # Split by whole engine, so no engine's cycles end up on both sides
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, val_idx = next(splitter.split(X, y, groups=groups))
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
    return X_train, X_val, y_train, y_val


def train_model(X_train, y_train, **rf_kwargs):
    model = RandomForestRegressor(random_state=42, **rf_kwargs)
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_val, y_val):
    predictions = model.predict(X_val)
    mae = metrics.mean_absolute_error(y_val, predictions)
    rmse = metrics.root_mean_squared_error(y_val, predictions)
    print(f"Validation MAE: {mae:.2f} cycles")
    print(f"Validation RMSE: {rmse:.2f} cycles")
    return mae, rmse


def save_model(model, path):
    joblib.dump(model, path)
    print(f"Model saved to {path}")


if __name__ == "__main__":
    df = pd.read_csv(COMPLETE_TRAINING_DATA_PATH)
    engine_ids = df["source_dataset"] + "_" + df["unit"].astype(str)  # unit numbers restart at 1 in every dataset
    X, y = split_features_and_target(df)
    X_train, X_val, y_train, y_val = split_train_validation(X, y, groups=engine_ids)
    model = train_model(X_train, y_train)
    evaluate_model(model, X_val, y_val)
    save_model(model, MODEL_PATH)
