import numpy as np
import pandas as pd
import random
import sys

if __name__ == "__main__":

    algo = sys.argv[1]
    print("Solving adwords using ",algo," algorithm")

    bids = pd.read_csv("bidder_dataset.csv")

    text_file = open("queries.txt", "r")
    queries = text_file.read().splitlines()

    budgetInitial = bids.groupby('Advertiser').max()['Budget']

    optimal_matching = sum(budgetInitial)

    n=100
    random.seed(0)
    mean_revenue = 0
    for i in range(n):
        print(i)
        revenue=0
        budgets = bids.groupby('Advertiser').max()['Budget']
        for query in queries:
            relevant_bids = bids[(bids['Keyword'] == query) & (budgets[bids['Advertiser']].reset_index()['Budget']>bids['Bid Value'])].reset_index(drop=True)
            if len(relevant_bids) == 0:
                continue
            if algo == "greedy":
                chosen_bid = relevant_bids.loc[relevant_bids['Bid Value'].idxmax()]
            if algo == "mssv":
                relevant_bids['budget_fraction'] = 1 - (budgets[relevant_bids['Advertiser']] / budgetInitial[relevant_bids['Advertiser']]).reset_index(drop=True)
                relevant_bids['bidder_weight'] = relevant_bids['Bid Value'] *  (1 - np.exp(relevant_bids['budget_fraction']-1))
                chosen_bid = relevant_bids.loc[relevant_bids['bidder_weight'].idxmax()]
            if algo == "balance":
                relevant_bids['unspent_budget'] = budgets[relevant_bids['Advertiser']].reset_index(drop=True)
                chosen_bid = relevant_bids.loc[relevant_bids['unspent_budget'].idxmax()]
            budgets[chosen_bid['Advertiser']] = budgets[chosen_bid['Advertiser']] - chosen_bid['Bid Value']
            revenue = revenue + chosen_bid['Bid Value']
        print(revenue)
        mean_revenue = mean_revenue + revenue
        random.shuffle(queries)
    print("Mean Revenue:",mean_revenue/n)
    print("Competitve Ratio:",mean_revenue/n/optimal_matching)
