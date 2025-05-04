# this code reads from the database and creates a linear regtression forcase of the values for  the next 5 years and saves the output
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime
from sqlalchemy import create_engine
import urllib

# ---------------------------------------------
# DB CONNECTION
# ---------------------------------------------
params = urllib.parse.quote_plus(
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=DESKTOP-AF2UAHM;"
    "Database=test7;"
    "Trusted_Connection=yes;"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# ---------------------------------------------
# PARAMETERS
# ---------------------------------------------
forecast_years = 5  # Number of years to forecast

# ---------------------------------------------
# STEP 1: READ ACTUAL DATA FROM DB
# ---------------------------------------------
query = """
SELECT [PROVIDER_NAME], [Year], [Payor], [Charges], [TotalCharges], [PaymentSourcePercentage]
FROM [PUDF].[dbo].[vw_PaymentSourceBreakdown]
WHERE [Payor] IS NOT NULL AND [PaymentSourcePercentage] IS NOT NULL
"""
df = pd.read_sql(query, engine)

# ---------------------------------------------
# STEP 2: COMPUTE FORECASTS
# ---------------------------------------------
forecast_rows = []

for (hospital, payor), group in df.groupby(['PROVIDER_NAME', 'Payor']):
    # Prepare data for regression
    X = pd.DataFrame({'Year': group['Year']})
    y = group['PaymentSourcePercentage']

    if len(X) < 2:
        continue  # Skip if not enough data for regression

    model = LinearRegression()
    model.fit(X, y)

    last_year = int(group['Year'].max())
    future_years = list(range(last_year + 1, last_year + 1 + forecast_years))
    X_future = pd.DataFrame({'Year': future_years})
    y_pred = model.predict(X_future)

    # Prepare forecast output rows
    for year, value in zip(future_years, y_pred):
        forecast_rows.append({
            'PROVIDER_NAME': hospital,
            'Payor': payor,
            'ForecastYear': year,
            'ForecastValue': round(float(value), 2),
            'ForecastRunDate': datetime.datetime.now().date()
        })

# ---------------------------------------------
# STEP 3: CREATE A DataFrame FOR THE FORECASTS
# ---------------------------------------------
forecast_df = pd.DataFrame(forecast_rows)

# ---------------------------------------------
# STEP 4: EXPORT TO TAB-DELIMITED FILE
# ---------------------------------------------
output_file_path = r'D:\icd-10\forcast\PaymentSourceForecasts_forecasted.txt'

try:
    forecast_df.to_csv(output_file_path, sep='\t', index=False)
    print(f"Forecast data has been successfully exported to {output_file_path}.")
except Exception as e:
    print(f"An error occurred while exporting the forecast data: {e}")
