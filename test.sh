#!/bin/bash

# This doesn't change - set and forget.
walletaddress="0x3daC4bC59F9d8891F75FcA35278a1967C1db1515"
bsc_api_key="BPMEUHVRYKQJCCYR4CUUQ4I2HJTH74DURW"

echo $(curl -s "https://api.dex.guru/v1/tokens/0xb0b924c4a31b7d4581a7f78f57cee1e65736be1d-bsc" -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8" -H "Accept-Language: en-US,en;q=0.5" -H "Cache-Control: max-age=0" -H "Connection:	keep-alive" -H "DNT: 1" -H "Host: api.dex.guru" -H "Upgrade-Insecure-Requests: 1" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0")

while [ 0 = 0 ]
  do

  # grab elongate
  contract="0x2a9718deff471f3bb91fa0eceab14154f150a385"



  # Fetch and calculate values
  elongate_price=$(curl -s "https://api.dex.guru/v1/tokens/0x2a9718deff471f3bb91fa0eceab14154f150a385-bsc" -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8" -H "Accept-Encoding: gzip, deflate, br" -H "Accept-Language: en-US,en;q=0.5" -H "Cache-Control: max-age=0" -H "Connection:	keep-alive" -H "DNT: 1" -H "Host: api.dex.guru" -H "Upgrade-Insecure-Requests: 1" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0" | jq .priceUSD  | awk -F"E" 'BEGIN{OFMT="%10.10f"} {print $1 * (10 ^ $2)}')
  elongate_inventory=$(curl -s "https://api.bscscan.com/api?module=account&action=tokenbalance&contractaddress=${contract}&address=${walletaddress}&tag=latest&apikey=${bsc_api_key}" | jq .result | tr -d '"' | sed 's/.........$/.&/')
  elongate_value=$(echo $elongate_price \* $elongate_inventory |bc)

  echo "ElonGate ========================================"
  echo "Current Price $"$elongate_price
  echo "Token Inventory "$elongate_inventory
  echo "Wallet Value $"$elongate_value

  # grab happy
  contract="0xb0b924c4a31b7d4581a7f78f57cee1e65736be1d"

  # Fetch and calculate values
  happy_price=$(curl -s "https://api.dex.guru/v1/tokens/0xb0b924c4a31b7d4581a7f78f57cee1e65736be1d-bsc" -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8" -H "Accept-Encoding: gzip, deflate, br" -H "Accept-Language: en-US,en;q=0.5" -H "Cache-Control: max-age=0" -H "Connection:	keep-alive" -H "DNT: 1" -H "Host: api.dex.guru" -H "Upgrade-Insecure-Requests: 1" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0" | jq .priceUSD  | awk -F"E" 'BEGIN{OFMT="%10.10f"} {print $1 * (10 ^ $2)}')
  happy_inventory=$(curl -s "https://api.bscscan.com/api?module=account&action=tokenbalance&contractaddress=${contract}&address=${walletaddress}&tag=latest&apikey=${bsc_api_key}" | jq .result | tr -d '"' | sed 's/.........$/.&/')
  happy_value=$(echo $happy_price \* $happy_inventory |bc)

  echo "Happy ============================================"
  echo "Current Price $"$happy_price
  echo "Token Inventory "$happy_inventory
  echo "Wallet Value $"$happy_value

  curl -X POST --data-urlencode "payload={\"channel\": \"#zachelongate\", \"username\": \"Jamiebot\", \"text\": \"ShitCoin Status Update\", \"attachments\": [{ \"text\": \"ElonGate Price:       $elongate_price\\nElonGate Holdings: $elongate_inventory\\nElonGate Value:       $elongate_value USD\"},{ \"text\": \"Happy Price:       $happy_price\\nHappy Holdings: $happy_inventory\\nHappy Value:       $happy_value USD\"}] , \"icon_emoji\": \":ghost:\"}" https://hooks.slack.com/services/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

  sleep 60

done


