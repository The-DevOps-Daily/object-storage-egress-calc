# object-storage-egress-calc

Price one month of S3-compatible object storage on nine providers, with the fine print applied: free-egress ratios, fair-use policies, bundles, minimum charges and minimum storage durations. No dependencies.

```bash
python3 calc.py --storage-gb 500 --egress-gb 5000 --gets 20000000 --puts 10000
```

```text
500 GB stored, 5,000 GB egress, 20,000,000 GETs, 10,000 PUTs, objects live 365 days (prices as of 2026-09-28)
  Wasabi (pay-as-you-go)           $      7.99  billed for 1024 GB minimum; egress above stored data: outside Wasabi's free egress policy (no overage price; service may be limited)
  Cloudflare R2 Standard           $     10.95
  Hetzner Object Storage (USD)     $     12.69
  ...
  AWS S3 Standard (us-east-1)      $    460.55
```

## Files

- `providers.json`: every price with its source URL, checked on 28 September 2026. Providers: AWS S3 Standard (us-east-1), Cloudflare R2 Standard and Infrequent Access, Backblaze B2, Wasabi, Tigris, DigitalOcean Spaces, Hetzner Object Storage, Storj.
- `calc.py`: the calculator. Options: `--storage-gb`, `--egress-gb`, `--gets`, `--puts`, `--lifetime-days`.
- `scenarios.sh`: the four workloads from the post; output in `runs/scenarios.txt`.
- `tests/`: unit tests for the pricing rules (`python3 -m unittest`).

## What it models, and what it does not

Modelled: storage tiers and free allowances, egress tiers, free egress allowances (fixed, or a multiple of storage), fair-use policies (flagged as a note, since they have no price), bundles with overage rates, request prices and free request allowances, retrieval fees, minimum billable storage, minimum storage duration (approximated as billed days over kept days), minimum monthly charges.

Not modelled: the difference between GB and GiB (up to about 7%), minimum billable object sizes (4 KB to 64 KB depending on provider), rounding rules, aborted-download billing, CDN plans in front of storage (such as the CloudFront flat-rate plans), taxes, and committed-use discounts. Hetzner is priced in its published USD rates.

Prices change. Check `providers.json` against the source URLs before you rely on a result.

## License

MIT
