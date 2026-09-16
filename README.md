# Phone Number Formatter for Ad-Audience Uploads

A Streamlit tool that cleans and formats a raw customer export (email,
phone, currency) into the country-code-prefixed phone format ad platforms
require for Custom Audience uploads — the kind of manual, error-prone
spreadsheet cleanup a growth/marketing team would otherwise do by hand
before every audience upload.

## What it does

Takes two input patterns and normalizes both to the same output shape:

1. **Internal-account numbers**: rows where the email is on an internal
   domain and the "phone" is actually embedded in the email's local part —
   parsed out and matched to a country code from a small lookup table
   (`COUNTRY_INFO`).
2. **Customer numbers**: rows with a real phone + currency column —
   normalized by mapping currency (USD, GBP, MYR, SGD, AED, SAR, AUD, CAD,
   INR, BDT) to its corresponding country calling code and expected number
   length, stripping non-digits, and re-prefixing correctly.

Both paths are merged and de-duplicated into a single `Email, Phone` table,
downloadable as Excel. Includes a synthetic sample-data generator for
testing the pipeline without a real customer file.

## Running it

```bash
pip install streamlit pandas plotly xlsxwriter
streamlit run app.py
```

## Stack

Python, Streamlit, pandas.
