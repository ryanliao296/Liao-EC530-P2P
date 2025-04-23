#!/bin/bash
if [ -z "$USER_ID" ] || [ -z "$PORT" ]; then
  echo "USER_ID and PORT environment variables are required."
  exit 1
fi

python P2P.py --user_id "$USER_ID" --port "$PORT"
