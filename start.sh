#!/bin/bash
source venv\Scripts\activate
exec gunicorn -b 0.0.0.0:10000 app:app
