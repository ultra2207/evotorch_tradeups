A program to find profitable cs2 tradeups using genetic algorithm based on evotorch. Enables u to skip the terrible buy order strat and directly
find listed profitable combos using evolutionery algorithm. Refer to control flow doc and documentation. Currently not very profitable due to
existing bots and market saturation. It shows an application of meta heuristic optimization algorithms in unique real world scenarios.

Code has reached a working V0.1 state however the quantity of unique tradeups and the profitablity of each tradeup and 7 day hold along with difficulty of obtaining items for the profitable combos (hard to snipe good quantity steam market and abysmal rates for buy orders) means that
it is just not very profitable in raw terms. Could be run with lower generations and can be made faster.

Documentation beyond control flow is not extensive as project has been shelved and is not in full deployment due to low profit. Can be built upon further with aiosteampy to automatically buy the found tradeups and node-steam-user to automatically do the tradeups. The 7 day trade hold makes it pointless as u will have to wait 7 days to list the outputs anyway and therefore further automations is unnecessary and u can use it as is if you are okay with less profit.
