# Course Name: Coding Essentials for Agents - Analytics Vidya

In this project, we will develop four robust API endpoints to facilitate seamless data retrieval and analysis, using FastAPI:

1. Company Information Endpoint: This endpoint will retrieve detailed company information, such as the full company name, business summary, industry, sector, and key officers' names and titles, by accepting a valid company symbol as input. The data will be sourced using the Yahoo Finance API.

2. Stock Market Data Endpoint:  This endpoint will fetch real-time stock market data, including market state, current market price, price change, percentage change, and other relevant metrics, for the specified company symbol.

3. Historical Market Data Endpoint:  Designed to handle JSON payloads via POST requests, this endpoint will return historical market data (start date, end date, etc.) for the specified company symbol within a given date range.

4. Analytical Insights Endpoint:  This endpoint will perform a comprehensive analysis of the company based on the provided historical data and deliver actionable insights derived from the analysis.

To run the backend server:
> fastapi dev main.py  -- development environment
> fastapi run main.py -- production environment
