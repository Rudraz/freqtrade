# Freqtrade Algorithmic Trading — Claude Code Context

## Project Goal
Automated crypto trading using freqtrade on Raspberry Pi 5.
Claude Code manages all code changes, git operations, Pi interactions, hyperoptimization,
and CI/CD monitoring with minimal manual intervention from Bala.

---

## Infrastructure

### Raspberry Pi 5
- **SSH alias:** `freqpi` (configured in ~/.ssh/config)
- **User:** `bala`
- **IP:** `192.168.68.86`
- **Freqtrade path:** `/home/bala/freqtrade/`
- **Docker container:** `freqtrade`
- **Config file:** `/home/bala/freqtrade/user_data/config.json`
- **Logs:** `/home/bala/freqtrade/user_data/logs/freqtrade.log`
- **Timezone:** `Asia/Singapore` (SGT = UTC+8)

### Common Pi Commands (run via SSH)
```bash
# Check bot status
ssh freqpi "docker ps"

# View recent logs
ssh freqpi "docker logs freqtrade --tail 50"

# Restart bot after strategy update
ssh freqpi "cd /home/bala/freqtrade && docker compose down && docker compose up -d"

# Check if bot is trading
ssh freqpi "docker logs freqtrade --tail 20 | grep -E 'TRADE|BUY|SELL|profit'"

# Check disk space on Pi
ssh freqpi "df -h"

# Check Pi CPU/memory
ssh freqpi "top -bn1 | head -5"

# Run hyperopt on Pi (CPU-bound — Pi 5 handles it with 4 cores)
ssh freqpi "cd /home/bala/freqtrade && docker compose run --rm freqtrade hyperopt \
  --config user_data/config.json \
  --hyperopt-loss SharpeHyperOptLoss \
  --strategy MeanReversionMomentum \
  --timeframe 5m \
  --epochs 200 \
  --spaces buy sell roi stoploss \
  -j 4"
```

---

## GitHub Repository
- **Repo:** `Rudraz/freqtrade`
- **Main branch:** `main`
- **Remote:** `https://github.com/Rudraz/freqtrade.git`

### GitHub Secrets (already configured)
| Secret | Purpose |
|--------|---------|
| `PI_SSH_PRIVATE_KEY` | SSH key for GitHub Actions → Pi deploy |
| `PI_HOST` | Pi IP address (192.168.68.86) |
| `PI_USER` | Pi username (bala) |
| `TELEGRAM_TOKEN` | Telegram bot token for notifications |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for notifications |
| `FT_CONFIG_JSON_BASE64` | Base64-encoded freqtrade config |
| `EXCHANGE_NAME` | Exchange name (kucoin) |
| `API_USERNAME` | KuCoin API username |
| `API_PASSWORD` | KuCoin API password |
| `JWT_SECRET` | FreqUI JWT secret |
| `WS_TOKEN` | WebSocket token |

### GitHub CLI Commands
```bash
# List recent CI runs
gh run list --repo Rudraz/freqtrade --limit 10

# Watch a run in real time
gh run watch --repo Rudraz/freqtrade

# View logs of last run
gh run view --repo Rudraz/freqtrade --log

# Trigger backtest manually
gh workflow run backtest.yml --repo Rudraz/freqtrade

# Trigger hyperopt manually (CI runner, 100 epochs)
gh workflow run hyperopt.yml --repo Rudraz/freqtrade

# Trigger deploy manually
gh workflow run deploy.yml --repo Rudraz/freqtrade

# Check all secrets
gh secret list --repo Rudraz/freqtrade
```

---

## Trading Configuration
- **Exchange:** KuCoin
- **Active Strategy:** `MeanReversionMomentum`
- **Timeframe:** `5m`
- **Mode:** Dry-run (until live trading approved by Bala)
- **Strategy file:** `user_data/strategies/MeanReversionMomentum.py`
- **Other strategies:** `ema_cross.py`, `rsi_momentum.py`, `base_strategy.py`

---

## CI/CD Pipeline Overview

### Full Automation Flow
```
git push (strategy or config change)
    ↓
backtest.yml
  ├─ Download 60 days KuCoin 5m data
  ├─ Run freqtrade backtesting
  ├─ validate_backtest.py — enforces profit/drawdown/trade/Sharpe thresholds
  └─ (pass only) → triggers deploy.yml
         ↓
    deploy.yml
      ├─ SSH into Pi
      ├─ git pull + config decode
      ├─ docker compose down && up -d
      └─ Telegram: "🚀 Deploy SUCCESS"

Weekly (Sunday 02:00 UTC):
hyperopt.yml
  ├─ Download 90 days data
  ├─ Run 100-epoch hyperopt (SharpeHyperOptLoss)
  ├─ Extract best params → hyperopt_results.json
  ├─ validate_hyperopt.py — checks improvement vs current params
  └─ (if improved) → open PR with updated strategy params

Daily (01:00 UTC):
forwardtest.yml
  └─ Backtest last 2 days to catch drift

Manual:
report.yml
  └─ Full HTML performance report with backtest + forward test
```

