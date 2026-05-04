import pandas as pd
import numpy as np
from pathlib import Path

def apply_differential_privacy(csv_in, csv_out, epsilon=1.0):
    """
    Applies Laplacian noise to vitals to achieve epsilon-Differential Privacy.
    """
    if not Path(csv_in).exists():
        print("Error: Vitals CSV not found.")
        return
        
    df = pd.read_csv(csv_in)
    
    # Sensitivity (Delta f) represents the maximum change expected.
    # We estimate HR sensitivity as 5 bpm, BP as 5 mmHg.
    sens_hr = 5.0
    sens_bp = 5.0
    
    # Scale parameter for Laplace distribution (b = sensitivity / epsilon)
    b_hr = sens_hr / epsilon
    b_bp = sens_bp / epsilon
    
    # Add Laplace noise
    noise_hr = np.random.laplace(0, b_hr, size=len(df))
    noise_sys = np.random.laplace(0, b_bp, size=len(df))
    noise_dia = np.random.laplace(0, b_bp, size=len(df))
    
    df['dp_heart_rate'] = (df['heart_rate'] + noise_hr).round(1)
    df['dp_systolic_bp'] = (df['systolic_bp'] + noise_sys).round(1)
    df['dp_diastolic_bp'] = (df['diastolic_bp'] + noise_dia).round(1)
    
    # Optional: Drop raw data to enforce anonymization
    df = df.drop(columns=['heart_rate', 'systolic_bp', 'diastolic_bp'])
    
    df.to_csv(csv_out, index=False)
    print(f"Differentially private vitals saved to {csv_out}")

if __name__ == "__main__":
    apply_differential_privacy("output/vitals.csv", "output/dp_vitals_anonymized.csv", epsilon=1.5)