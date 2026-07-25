import numpy as np
import pandas as pd
import pickle
import os
import logging
from typing import Tuple, Dict, Any, List

from sklearn.impute import KNNImputer
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Silence tensorflow logging spam
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM, Dropout

logger = logging.getLogger("ForecastingEngine")

# Check GPU availability
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logger.info(f"NVIDIA GPU detected and configured: {gpus}")
    except RuntimeError as e:
        logger.warning(f"Error configuring GPU: {e}")
else:
    logger.info("TensorFlow running on CPU (No GPU detected).")

class ForecasterPipeline:
    FEATURES = [
        'Open', 'High', 'Low', 'Volume', 'RSI', 'MACD', 'MACD_Signal',
        'MACD_Diff', 'SMA_200', 'SMA_100', 'SMA_50', 'Stoch_K', 'Stoch_D',
        'ATR', 'Weighted_Sentiment', 'Inflation', 'Unemployment'
    ]
    TARGET = 'Returns'

    def __init__(self, model_dir: str = "backend/data/models"):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self.rf_model = None
        self.lstm_model = None
        self.feature_scaler = MinMaxScaler(feature_range=(0, 1))
        self.target_scaler = MinMaxScaler(feature_range=(0, 1))
        self.imputer = KNNImputer(n_neighbors=5)

    def preprocess_data(self, df: pd.DataFrame, is_training: bool = True) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Extracts features and target, performs KNN imputation, and calculates Returns.
        """
        df_clean = df.copy()
        
        # Calculate daily log returns: ln(Close_t / Close_t-1)
        if 'Close' in df_clean.columns:
            df_clean['Returns'] = np.log(df_clean['Close'] / df_clean['Close'].shift(1))
            df_clean['Returns'] = df_clean['Returns'].fillna(0.0)
        else:
            df_clean['Returns'] = 0.0

        # Ensure all columns exist
        for col in self.FEATURES + [self.TARGET]:
            if col not in df_clean.columns:
                # Add placeholder if missing
                df_clean[col] = 0.0

        # Extract X and y
        X = df_clean[self.FEATURES]
        y = df_clean[self.TARGET]

        # KNN Imputation
        if is_training:
            logger.info("Fitting KNNImputer on features...")
            X_imputed = self.imputer.fit_transform(X)
        else:
            X_imputed = self.imputer.transform(X)

        X_df = pd.DataFrame(X_imputed, columns=self.FEATURES)
        return X_df, y

    def train_random_forest(self, X: pd.DataFrame, y: pd.Series, prices: pd.Series) -> Dict[str, Any]:
        """
        Trains a Random Forest Regressor on returns, and evaluates it on reconstructed test prices.
        """
        logger.info("Training Random Forest Regressor...")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
        _, prices_test = train_test_split(prices, test_size=0.2, random_state=42, shuffle=False)

        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        
        # Predictions (Returns)
        y_pred_test = rf.predict(X_test)

        # Reconstruct price validation metrics from returns
        # Price_pred_t = Price_prev_t * e^(Return_pred_t)
        prices_prev = prices_test.shift(1).fillna(prices_test.iloc[0])
        prices_pred = prices_prev * np.exp(y_pred_test)

        prices_actual = prices_test.values
        prices_predicted = prices_pred.values

        # Metrics
        mse = mean_squared_error(prices_actual, prices_predicted)
        mae = mean_absolute_error(prices_actual, prices_predicted)
        r2 = r2_score(prices_actual, prices_predicted)

        # Directional Accuracy (is direction of predicted return matching direction of actual return?)
        # Direction: return goes up > 0, down < 0
        y_test_diff = np.sign(y_test.values)
        y_pred_diff = np.sign(y_pred_test)
        dir_accuracy = float(np.sum(y_test_diff == y_pred_diff) / len(y_test_diff)) if len(y_test_diff) > 0 else 0.0

        self.rf_model = rf
        
        # Save RF model to disk
        with open(os.path.join(self.model_dir, "rf_model.pkl"), "wb") as f:
            pickle.dump(rf, f)
        with open(os.path.join(self.model_dir, "imputer.pkl"), "wb") as f:
            pickle.dump(self.imputer, f)

        logger.info(f"Random Forest Training complete. Test MSE: {mse:.4f}, Dir Acc: {dir_accuracy*100:.2f}%")
        
        return {
            "model_type": "Random Forest",
            "mse": float(mse),
            "mae": float(mae),
            "r2": float(r2),
            "directional_accuracy": dir_accuracy,
            "test_actual": prices_actual.tolist(),
            "test_predicted": prices_predicted.tolist()
        }

    def train_lstm(self, X: pd.DataFrame, y: pd.Series, prices: pd.Series, epochs: int = 15, batch_size: int = 32, time_step: int = 50) -> Dict[str, Any]:
        """
        Prepares sequences and trains an LSTM neural network on returns.
        Leverages GPU if available. Evaluates on reconstructed Close prices.
        """
        logger.info(f"Training LSTM model (time_step={time_step})...")
        
        # Scale data
        X_scaled = self.feature_scaler.fit_transform(X)
        y_scaled = self.target_scaler.fit_transform(y.values.reshape(-1, 1)).flatten()

        # Create sequential dataset including aligned prices
        X_seq, y_seq, p_seq = [], [], []
        for i in range(len(X_scaled) - time_step - 1):
            X_seq.append(X_scaled[i : (i + time_step)])
            y_seq.append(y_scaled[i + time_step])
            p_seq.append(prices.iloc[i + time_step])
        X_seq, y_seq, p_seq = np.array(X_seq), np.array(y_seq), np.array(p_seq)

        if len(X_seq) == 0:
            raise ValueError("Dataset is too small to form sequential steps for LSTM. Reduce time_step or fetch more data.")

        # Split sequence data
        split_idx = int(len(X_seq) * 0.8)
        X_train, X_test = X_seq[:split_idx], X_seq[split_idx:]
        y_train, y_test = y_seq[:split_idx], y_seq[split_idx:]
        prices_test = p_seq[split_idx:]

        # Reshape for LSTM: [samples, time_steps, features]
        X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], len(self.FEATURES))
        X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], len(self.FEATURES))

        # Model design
        model = Sequential()
        model.add(LSTM(50, return_sequences=True, input_shape=(time_step, len(self.FEATURES))))
        model.add(Dropout(0.2))
        model.add(LSTM(50, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(25))
        model.add(Dense(1))

        model.compile(optimizer='adam', loss='mean_squared_error')
        
        # Fit model
        model.fit(
            X_train, y_train, 
            epochs=epochs, 
            batch_size=batch_size, 
            validation_data=(X_test, y_test),
            verbose=0
        )

        # Predictions (Scaled Returns)
        y_pred_test_scaled = model.predict(X_test).flatten()
        
        # Rescale predictions back to returns
        y_pred_test_returns = self.target_scaler.inverse_transform(y_pred_test_scaled.reshape(-1, 1)).flatten()
        y_test_returns = self.target_scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()

        # Reconstruct predicted Close prices from predicted returns:
        # Price_pred_t = Price_prev_t * e^(Return_pred_t)
        prices_prev = []
        for i in range(split_idx, len(X_seq)):
            prices_prev.append(prices.iloc[i + time_step - 1])
        prices_prev = np.array(prices_prev)

        prices_predicted = prices_prev * np.exp(y_pred_test_returns)
        prices_actual = prices_test

        # Metrics
        mse = mean_squared_error(prices_actual, prices_predicted)
        if np.isnan(mse):
            mse = 0.0
        mae = mean_absolute_error(prices_actual, prices_predicted)
        r2 = r2_score(prices_actual, prices_predicted)
        if np.isnan(r2):
            r2 = 0.0

        # Directional Accuracy (is direction of predicted return matching direction of actual return?)
        y_test_diff = np.sign(y_test_returns)
        y_pred_diff = np.sign(y_pred_test_returns)
        dir_accuracy = float(np.sum(y_test_diff == y_pred_diff) / len(y_test_diff)) if len(y_test_diff) > 0 else 0.0

        self.lstm_model = model
        
        # Save models
        model.save(os.path.join(self.model_dir, "lstm_model.keras"))
        with open(os.path.join(self.model_dir, "feature_scaler.pkl"), "wb") as f:
            pickle.dump(self.feature_scaler, f)
        with open(os.path.join(self.model_dir, "target_scaler.pkl"), "wb") as f:
            pickle.dump(self.target_scaler, f)

        logger.info(f"LSTM Training complete. Test MSE: {mse:.4f}, Dir Acc: {dir_accuracy*100:.2f}%")

        return {
            "model_type": "LSTM",
            "mse": float(mse),
            "mae": float(mae),
            "r2": float(r2),
            "directional_accuracy": dir_accuracy,
            "test_actual": prices_actual.tolist(),
            "test_predicted": prices_predicted.tolist()
        }

    def predict_future_rf(self, last_row: pd.Series, future_days: int = 5) -> List[float]:
        """
        Predicts close prices using the Random Forest model trained on returns.
        Carries forward last technical features, updates time index, and returns absolute price predictions.
        """
        if self.rf_model is None:
            # Try load model
            rf_path = os.path.join(self.model_dir, "rf_model.pkl")
            if os.path.exists(rf_path):
                with open(rf_path, "rb") as f:
                    self.rf_model = pickle.load(f)
            else:
                raise ValueError("Random Forest model has not been trained or loaded yet.")

        # Set up future DataFrame
        future_X = pd.DataFrame([last_row[self.FEATURES]] * future_days)
        pred_returns = self.rf_model.predict(future_X)
        
        # Convert predicted returns back to absolute Close prices recursively
        last_close = float(last_row['Close'])
        predictions = []
        for r in pred_returns:
            pred_price = last_close * np.exp(r)
            predictions.append(pred_price)
            last_close = pred_price
            
        return predictions

    def predict_future_lstm(self, historical_df: pd.DataFrame, future_days: int = 5, time_step: int = 50) -> List[float]:
        """
        Predicts close prices using the trained LSTM model.
        Requires past `time_step` records to construct the final sequence and predict forward.
        """
        if self.lstm_model is None:
            lstm_path = os.path.join(self.model_dir, "lstm_model.keras")
            if os.path.exists(lstm_path):
                self.lstm_model = load_model(lstm_path)
                with open(os.path.join(self.model_dir, "feature_scaler.pkl"), "rb") as f:
                    self.feature_scaler = pickle.load(f)
                with open(os.path.join(self.model_dir, "target_scaler.pkl"), "rb") as f:
                    self.target_scaler = pickle.load(f)
            else:
                raise ValueError("LSTM model has not been trained or loaded yet.")

        # Ensure we have enough history
        if len(historical_df) < time_step:
            raise ValueError(f"Need at least {time_step} history steps to construct LSTM sequence.")

        # Prep the last time_step data points
        last_df = historical_df.tail(time_step)[self.FEATURES].copy()
        
        # We fetch scaled features:
        scaled_features = self.feature_scaler.transform(last_df)
        
        predictions = []
        current_seq = scaled_features.copy()
        
        # Get the actual last Close price
        last_close = float(historical_df['Close'].iloc[-1])

        for _ in range(future_days):
            # Shape for model: [1, time_steps, features]
            input_seq = current_seq.reshape(1, time_step, len(self.FEATURES))
            pred_scaled = self.lstm_model.predict(input_seq, verbose=0)[0][0]
            
            # Inverse scale to get target return
            pred_return = float(self.target_scaler.inverse_transform([[pred_scaled]])[0][0])
            
            # Convert return to absolute price
            pred_price = last_close * np.exp(pred_return)
            predictions.append(pred_price)
            last_close = pred_price

            # Roll the sequence forward: drop first step, append new step with predicted target.
            # In features, we carry forward the last features, but update the 'Open', 'High', 'Low' with the predicted Close price
            new_row_df = pd.DataFrame([last_df.iloc[-1].copy()])
            new_row_df['Open'] = pred_price
            new_row_df['High'] = pred_price
            new_row_df['Low'] = pred_price
            # Scale the row
            new_step = self.feature_scaler.transform(new_row_df)[0]
            
            current_seq = np.vstack([current_seq[1:], new_step])

        return predictions