### Workflow Files
| File | Trigger | Purpose |
|------|---------|---------|
| `backtest.yml` | push to strategy/config | Backtest + validate + deploy |
| `deploy.yml` | called by backtest or manual | SSH deploy to Pi |
| `hyperopt.yml` | weekly schedule + manual | Hyperoptimize and open PR |
| `forwardtest.yml` | daily cron + manual | Detect forward drift |
| `report.yml` | manual | Generate HTML performance report |

### Validation Thresholds (in `scripts/validate_backtest.py`)
| Metric | Threshold | Reason |
|--------|-----------|--------|
| Monthly profit | ≥ 3% | Minimum viable return |
| Max drawdown | ≤ 20% | Capital protection |
| Total trades | ≥ 10 | Statistical significance |
| Win rate | ≥ 40% | Not random noise |
| Sharpe ratio | ≥ 0.5 | Risk-adjusted quality |

---

## Hyperoptimization

### What It Optimizes
Freqtrade hyperopt uses Bayesian search to find the best values for:
- **`buy` space** — RSI thresholds, EMA periods, ATR multipliers
- **`sell` space** — RSI exit levels, EMA crossover margins
- **`roi` space** — Profit-taking table (time → min profit %)
- **`stoploss` space** — Dynamic stop-loss percentage (capped at -3% by safety rule)
- **`trailing` space** — Trailing stop activation and offset

### Loss Functions (choose based on goal)
| Loss Function | Use When |
|--------------|----------|
| `SharpeHyperOptLoss` | Maximise risk-adjusted return (default choice) |
| `SortinoHyperOptLoss` | Penalise downside volatility more |
| `MaxDrawDownHyperOptLoss` | Minimise drawdown above all else |
| `ProfitDrawDownHyperOptLoss` | Balance profit vs drawdown |
| `OnlyProfitHyperOptLoss` | Raw profit only (can overfit) |

### Running Hyperopt Locally (Docker)
```bash
# Full hyperopt — 200 epochs, all spaces
docker run --rm \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  freqtradeorg/freqtrade:stable \
  hyperopt \
    --config user_data/config.json \
    --strategy MeanReversionMomentum \
    --hyperopt-loss SharpeHyperOptLoss \
    --timeframe 5m \
    --epochs 200 \
    --spaces buy sell roi stoploss \
    -j -1

# Quick test — 50 epochs, buy/sell only
docker run --rm \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  freqtradeorg/freqtrade:stable \
  hyperopt \
    --config user_data/config.json \
    --strategy MeanReversionMomentum \
    --hyperopt-loss SharpeHyperOptLoss \
    --timeframe 5m \
    --epochs 50 \
    --spaces buy sell

# Show top 10 results from last hyperopt run
docker run --rm \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  freqtradeorg/freqtrade:stable \
  hyperopt-show --best --print-json

# Show all results sorted by Sharpe
docker run --rm \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  freqtradeorg/freqtrade:stable \
  hyperopt-list --best --print-json --no-header
```

### Applying Hyperopt Results to Strategy
After hyperopt, best params are printed to console. Apply them:

**Option A — Inline in strategy** (preferred for CI tracking):
```python
# In MeanReversionMomentum.py
class MeanReversionMomentum(IStrategy):
    # Hyperopt-optimised (2026-05-09, 200 epochs, SharpeHyperOptLoss)
    buy_rsi_lower = 32          # hyperopt range: IntParameter(20, 45, default=30)
    sell_rsi_upper = 55         # hyperopt range: IntParameter(50, 75, default=60)
    minimal_roi = {"0": 0.02, "30": 0.01, "60": 0.005}
    stoploss = -0.03
```

**Option B — Auto-load via `--hyperopt-filename`** (for CI):
```bash
# freqtrade auto-applies best params if this file exists
user_data/hyperopt_results/MeanReversionMomentum.json
```

### Adding Hyperopt Spaces to Strategy
To make a strategy hyperoptable, add `IntParameter` / `DecimalParameter` class variables:
```python
from freqtrade.strategy import IntParameter, DecimalParameter

class MeanReversionMomentum(IStrategy):
    # Hyperopt search spaces
    buy_rsi = IntParameter(20, 45, default=32, space='buy', optimize=True)
    sell_rsi = IntParameter(50, 75, default=55, space='sell', optimize=True)
    rsi_period = IntParameter(10, 20, default=14, space='buy', optimize=True)
    ema_fast_period = IntParameter(8, 20, default=12, space='buy', optimize=True)
    ema_slow_period = IntParameter(20, 35, default=26, space='buy', optimize=True)

    def populate_indicators(self, df, metadata):
        df['rsi'] = ta.RSI(df, timeperiod=self.rsi_period.value)
        df['ema_fast'] = ta.EMA(df, timeperiod=self.ema_fast_period.value)
        # etc.
```

---

## Strategy Development Cycle

```
1. Hypothesis → Edit MeanReversionMomentum.py
2. Local backtest (Docker) → validate thresholds pass
3. git push → CI backtest.yml runs automatically
4. CI passes → auto-deploy to Pi
5. Pi runs dry-run → forwardtest.yml monitors daily
6. Weekly hyperopt.yml → extract best params → open PR
7. Review PR → merge → re-deploy with optimised params
8. Repeat
```

