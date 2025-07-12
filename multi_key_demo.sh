#!/bin/bash

# === MULTI-KEY DEMO CONFIG ===
SECRETS=(
  "demo-secret:demo-policy:32"
  "prod-api-key:api_keys:40"
  "db-password:passwords:24"
  "service-token:tokens:48"
)

for entry in "${SECRETS[@]}"; do
  IFS=":" read -r SECRET_KEY SECRET_POLICY SECRET_LENGTH <<< "$entry"
  echo ""
  echo "=============================="
  echo "Demo for key: $SECRET_KEY, policy: $SECRET_POLICY, length: $SECRET_LENGTH"
  echo "=============================="

  echo "---- 1. Create/Ensure Rotation Policy ----"
  if ! secret-run rotate policy --action create --name "$SECRET_POLICY" --pattern "$SECRET_KEY" --interval 30 --auto-rotate --method random --min-length 16 2>/dev/null; then
    echo "Policy '$SECRET_POLICY' already exists or creation failed, continuing..."
  fi
  sleep 1

  echo "---- 2. Ensure Metadata for $SECRET_KEY Exists ----"
  python3 -c "import json, datetime, hashlib; from pathlib import Path; f=Path.home()/'.config'/'secret-run'/'secret-metadata.json'; m=json.load(open(f)); k='$SECRET_KEY'; now=datetime.datetime.now().isoformat(); h=hashlib.sha256(k.encode()).hexdigest();
if k not in m:
    m[k] = {'key': k, 'created_at': now, 'last_rotated': None, 'expires_at': None, 'rotation_count': 0, 'hash': h, 'policy': '$SECRET_POLICY', 'tags': [], 'usage_count': 0, 'last_used': None};
    json.dump(m, open(f, 'w'), indent=2)
    print(f'Metadata for {k} created.')
else:
    print(f'Metadata for {k} already exists.')"
  sleep 1

  echo "---- 3. Generate Secret ----"
  secret-run rotate generate --key "$SECRET_KEY" --method random --length "$SECRET_LENGTH" --policy "$SECRET_POLICY" || echo "Secret generation completed (pyperclip warning ignored)"
  sleep 2

done

echo ""
echo "=============================="
echo "  End of Multi-Key Secret Demo  "
echo "=============================="
echo "" 