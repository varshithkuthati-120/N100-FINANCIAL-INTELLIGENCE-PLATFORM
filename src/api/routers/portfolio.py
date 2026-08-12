from fastapi import APIRouter
import pandas as pd
import os

router = APIRouter()

@router.get("/portfolio/stats")
def get_portfolio_stats():
    # Read from output/portfolio_stats.csv
    if os.path.exists('output/portfolio_stats.csv'):
        df = pd.read_csv('output/portfolio_stats.csv')
        return df.to_dict(orient='records')
    return []
