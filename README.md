# Client-1-SeriveM8-Integration

## Automated Execution with Cron

To automatically run `process.proposal.sh` every 5 minutes and have the log file (`process_proposal.log`) overwritten with each new run, follow these steps:

1. **Open your crontab editor:**
   ```bash
   crontab -e
   ```

2. **Add the following line to the end of the crontab file:**
   ```bash
   */5 * * * * cd /home/ubuntu/Client-1-SeriveM8-Integration && ./process.proposal.sh > process_proposal.log 2>&1
   ```
   - Replace `/home/ubuntu/Client-1-SeriveM8-Integration` with the absolute path to your project directory if it's different.
   - This ensures the script runs every 5 minutes, and each time, the previous log will be replaced with the latest output.

