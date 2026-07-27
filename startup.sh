#!/bin/bash
cd "$ORYX_APP_PATH"
gunicorn --bind=0.0.0.0:$PORT --timeout 600 app:app
