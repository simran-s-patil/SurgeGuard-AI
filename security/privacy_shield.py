import numpy as np
import pandas as pd


def add_laplace_noise(values, epsilon=1.0, sensitivity=1.0):
    """Add Laplace noise to a numeric array or pandas Series."""
    scale = float(sensitivity) / max(epsilon, 1e-9)
    noise = np.random.laplace(loc=0.0, scale=scale, size=np.shape(values))
    return values + noise


class PrivacyWrapper:
    """Wrap vitals data processing with differential privacy."""
    def __init__(self, epsilon=1.0, sensitivity=1.0):
        self.epsilon = float(epsilon)
        self.sensitivity = float(sensitivity)

    def wrap_dataframe(self, df):
        """Return a DP-protected copy of a vitals DataFrame."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame for vitals data")

        noised = df.copy(deep=True)
        numeric_columns = noised.select_dtypes(include=["number"]).columns
        for col in numeric_columns:
            noised[col] = add_laplace_noise(noised[col].values, self.epsilon, self.sensitivity)
        return noised

    def wrap_loader(self, loader, vitals_key="vitals"):
        """Wrap a data loader that yields batches containing vitals arrays or dicts."""
        for batch in loader:
            if isinstance(batch, dict) and vitals_key in batch:
                batch[vitals_key] = add_laplace_noise(batch[vitals_key], self.epsilon, self.sensitivity)
            yield batch
