resource "google_bigquery_dataset" "finance_data" {
  dataset_id = "finance_data"
  location   = "us-central1"
}

resource "google_bigquery_table" "portfolio" {
  dataset_id = google_bigquery_dataset.finance_data.dataset_id
  table_id   = "portfolio"

  schema = jsonencode([
    { name = "ticker", type = "STRING", mode = "NULLABLE" },
    { name = "name", type = "STRING", mode = "NULLABLE" },
    { name = "sector", type = "STRING", mode = "NULLABLE" },
    { name = "purchase_date", type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "quantity", type = "INTEGER", mode = "NULLABLE" },
    { name = "purchase_price_eur", type = "FLOAT", mode = "NULLABLE" },
    { name = "current_price_eur", type = "FLOAT", mode = "NULLABLE" },
    { name = "invested_value_eur", type = "FLOAT", mode = "NULLABLE" },
    { name = "current_value_eur", type = "FLOAT", mode = "NULLABLE" },
    { name = "unrealized_pnl_eur", type = "FLOAT", mode = "NULLABLE" },
    { name = "unrealized_pnl_pct", type = "FLOAT", mode = "NULLABLE" },
    { name = "currency", type = "STRING", mode = "NULLABLE" },
    { name = "account_type", type = "STRING", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "transactions" {
  dataset_id = google_bigquery_dataset.finance_data.dataset_id
  table_id   = "transactions"

  schema = jsonencode([
    { name = "transaction_id", type = "INTEGER", mode = "NULLABLE" },
    { name = "date", type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "type", type = "STRING", mode = "NULLABLE" },
    { name = "ticker", type = "STRING", mode = "NULLABLE" },
    { name = "name", type = "STRING", mode = "NULLABLE" },
    { name = "quantity", type = "INTEGER", mode = "NULLABLE" },
    { name = "unit_price_eur", type = "FLOAT", mode = "NULLABLE" },
    { name = "fees_eur", type = "FLOAT", mode = "NULLABLE" },
    { name = "total_amount_eur", type = "FLOAT", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "sector_allocation" {
  dataset_id = google_bigquery_dataset.finance_data.dataset_id
  table_id   = "sector_allocation"

  schema = jsonencode([
    { name = "sector", type = "STRING", mode = "NULLABLE" },
    { name = "current_value_eur", type = "FLOAT", mode = "NULLABLE" },
    { name = "weight_pct", type = "FLOAT", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "market_prices" {
  dataset_id = google_bigquery_dataset.finance_data.dataset_id
  table_id   = "market_prices"

  schema = jsonencode([
    { name = "ticker", type = "STRING", mode = "NULLABLE" },
    { name = "price_eur", type = "FLOAT", mode = "NULLABLE" },
    { name = "fetched_at", type = "TIMESTAMP", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "price_history" {
  dataset_id = google_bigquery_dataset.finance_data.dataset_id
  table_id   = "price_history"

  schema = jsonencode([
    { name = "date", type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "close_price_eur", type = "FLOAT", mode = "NULLABLE" },
    { name = "volume", type = "INTEGER", mode = "NULLABLE" },
    { name = "ticker", type = "STRING", mode = "NULLABLE" },
  ])
}

resource "google_bigquery_table" "news_sentiment" {
  dataset_id = google_bigquery_dataset.finance_data.dataset_id
  table_id   = "news_sentiment"

  schema = jsonencode([
    { name = "ticker", type = "STRING", mode = "NULLABLE" },
    { name = "title", type = "STRING", mode = "NULLABLE" },
    { name = "description", type = "STRING", mode = "NULLABLE" },
    { name = "url", type = "STRING", mode = "NULLABLE" },
    { name = "source", type = "STRING", mode = "NULLABLE" },
    { name = "published_at", type = "TIMESTAMP", mode = "NULLABLE" },
    { name = "sentiment_score", type = "FLOAT", mode = "NULLABLE" },
    { name = "match_score", type = "FLOAT", mode = "NULLABLE" },
    { name = "fetched_at", type = "TIMESTAMP", mode = "NULLABLE" },
  ])
}