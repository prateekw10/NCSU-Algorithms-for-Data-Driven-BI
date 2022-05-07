for i,review in enumerate(test_pos):
    test_pos[i] = list(set(test_pos[i]))
    for word in test_pos[i]:
        if word in pos_dict.keys():
            pos_dict[word] = pos_dict[word] + 1
        else:
            pos_dict[word] = 1
for i,review in enumerate(test_neg):
    test_neg[i] = list(set(test_neg[i]))
    for word in test_neg[i]:
        if word in neg_dict.keys():
            neg_dict[word] = neg_dict[word] + 1
        else:
            neg_dict[word] = 1
print(train_pos[0])
pos_total_words =  sum(pos_dict.values())
neg_total_words =  sum(neg_dict.values())
# Complete above properties
for i,review in enumerate(train_pos):
    j = 0
    while(j < len(train_pos[i])):
        condition1 = train_pos[i][j] in stopwords
        condition2 = pos_dict[train_pos[i][j]] < pos_total_words/100
        condition3 = train_pos[i][j] in pos_dict.keys() and train_pos[i][j] in neg_dict.keys() and pos_dict[train_pos[i][j]] < 2*neg_dict[train_pos[i][j]]
        condition2 = False
        if condition1 or condition2 or condition3:    
            train_pos[i].pop(j)
        else:
            j = j+1
print(train_pos[0])
for i,review in enumerate(train_neg):
    j = 0
    while(j < len(train_neg[i])):
        condition1 = train_neg[i][j] in stopwords
        condition2 = neg_dict[train_neg[i][j]] < neg_total_words/100
        condition3 = train_neg[i][j] in pos_dict.keys() and train_neg[i][j] in neg_dict.keys() and neg_dict[train_neg[i][j]] < 2*pos_dict[train_neg[i][j]]
        condition2 = False
        if condition1 or condition2 or condition3:    
            train_neg[i].pop(j)
        else:
            j = j+1
for i,review in enumerate(test_pos):
    j = 0
    while(j < len(test_pos[i])):
        condition1 = test_pos[i][j] in stopwords
        condition2 = pos_dict[test_pos[i][j]] < pos_total_words/100
        condition3 = test_pos[i][j] in pos_dict.keys() and test_pos[i][j] in neg_dict.keys() and pos_dict[test_pos[i][j]] < 2*neg_dict[test_pos[i][j]]
        condition2 = False
        if condition1 or condition2 or condition3:    
            test_pos[i].pop(j)
        else:
            j = j+1
for i,review in enumerate(test_neg):
    j = 0
    while(j < len(test_neg[i])):
        condition1 = test_neg[i][j] in stopwords
        condition2 = neg_dict[test_neg[i][j]] < neg_total_words/100
        condition3 = test_neg[i][j] in pos_dict.keys() and test_neg[i][j] in neg_dict.keys() and neg_dict[test_neg[i][j]] < 2*pos_dict[test_neg[i][j]]
        condition2 = False
        if condition1 or condition2 or condition3:    
            test_neg[i].pop(j)
        else:
            j = j+1







