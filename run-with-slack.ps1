# Run soc-watch with Slack Bot posting to channel (pings you)
# Set SOC_SLACK_BOT_TOKEN and SOC_SLACK_CHANNEL before running
$env:SOC_SLACK_DM_USER_ID = "U0AHDLC6D9P"
$env:SOC_SLACK_CHANNEL = "#all-ucla-soc-test"

if (-not $env:SOC_SLACK_BOT_TOKEN) {
    Write-Host "Set SOC_SLACK_BOT_TOKEN first, e.g.:"
    Write-Host '  $env:SOC_SLACK_BOT_TOKEN = "xoxb-your-token"'
    exit 1
}

$url = "https://sa.ucla.edu/ro/public/soc/Results?t=261&s_g_cd=%25&sBy=classidnumber&id=187101910&undefined=Go&btnIsInIndex=btn_inIndex"
soc-watch --url $url --interval 10 --slack-channel $env:SOC_SLACK_CHANNEL
