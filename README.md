Code has reached a working V0.1 state 

The final tradeup_expanded_items.json is of the form:

{
  "Best Tradeup: Revolution Case (9) + Kilowatt Case (1)_Mil-Spec_0.0875_11.38": [
    [
      "P250  Re.built (Minimal Wear)_data.json",
      "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5034545037296709584A38764891451D9233198005804787110",
      "Revolution Case",
      "8.417999200290076",
      "0.11096058040857315",
      "5034545037296709584",
      "38764891451"
    ],
    [
      "MP5-SD  Liquidation (Factory New)_data.json",
      "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5034545037292954964A38763352506D4822979203440116529",
      "Revolution Case",
      "23.701497748357717",
      "0.019285978749394417",
      "5034545037292954964",
      "38763352506"
    ],
    [
      "SG 553  Cyberforce (Minimal Wear)_data.json",
      "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5036796837110579382A38755326505D9233200350354115481",
      "Revolution Case",
      "8.245499216677574",
      "0.1022474393248558",
      "5036796837110579382",
      "38755326505"
    ],
    [
      "MAG-7  Insomnia (Minimal Wear)_data.json",
      "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5030041437671007295A38776801380D6947557010779395703",
      "Revolution Case",
      "7.70499926802507",
      "0.09967947751283646",
      "5030041437671007295",
      "38776801380"
    ],
    [
      "P250  Re.built (Minimal Wear)_data.json",
      "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5041300436740240478A38776919071D7791977660415773004",
      "Revolution Case",
      "8.084499231972574",
      "0.09749531000852585",
      "5041300436740240478",
      "38776919071"
    ],
    [
      "P250  Re.built (Minimal Wear)_data.json",
      "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5034545037298031594A38769733326D7791977660415773004",
      "Revolution Case",
      "8.417999200290076",
      "0.10278624296188354",
      "5034545037298031594",
      "38769733326"
    ],
    [
      "Tec-9  Rebel (Minimal Wear)_data.json",
      "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5034545037301412774A38777282032D12017374758888493374",
      "Revolution Case",
      "7.808499258192571",
      "0.09799350798130035",
      "5034545037301412774",
      "38777282032"
    ],
    [
      "P250  Re.built (Minimal Wear)_data.json",
      "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5041300436740240718A38776822280D7791977660415773004",
      "Revolution Case",
      "8.084499231972574",
      "0.10256356745958328",
      "5041300436740240718",
      "38776822280"
    ],
    [
      "SG 553  Cyberforce (Minimal Wear)_data.json",
      "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5036796837110565222A38760039993D9233200350354115481",
      "Revolution Case",
      "8.245499216677574",
      "0.1012558713555336",
      "5036796837110565222",
      "38760039993"
    ],
    [
      "XM1014  Irezumi (Factory New)_data.json",
      "steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20M5032293237473922242A38473964994D16628457543801092237",
      "Kilowatt Case",
      "25.023997622720227",
      "0.032931722700595856",
      "5032293237473922242",
      "38473964994"
    ]
  ],
}
However the quantity of unique tradeups and the profitablity of each tradeup means that at most it would earn a few hundred rupees a day if deployed
hence, project is being put on ice for the forseeable future.




Importat Note: 
    The final tradeup_expanded_items.json does end up having 28 valid profitable tradeups so project considered a success in theory
    but in reality there are too few tradeups for it to be considered worth doing, hence permanently shelved with no further development.

After dollar is coded and running return to this and make a few changes:
    Modify the tradeups_expanded_items.json into final_tradeups_unchecked.json which will also contain the profitablity and price and links to all the items.
    Create a checker that will check to see if all these items are available for sale in a sinlge tradeups then the tradeup is added to final_tradeups_verified.json and the total profitablity and total expected profit is also printed to user.


