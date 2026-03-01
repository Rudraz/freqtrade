# Freqtrade Algorithmic Trading — Claude Code Context

## Project Goal
Automated crypto trading using freqtrade on Raspberry Pi 5.
Claude Code manages all code changes, git operations, Pi interactions,
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

```
git push (strategy change)
    ↓
backtest.yml — downloads 60 days KuCoin data, runs backtest
    ↓
validate_backtest.py — checks profit/drawdown/trade thresholds
    ↓ (pass only)
deploy.yml — SSH into Pi, git pull, restart Docker container
    ↓
Telegram notification → Bala's phone
```

### Validation Thresholds (in scripts/validate_backtest.py)
- Minimum monthly profit: **3%**
- Maximum drawdown: **20%**
- Minimum number of trades: **10**
- Minimum Sharpe ratio: **0.5**

---

## Workflow: How Claude Code Should Operate

### When Bala asks for a strategy change:
1. Show Bala what changes will be made (diff) and explain why
2. Ask for confirmation before committing
3. Run: `git add`, `git commit -m "..."`, `git push`
4. Monitor CI: `gh run watch --repo Rudraz/freqtrade`
5. Report pass/fail results to Bala
6. If deploy triggered, confirm Pi restarted successfully

### When Bala asks to check bot status:
1. `ssh freqpi "docker logs freqtrade --tail 30"`
2. Summarise what the bot has been doing
3. Flag any errors or warnings

### When CI fails:
1. `gh run view --repo Rudraz/freqtrade --log`
2. Identify the failure reason
3. Propose a fix and explain it to Bala
4. Only proceed after Bala approves

### Safety Rules (never override these):
- Never push directly to `main` without backtest validation passing
- Never modify `stop_loss` below 3%
- Never switch from dry-run to live without explicit instruction from Bala
- Never delete backtest results
- Always explain what you're doing before doing it

---

## Project File Structure
```
~/freqtrade/
├── CLAUDE.md                          ← This file
├── docker-compose.yml                 ← Pi Docker config
├── user_data/
│   ├── config.json                    ← Main freqtrade config
│   ├── config.deploy.json             ← Deploy-time config
│   ├── strategies/
│   │   ├── MeanReversionMomentum.py   ← ACTIVE strategy
│   │   ├── base_strategy.py
│   │   ├── ema_cross.py
│   │   └── rsi_momentum.py
│   ├── backtest_results/              ← CI backtest outputs
│   └── logs/                          ← Bot logs (on Pi only)
├── scripts/
│   └── validate_backtest.py           ← CI validation script
└── .github/
    └── workflows/
        ├── backtest.yml               ← Runs + validates backtest
        ├── deploy.yml                 ← SSH deploy to Pi
        ├── forwardtest.yml            ← Daily forward test
        └── report.yml                 ← Performance reporting
```

---

## Telegram Notification Format
When sending manual Telegram alerts (for debugging), use:
```bash
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_CHAT_ID}" \
  -d text="🤖 Freqtrade: <your message here>"
```