### Backtesting Locally
```bash
# Download data first (60 days)
docker run --rm \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  freqtradeorg/freqtrade:stable \
  download-data --exchange kucoin --timeframe 5m --days 60

# Run backtest
docker run --rm \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  freqtradeorg/freqtrade:stable \
  backtesting \
    --config user_data/config.json \
    --strategy MeanReversionMomentum \
    --timeframe 5m \
    --export trades \
    --export-filename user_data/backtest_results/MeanReversionMomentum.json

# Validate results locally
python scripts/validate_backtest.py user_data/backtest_results/MeanReversionMomentum.json
```

---

## Workflow: How Claude Code Should Operate

### When Bala asks for a strategy change:
1. Show Bala what changes will be made (diff) and explain why
2. Ask for confirmation before committing
3. Run: `git add`, `git commit -m "..."`, `git push`
4. Monitor CI: `gh run watch --repo Rudraz/freqtrade`
5. Report pass/fail results to Bala
6. If deploy triggered, confirm Pi restarted: `ssh freqpi "docker ps"`

### When Bala asks to run hyperopt:
1. Confirm scope (epochs, loss function, spaces) with Bala
2. Trigger `gh workflow run hyperopt.yml --repo Rudraz/freqtrade`
3. Monitor run — hyperopt takes 20-40 min on CI
4. Report best params found
5. Show Bala a diff of what would change in the strategy
6. Ask for confirmation before creating a PR or committing

### When Bala asks to check bot status:
1. `ssh freqpi "docker logs freqtrade --tail 30"`
2. Summarise what the bot has been doing
3. Flag any errors or warnings
4. Check open trades: `ssh freqpi "docker logs freqtrade --tail 50 | grep -E 'open|TRADE|profit'"`

### When CI fails:
1. `gh run view --repo Rudraz/freqtrade --log`
2. Identify the failure reason (backtest thresholds? docker pull? SSH?)
3. Propose a fix and explain it to Bala
4. Only proceed after Bala approves

### Safety Rules (never override these):
- Never push directly to `main` without backtest validation passing
- Never modify `stop_loss` below -3% (safety floor)
- Never switch from dry-run to live without explicit instruction from Bala
- Never delete backtest results
- Never auto-merge a hyperopt PR — always show Bala the diff first
- Always explain what you're doing before doing it

---

## Project File Structure
```
~/freqtrade/                               ← git root
├── CLAUDE.md                              ← This file
├── docker-compose.yml                     ← Pi Docker config
├── .github/
│   └── workflows/
│       ├── backtest.yml                   ← Backtest + validate + trigger deploy
│       ├── deploy.yml                     ← SSH deploy to Pi
│       ├── hyperopt.yml                   ← Weekly hyperopt → PR
│       ├── forwardtest.yml                ← Daily forward drift check
│       └── report.yml                     ← HTML performance report
├── user_data/
│   ├── config.json                        ← Main freqtrade config (from secret)
│   ├── config.deploy.json                 ← Deploy-time config template
│   ├── strategies/
│   │   ├── MeanReversionMomentum.py       ← ACTIVE strategy
│   │   ├── base_strategy.py
│   │   ├── ema_cross.py
│   │   └── rsi_momentum.py
│   ├── hyperopts/
│   │   └── sample_hyperopt_loss.py        ← Custom loss function template
│   ├── hyperopt_results/                  ← Saved hyperopt runs (JSON)
│   └── backtest_results/                  ← CI/local backtest outputs
└── scripts/
    └── validate_backtest.py               ← CI validation script
```

---

## Troubleshooting

### Bot not trading
```bash
ssh freqpi "docker logs freqtrade --tail 100 | grep -iE 'error|warning|no.*pair|stake'"
# Common causes: insufficient balance, all pairs filtered out, API rate limit
```

### CI backtest failing validation
```bash
gh run view --repo Rudraz/freqtrade --log | grep -A5 "THRESHOLD CHECKS"
# Then review validate_backtest.py thresholds — adjust MIN_MONTHLY_PROFIT_PCT if market regime changed
```

### SSH deploy fails
```bash
# Test SSH from local machine
ssh -i ~/.ssh/deploy_key bala@192.168.68.86 "echo ok"
# If fail: check PI_SSH_PRIVATE_KEY secret, Pi SSH service, firewall
```

### Hyperopt produces no improvement
- Increase `--epochs` (200+ for meaningful search)
- Widen the search spaces in the strategy's `IntParameter`/`DecimalParameter` ranges
- Try a different loss function (`SortinoHyperOptLoss` for volatile markets)
- Check if data quality is good: `docker logs freqtrade | grep "insufficient data"`

### Docker container keeps restarting on Pi
```bash
ssh freqpi "docker logs freqtrade --tail 30"
ssh freqpi "docker inspect freqtrade | grep -A3 RestartPolicy"
# Usually: config.json missing, bad API credentials, or exchange connectivity
```

---

## Telegram Notification Format
```bash
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_CHAT_ID}" \
  -d text="🤖 Freqtrade: <your message here>"
```
