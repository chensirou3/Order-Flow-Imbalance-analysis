"""Statistical utility functions."""

import numpy as np
import pandas as pd
from typing import Tuple


def mean_std_t(x: pd.Series) -> Tuple[float, float, float, int]:
    """Compute mean, std, t-statistic, and sample size for a series.
    
    Args:
        x: Pandas Series (NaNs will be ignored)
        
    Returns:
        Tuple of (mean, std, t_stat, N) where:
            - mean: sample mean
            - std: sample standard deviation
            - t_stat: t-statistic for testing if mean != 0
            - N: number of non-NaN observations
            
    Notes:
        - t_stat = mean / (std / sqrt(N))
        - If N <= 1 or std == 0, t_stat will be NaN
    """
    # Remove NaNs
    x_clean = x.dropna()
    
    N = len(x_clean)
    
    if N == 0:
        return np.nan, np.nan, np.nan, 0
    
    mean = x_clean.mean()
    std = x_clean.std()
    
    if N <= 1 or std == 0 or np.isnan(std):
        t_stat = np.nan
    else:
        t_stat = mean / (std / np.sqrt(N))
    
    return mean, std, t_stat, N


def simple_ols(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    """Fit simple linear regression y = alpha + beta * x.
    
    Args:
        x: Independent variable (predictor)
        y: Dependent variable (response)
        
    Returns:
        Tuple of (beta, t_stat_beta) where:
            - beta: slope coefficient
            - t_stat_beta: t-statistic for testing if beta != 0
            
    Notes:
        - Uses numpy for simple OLS calculation
        - Pairs with NaN in either x or y are dropped
        - If insufficient data, returns (NaN, NaN)
    """
    # Create DataFrame and drop NaNs
    df = pd.DataFrame({'x': x, 'y': y}).dropna()
    
    if len(df) < 3:  # Need at least 3 points for meaningful regression
        return np.nan, np.nan
    
    x_vals = df['x'].values
    y_vals = df['y'].values
    
    N = len(x_vals)
    
    # Compute beta using OLS formula
    x_mean = x_vals.mean()
    y_mean = y_vals.mean()
    
    numerator = np.sum((x_vals - x_mean) * (y_vals - y_mean))
    denominator = np.sum((x_vals - x_mean) ** 2)
    
    if denominator == 0:
        return np.nan, np.nan
    
    beta = numerator / denominator
    alpha = y_mean - beta * x_mean
    
    # Compute residuals and standard error
    y_pred = alpha + beta * x_vals
    residuals = y_vals - y_pred
    
    # Residual sum of squares
    rss = np.sum(residuals ** 2)
    
    # Degrees of freedom
    df_resid = N - 2
    
    if df_resid <= 0:
        return beta, np.nan
    
    # Residual standard error
    rse = np.sqrt(rss / df_resid)
    
    # Standard error of beta
    se_beta = rse / np.sqrt(denominator)
    
    if se_beta == 0:
        t_stat_beta = np.nan
    else:
        t_stat_beta = beta / se_beta
    
    return beta, t_stat_beta

