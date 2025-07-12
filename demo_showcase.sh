#!/bin/bash

set -e

# === CONFIGURABLE VARIABLES ===
SECRET_KEY="demo-secret"
SECRET_POLICY="demo-policy"
SECRET_LENGTH=32

echo ""
echo "=============================="
echo " Secret Run CLI Demo Showcase "
echo "=============================="
echo ""

# Activate virtual environment
echo "source venv/bin/activate"
source venv/bin/activate
sleep 1

echo ""
echo "---- 1. Show Help ----"
echo "secret-run --help"
secret-run --help
sleep 2

echo ""
echo "---- 2. Show Rotate Command Help ----"
echo "secret-run rotate --help"
secret-run rotate --help
sleep 2

echo ""
echo "---- 3. Show Cloud Command Help ----"
echo "secret-run cloud --help"
secret-run cloud --help
sleep 2

echo ""
echo "---- 4. Create a Rotation Policy ----"
echo "secret-run rotate policy --action create --name $SECRET_POLICY --pattern '$SECRET_KEY' --interval 30 --auto-rotate --method random --min-length 16"
secret-run rotate policy --action create --name "$SECRET_POLICY" --pattern "$SECRET_KEY" --interval 30 --auto-rotate --method random --min-length 16
sleep 2

echo "---- 5. Ensure Metadata for $SECRET_KEY Exists ----"
python3 -c "import json, datetime, hashlib; from pathlib import Path; f=Path.home()/'.config'/'secret-run'/'secret-metadata.json'; m=json.load(open(f)); k='$SECRET_KEY'; now=datetime.datetime.now().isoformat(); h=hashlib.sha256(k.encode()).hexdigest();
if k not in m:
    m[k] = {'key': k, 'created_at': now, 'last_rotated': None, 'expires_at': None, 'rotation_count': 0, 'hash': h, 'policy': '$SECRET_POLICY', 'tags': [], 'usage_count': 0, 'last_used': None};
    json.dump(m, open(f, 'w'), indent=2)
    print(f'Metadata for {k} created.')
else:
    print(f'Metadata for {k} already exists.')"
sleep 1

echo "---- 6. Generate a New Secret ----"
echo "secret-run rotate generate --key $SECRET_KEY --method random --length $SECRET_LENGTH --policy $SECRET_POLICY"
secret-run rotate generate --key "$SECRET_KEY" --method random --length "$SECRET_LENGTH" --policy "$SECRET_POLICY"
sleep 2

echo ""
echo "---- 7. List Rotation Policies ----"
echo "secret-run rotate policy --action list"
secret-run rotate policy --action list
sleep 2

echo ""
echo "---- 8. Show Secret Rotation Status ----"
echo "secret-run rotate status"
secret-run rotate status
sleep 2

echo ""
echo "---- 9. Rotate a Secret ----"
echo "secret-run rotate rotate --key demo-secret --method random --force"
secret-run rotate rotate --key demo-secret --method random --force
sleep 2

echo ""
echo "---- 10. Auto-Rotate (Dry Run) ----"
echo "secret-run rotate auto-rotate --dry-run"
secret-run rotate auto-rotate --dry-run
sleep 2

echo ""
echo "---- 11. Show Cloud Integrations ----"
echo "secret-run cloud list"
secret-run cloud list
sleep 2

echo ""
echo "---- 12. Try to Get a Secret from Cloud (should show not found) ----"
echo "secret-run cloud get --secret demo-cloud-secret"
secret-run cloud get --secret demo-cloud-secret
sleep 2

echo ""
echo "---- 13. Show Version ----"
echo "secret-run version"
secret-run version
sleep 2

echo ""
echo "=============================="
echo "   End of Secret Run Demo!    "
echo "=============================="
echo "" 