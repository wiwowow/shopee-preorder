import hmac, hashlib, time, requests, os, sys

# ── Konfigurasi ──────────────────────────────────────────────
PARTNER_ID    = 2053216
SHOP_ID       = 20083915
PARTNER_KEY   = os.environ["SHOPEE_PARTNER_KEY"]
REFRESH_TOKEN = os.environ["SHOPEE_REFRESH_TOKEN"]
DAYS_TO_SHIP  = 3

ITEM_IDS = [
    48014448305, 40082361529, 28567054028, 25690498784,
    44001747421, 51914455562, 44032480329, 54868056190,
    26695272948, 42034546250, 53564433594, 45312665196,
    52514877477, 54164456533, 54564255288, 47014470171,
    26845826917, 46668080992, 48763862338,
]
# ─────────────────────────────────────────────────────────────

def make_sign(path, access_token=""):
    ts   = int(time.time())
    base = f"{PARTNER_ID}{path}{ts}{access_token}{SHOP_ID}" if access_token \
           else f"{PARTNER_ID}{path}{ts}"
    sig  = hmac.new(PARTNER_KEY.encode(), base.encode(), hashlib.sha256).hexdigest()
    return ts, sig

def get_access_token():
    path  = "/api/v2/auth/access_token/get"
    ts, sig = make_sign(path)
    resp  = requests.post(
        f"https://partner.shopeemobile.com{path}",
        params={"partner_id": PARTNER_ID, "timestamp": ts, "sign": sig},
        json={"refresh_token": REFRESH_TOKEN, "partner_id": PARTNER_ID, "shop_id": SHOP_ID}
    )
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"Gagal ambil token: {data}")

    # Shopee rotates refresh_token on every use — save the new one
    new_refresh = data.get("refresh_token", "")
    if new_refresh and new_refresh != REFRESH_TOKEN:
        with open("new_refresh_token.txt", "w") as f:
            f.write(new_refresh)
        print(f"🔄 Refresh token baru disimpan (akan diupdate otomatis)")

    return data["access_token"]

def toggle_item(access_token, item_id, is_pre_order):
    path   = "/api/v2/product/update_item"
    ts, sig = make_sign(path, access_token)
    resp   = requests.post(
        f"https://partner.shopeemobile.com{path}",
        params={
            "partner_id":   PARTNER_ID,
            "timestamp":    ts,
            "sign":         sig,
            "shop_id":      SHOP_ID,
            "access_token": access_token
        },
        json={
            "item_id":   item_id,
            "pre_order": {
                "is_pre_order": is_pre_order,
                "days_to_ship": DAYS_TO_SHIP
            }
        }
    )
    return resp.json()

# ── Main ──────────────────────────────────────────────────────
if len(sys.argv) < 2 or sys.argv[1] not in ("on", "off"):
    print("Usage: python toggle_preorder.py on|off")
    sys.exit(1)

mode         = sys.argv[1]
is_pre_order = (mode == "on")

print(f"{'='*50}")
print(f"  Pre-order: {'ON 🟢' if is_pre_order else 'OFF 🔴'}")
print(f"{'='*50}")

access_token = get_access_token()
print(f"✅ Access token diperoleh\n")

ok, fail = 0, 0
for item_id in ITEM_IDS:
    result = toggle_item(access_token, item_id, is_pre_order)
    if result.get("error") in (None, "", 0):
        print(f"  ✓ {item_id}")
        ok += 1
    else:
        print(f"  ✗ {item_id} → {result}")
        fail += 1
    time.sleep(0.3)

print(f"\nSelesai: {ok} berhasil, {fail} gagal")
